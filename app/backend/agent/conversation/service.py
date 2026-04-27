import logging
import threading
from typing import Annotated, Generator, cast

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from conversation.models import ConversationMetadata, Message

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are an information extraction assistant.
Analyze the user message and extract important personal info, preferences, or key facts/decisions.

Extract:
- Personal info: name, occupation, location, etc.
- Preferences: language, communication style, interests
- Key facts/decisions: project decisions, constraints, goals

Rules:
- Only extract clearly stated information (no inference)
- Keys: concise English snake_case (e.g. "user_name", "preferred_language")
- If nothing important, return empty items"""


class MetadataItem(BaseModel):
    key: str
    value: str


class ExtractedMetadata(BaseModel):
    items: list[MetadataItem] = Field(default_factory=list)


def extract_metadata(conversation_id: int, user_message: str) -> None:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    try:
        extractor = llm.with_structured_output(ExtractedMetadata)
        result = cast(
            ExtractedMetadata,
            extractor.invoke(
                [
                    SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
                    HumanMessage(content=user_message),
                ]
            ),
        )
        for item in result.items:
            ConversationMetadata.objects.update_or_create(
                conversation_id=conversation_id,
                key=item.key,
                defaults={"value": item.value, "is_deleted": False},
            )
    except Exception:
        logger.error("metadata extraction failed", exc_info=True)


class ConversationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    metadata_context: str


class ConversationGraph:
    def __init__(self, model: str, temperature: float, system_prompt: str):
        self._llm = ChatOpenAI(model=model, temperature=temperature, streaming=True)
        self._system_prompt = system_prompt
        self._graph = self._build()

    def _metadata_node(self, state: ConversationState, config: RunnableConfig) -> dict:
        conversation_id = config["configurable"]["conversation_id"]
        items = list(
            ConversationMetadata.objects.filter(
                conversation_id=conversation_id,
                is_deleted=False,
            )
            .order_by("created_at")
            .values_list("key", "value")
        )
        if not items:
            return {"metadata_context": ""}
        lines = "\n".join(f"- {k}: {v}" for k, v in items)
        return {"metadata_context": f"\n\nContext:\n{lines}"}

    def _chatbot_node(self, state: ConversationState) -> dict:
        full_prompt = self._system_prompt + state["metadata_context"]
        messages = [SystemMessage(content=full_prompt)] + state["messages"]
        response = self._llm.invoke(messages)
        return {"messages": [response]}

    def _build(self):
        graph = StateGraph(ConversationState)
        graph.add_node("metadata", self._metadata_node)
        graph.add_node("chatbot", self._chatbot_node)
        graph.add_edge("metadata", "chatbot")
        graph.set_entry_point("metadata")
        graph.set_finish_point("chatbot")
        return graph.compile()

    def stream(
        self, history: list[Message], user_message: str, conversation_id: int
    ) -> Generator[str, None, None]:
        input_messages = [
            HumanMessage(content=m.content)
            if m.role == "user"
            else AIMessage(content=m.content)
            for m in history
        ] + [HumanMessage(content=user_message)]

        for chunk, _ in self._graph.stream(
            {"messages": input_messages, "metadata_context": ""},
            config={"configurable": {"conversation_id": conversation_id}},
            stream_mode="messages",
        ):
            if chunk.content:
                yield chunk.content

        # best-effort: runs only when generator fully exhausted; skipped on early close (e.g. client disconnect mid-stream)
        t = threading.Thread(
            target=extract_metadata,
            args=(conversation_id, user_message),
            daemon=True,
        )
        t.start()

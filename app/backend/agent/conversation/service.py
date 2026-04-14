from typing import Annotated, Generator

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from conversation.models import ConversationMetadata, Message


class ConversationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    metadata_context: str


class ConversationGraph:
    def __init__(self, model: str, temperature: float, system_prompt: str, conversation_id: int):
        self._llm = ChatOpenAI(model=model, temperature=temperature, streaming=True)
        self._system_prompt = system_prompt
        self._conversation_id = conversation_id
        self._graph = self._build()

    def _metadata_node(self, state: ConversationState) -> dict:
        # state not used; metadata is fetched directly from DB by conversation_id
        items = list(
            ConversationMetadata.objects.filter(
                conversation_id=self._conversation_id,
                is_deleted=False,
            ).order_by('created_at').values_list('key', 'value')
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

    def stream(self, history: list[Message], user_message: str) -> Generator[str, None, None]:
        input_messages = [
            HumanMessage(content=m.content) if m.role == "user" else AIMessage(content=m.content)
            for m in history
        ] + [HumanMessage(content=user_message)]

        for chunk, _ in self._graph.stream(
            {"messages": input_messages, "metadata_context": ""},
            stream_mode="messages",
        ):
            if chunk.content:
                yield chunk.content

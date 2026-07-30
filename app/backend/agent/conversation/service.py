import logging
import os
from typing import Annotated, Generator

from asgiref.sync import async_to_sync
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from conversation.models import ConversationMetadata, Message

logger = logging.getLogger(__name__)

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8001/mcp")

_mcp_tools: list[BaseTool] | None = None


def _to_sync(tool: BaseTool) -> BaseTool:
    # MCP adapter 툴은 coroutine 만 있어서 sync 그래프(graph.stream)에서 실행이 깨진다.
    # get_tools() 는 툴 호출마다 새 세션을 만들므로 호출마다 새 이벤트 루프를 써도 안전하다.
    # AsyncToSync 객체를 func 으로 바로 쓰면 langchain 의 signature 검사가 깨져서
    # 평범한 함수로 한 번 감싼다.
    # ponytail: 호출마다 루프+세션 생성. MCP 서버가 원격으로 빠지면 영속 루프 스레드
    # + load_mcp_tools(session=...) 로 세션 재사용하도록 업그레이드.
    run_coro = async_to_sync(tool.coroutine)

    def _sync(**kwargs):
        return run_coro(**kwargs)

    return tool.model_copy(update={"func": _sync})


def get_mcp_tools() -> list[BaseTool]:
    global _mcp_tools
    if _mcp_tools is None:
        try:
            client = MultiServerMCPClient(
                {
                    "agent-memory": {
                        "url": MCP_SERVER_URL,
                        "transport": "streamable_http",
                    }
                }
            )
            _mcp_tools = [_to_sync(t) for t in async_to_sync(client.get_tools)()]
        except Exception:
            logger.warning("failed to load MCP tools, chat runs without tools")
            return []
    return _mcp_tools


class ConversationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    metadata_context: str


TOOL_SYSTEM_PROMPT = """

The current conversation_id is {conversation_id}. You have tools to manage \
this conversation's persistent memory (save_memory, list_memory, delete_memory); \
always pass this conversation_id to tool calls. When the user shares important \
personal info, preferences, or key facts/decisions, save them with save_memory."""


class ConversationGraph:
    def __init__(
        self,
        model: str,
        temperature: float,
        system_prompt: str,
        tools: list[BaseTool] | None = None,
    ):
        llm = ChatOpenAI(model=model, temperature=temperature, streaming=True)
        self._tools = tools or []
        self._llm = llm.bind_tools(self._tools) if self._tools else llm
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

    def _chatbot_node(self, state: ConversationState, config: RunnableConfig) -> dict:
        full_prompt = self._system_prompt + state["metadata_context"]
        if self._tools:
            conversation_id = config["configurable"]["conversation_id"]
            full_prompt += TOOL_SYSTEM_PROMPT.format(conversation_id=conversation_id)
        messages = [SystemMessage(content=full_prompt)] + state["messages"]
        response = self._llm.invoke(messages)
        return {"messages": [response]}

    def _build(self):
        graph = StateGraph(ConversationState)
        graph.add_node("metadata", self._metadata_node)
        graph.add_node("chatbot", self._chatbot_node)
        graph.add_edge("metadata", "chatbot")
        graph.set_entry_point("metadata")
        if self._tools:
            graph.add_node("tools", ToolNode(self._tools))
            graph.add_conditional_edges("chatbot", tools_condition)
            graph.add_edge("tools", "chatbot")
        else:
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
            # ToolMessage 등 비-AI 메시지가 사용자 화면으로 새지 않도록 거른다
            if isinstance(chunk, AIMessage) and chunk.content:
                yield chunk.content

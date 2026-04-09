from typing import Generator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph

from conversation.models import Message


class ConversationGraph:
    def __init__(self, model: str, temperature: float, system_prompt: str):
        self._llm = ChatOpenAI(model=model, temperature=temperature, streaming=True)
        self._system_prompt = system_prompt
        self._graph = self._build()

    def _chatbot_node(self, state: MessagesState):
        messages = [SystemMessage(content=self._system_prompt)] + state["messages"]
        response = self._llm.invoke(messages)
        return {"messages": [response]}

    def _build(self):
        graph = StateGraph(MessagesState)
        graph.add_node("chatbot", self._chatbot_node)
        graph.set_entry_point("chatbot")
        graph.set_finish_point("chatbot")
        return graph.compile()

    def stream(self, history: list[Message], user_message: str) -> Generator[str, None, None]:
        input_messages = [
            HumanMessage(content=m.content) if m.role == "user" else AIMessage(content=m.content)
            for m in history
        ] + [HumanMessage(content=user_message)]

        for chunk, _ in self._graph.stream({"messages": input_messages}, stream_mode="messages"):
            if chunk.content:
                yield chunk.content

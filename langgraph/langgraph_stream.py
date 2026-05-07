from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph

load_dotenv()

LLM_MODEL = "gpt-5"


def build_graph():
    model = ChatOpenAI(model=LLM_MODEL)

    def chatbot(state: MessagesState):
        response = model.invoke(state["messages"])
        return {"messages": [response]}

    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)

    return graph_builder.compile()


if __name__ == "__main__":
    query = "AI Agent 에 대해서 간단하게 설명해줘."

    graph = build_graph()

    for message_chunk, metadata in graph.stream(
        MessagesState(messages=[HumanMessage(content=query)]),
        stream_mode="messages",
    ):
        if message_chunk.content:
            print(message_chunk.content, end="", flush=True)
    print()

from langgraph.graph import StateGraph, START, END
from typing import TypedDict


# 카운터를 저장하는 상자
class CounterState(TypedDict):
    count: int


# 첫 번째 증가 함수
def first_increment(state):
    print("첫 번째 증가")
    return {"count": state["count"] + 1}


# 두 번째 증가 함수  
def second_increment(state):
    print("두 번째 증가")
    return {"count": state["count"] + 10}


# 그래프 구성
graph = StateGraph(CounterState)
graph.add_node("first", first_increment)
graph.add_node("second", second_increment)


# 연결: START → first → second → END
graph.add_edge(START, "first")
graph.add_edge("first", "second") 
graph.add_edge("second", END)


# 실행
app = graph.compile()
result = app.invoke({"count": 0})
print(f"최종 결과: {result}")

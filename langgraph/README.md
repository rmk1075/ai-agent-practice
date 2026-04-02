# LangGraph

## LangGraph 예제

### 환경설정

LangGraph 패키지 설치

```bash
pip install -U langgraph
```

LangGraph 와 함께 사용할 패키지들 설치

```bash
pip install langchain langchain-openai
```

LLM 호출을 위한 환경변수 관련 패키지 설치와 환경변수 설정

.env 환경변수 호출을 위한 `python-dotenv` 패키지 설치

```bash
pip install python-dotenv
```

OpenAI API 를 사용하기 위해 Key 정보를 환경변수로 지정

```text
# .env
OPENAI_API_KEY=your-api-key-here
```

### StateGraph

#### State

상태를 저장하는 데이터 저장소로 모든 노드가 공유한다.
python 의 TypedDict 를 사용해서 정의되며 모든 종류의 데이터를 저장할 수 있다.

```python
class SimpleState(TypedDict):
    name: str
    count: int
```

#### Node

실제 작업을 수행하는 Python 함수로 현재 상태를 입력받고 새로운 상태를 반환한다.
항상 `state` 를 첫 번째 매개변수로 입력받고 dict 형태의 새로운 상태를 반환한다.
Node 가 반환한 dict 에 포함되지 않은 필드는 기존 값을 유지한다.

```python
def add_one(state):
    return {"count": state["count"] + 1}

def set_name(state):
    return {"name": "jamie"}
```

#### Edge

Node 들 사이의 연결을 정의하여 작업의 순서를 알려준다.
START, END 상수를 통해 시작과 끝을 표현할 수 있다.

```python
from langgraph.graph import START, END

graph.add_edge("node1", "node2")

graph.add_edge(START, "first_node")
graph.add_edge("last_node", END)
```

- https://wikidocs.net/261590

# LangChain

## LangChain 예제

### LangChain 설치

```shell
pip install langchain langchain-openai langchain-chroma langchain-classic
```

### Chroma DB 초기화

chroma db collection 을 생성하고 Agent 관련 문서를 저장한다.

```python
def init_chroma():
    documents = [
        "Agents combine language models with tools to create systems that can reason about tasks, decide which tools to use, and iteratively work towards solutions.",
        "An LLM Agent runs tools in a loop to achieve a goal.",
        "An agent runs until a stop condition is met - i.e., when the model emits a final output or an iteration limit is reached."
    ]
    
    embedding_function = OpenAIEmbeddingFunction(model_name=EMBEDDING_MODEL)

    chroma = chromadb.EphemeralClient()
    collection = chroma.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function
    )

    collection.add(
        ids=[f"doc_{i + 1}" for i in range(len(documents))],
        documents=documents
    )
```

### LangChain 사용하지 않는 코드

### LangChain 사용하는 코드

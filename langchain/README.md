# LangChain

## LangChain 예제

### Without LangChain

langchain 을 사용하지 않고 OpenAI SDK 과 Chroma DB 를 사용하여 간단한 LLM agent 를 개발한다.

#### 패키지 설치

```shell
pip install dotenv openai chromadb
```

#### Chroma DB 초기화

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

#### LLM agent

```python
query = "AI Agent 에 대해서 설명해줘."

client = OpenAI()

# Retrieval
embedding = client.embeddings.create(
    model=EMBEDDING_MODEL,
    input=query
).data[0].embedding

chroma = chromadb.Client()
collection = chroma.get_collection(name=COLLECTION_NAME)
results = collection.query(
    query_embeddings=[embedding],
    n_results=3
)

# Prompt 구성
context = "\n".join(results["documents"][0])
prompt = f"""
Context:
{context}

Question:
{query}

Answer:
"""

# LLM 호출
response = client.responses.create(
    model=LLM_MODEL,
    input=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

print(response.output_text)
```

### With LangChain

langchain 을 사용하여 LLM agent 를 개발한다.

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
def init_chroma_collection():
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

    return collection
```

#### LLM agent

```python
query = "AI Agent 에 대해서 설명해줘."

collection = init_chroma_collection()
results = collection.query(
    query_texts=[query],
    n_results=3
)

context = "\n".join(results["documents"][0])
prompt = f"""
Context:
{context}

Question:
{query}

Answer:
"""

client = OpenAI()
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

아래 문서들을 참고해서 개발했다.

- https://docs.langchain.com/oss/python/langchain/knowledge-base
- https://docs.langchain.com/oss/python/langchain/rag
- https://wikidocs.net/231600

#### 패키지 설치

```shell
pip install dotenv langchain-openai langchain-core langchain
```

#### VectorStore 초기화

Chroma DB 대신 langchain 의 InMemoryVectorStore 를 VectorStore 로 사용했다.

```python
def init_vector_store():
    documents = [
        "Agents combine language models with tools to create systems that can reason about tasks, decide which tools to use, and iteratively work towards solutions.",
        "An LLM Agent runs tools in a loop to achieve a goal.",
        "An agent runs until a stop condition is met - i.e., when the model emits a final output or an iteration limit is reached."
    ]
    documents = [Document(page_content=doc) for doc in documents]

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vector_store = InMemoryVectorStore(embedding=embeddings)
    vector_store.add_documents(documents=documents)

    return vector_store
```

#### LLM Agent

langchain 을 사용하여 RAG 를 구성하고 쿼리의 답변을 생성하는 간단한 LLM agent 를 개발했다.

InMemoryVectorStore retriever 와 프롬프트 템플릿, ChatOpenAI, 그리고 문자열 출력 parser 로 rag_chain 을 구성했다.

```python
query = "AI Agent 에 대해서 설명해줘."

vector_store = init_vector_store()
retriever = vector_store.as_retriever()

prompt = ChatPromptTemplate.from_template("""
Context:
{context}

Question:
{question}

Answer:
""")

def format_docs(docs):
    return "\n".join(doc.page_content for doc in docs)

model = ChatOpenAI(model=LLM_MODEL)

rag_chain = (
    {'context': retriever | format_docs, 'question': RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

response = rag_chain.invoke(input=query)
print(response)
```

## LanChain LLM Chain

[LanChain랭체인(LangChain) 입문부터 응용까지 [ver 1.0+]](https://wikidocs.net/book/14473)

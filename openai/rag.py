from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from openai import OpenAI

import chromadb


LLM_MODEL = "gpt-5"
EMBEDDING_MODEL = "text-embedding-3-small"
COLLECTION_NAME="my-collection"
QUERY = "What is AcmeDB optimized for?"


def without_rag():
    client = OpenAI()

    response = client.responses.create(
        model=LLM_MODEL,
        input=[
            {"role": "user", "content": QUERY}
        ]
    )

    print("=== Without RAG ===")
    print(response.output_text)


def with_rag():
    client = OpenAI()

    # vector db 초기화
    chroma_client = chromadb.Client()
    embedding_function = OpenAIEmbeddingFunction(model_name=EMBEDDING_MODEL)
    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function
    )

    # 문서 저장
    documents = [
        "AcmeDB is a distributed database optimized for write-heavy workloads. It uses LSM-tree and supports horizontal scaling."
    ]
    collection.add(
        documents=documents,
        ids=["1"]
    )

    # 관련 문서 조회
    results = collection.query(
        query_texts=[QUERY],
        n_results=1
    )
    documents = results["documents"][0]

    # prompt 생성
    context = "\n".join(documents)

    prompt = f"""
    Answer based only on the context below.

    Context:
    {context}

    Question:
    {QUERY}
    """

    response = client.responses.create(
        model=LLM_MODEL,
        input=[
            {"role": "user", "content": prompt}
        ]
    )

    print("\n=== With RAG ===")
    print(response.output_text)


if __name__ == "__main__":
    print(f"query={QUERY}")

    without_rag()

    with_rag()

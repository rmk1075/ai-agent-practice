import chromadb

from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

LLM_MODEL = "gpt-5"
EMBEDDING_MODEL = "text-embedding-3-small"
COLLECTION_NAME = "langchain-collection"


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
        ids=[f"doc{i + 1}" for i in range(len(documents))],
        documents=documents
    )


if __name__ == "__main__":
    init_chroma()
    
    query = "AI Agent 에 대해서 설명해줘."

    client = OpenAI()

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

    context = "\n".join(results["documents"][0])
    prompt = f"""
Context:
{context}

Question:
{query}

Answer:
"""

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

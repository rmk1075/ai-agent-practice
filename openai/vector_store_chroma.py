from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv

import chromadb


load_dotenv()

EMBEDDING_MODEL = "text-embedding-3-small"

embedding_function = OpenAIEmbeddingFunction(model_name=EMBEDDING_MODEL)

# in-memory client
client = chromadb.EphemeralClient()

collection = client.create_collection(
    name="my_collection",
    embedding_function=embedding_function
)

# add documents
documents = [
    "FastAPI is a modern Python web framework for building APIs with high performance.",
    "Kubernetes is used to orchestrate containerized applications at scale.",
    "Grilling steak requires high heat and proper seasoning for best flavor.",
    "A balanced diet includes vegetables, proteins, and healthy fats.",
    "Squats and deadlifts are essential exercises for building lower body strength."
]

ids = [f"doc_{i}" for i in range(len(documents))]

collection.add(
    ids=ids,
    documents=documents
)

# query
queries = [
    "How to build scalable backend systems?",
    "What should I eat to stay healthy?",
    "Best way to cook meat with fire",
    "Exercises for strong legs"
]

for query in queries:
    result = collection.query(
        query_texts=[query],
        n_results=2 # query 마다 2개의 답변을 반환
    )

    print(f"[Query] {query}")
    for i, document in enumerate(result["documents"][0]):
        print(f"    -> Result {i + 1}: {document}")

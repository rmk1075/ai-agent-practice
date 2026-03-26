import chromadb

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings


load_dotenv()

LLM_MODEL = "gpt-5"
EMBEDDING_MODEL = "text-embedding-3-small"
COLLECTION_NAME = "langchain-collection"


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


# if __name__ == "__main__":
#     vector_store = init_vector_store()
    
#     query = "AI Agent 에 대해서 설명해줘."

#     docs = vector_store.similarity_search(query=query, k=3)
#     retriever = vector_store.as_retriever()
#     llm = ChatOpenAI(model=LLM_MODEL)
#     embedding = OpenAIEmbeddings(model=EMBEDDING_MODEL)

#     chroma = Chroma(
#         collection_name=COLLECTION_NAME,
#         embedding_function=embedding
#     )

#     retriever = chroma.as_retriever()

#     prompt = ChatPromptTemplate.from_template("""
# Context:
# {context}

# Question:
# {input}

# Answer:
# """)

#     document_chain = create_stuff_documents_chain(llm, prompt)
#     rag_chain = create_retrieval_chain(retriever, document_chain)

#     response = rag_chain.invoke({"input": query})
#     print(response["answer"])

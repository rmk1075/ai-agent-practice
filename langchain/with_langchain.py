from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


load_dotenv()

LLM_MODEL = "gpt-5"
EMBEDDING_MODEL = "text-embedding-3-small"


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


if __name__ == "__main__":
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

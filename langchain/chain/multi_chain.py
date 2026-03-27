from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough


llm = init_chat_model("gpt-4o-mini")

# Sequential
def sequential_chain():
    # 1단계: 한국어를 영어로 번역
    translate_prompt = ChatPromptTemplate.from_template(
        "다음 한국어를 영어로 번역하세요: {korean_word}"
    )

    # 2단계: 영어 단어 설명
    explain_prompt = ChatPromptTemplate.from_template(
        "다음 영어 단어를 한국어로 자세히 설명하세요: {english_word}"
    )

    # 체인 1: 번역
    chain1 = translate_prompt | llm | StrOutputParser()

    # 체인 2: 번역 결과를 입력으로 사용
    chain2 = (
        {"english_word": chain1}
        | explain_prompt
        | llm
        | StrOutputParser()
    )

    # 실행
    result = chain2.invoke({"korean_word": "인공지능"})
    print(result)


# Parallel
def parallel_chain():
    # 1단계: 한국어를 영어로 번역
    translate_prompt = ChatPromptTemplate.from_template(
        "다음 한국어를 영어로 번역하세요: {korean_word}"
    )

    # 2단계: 영어 단어 설명
    explain_prompt = ChatPromptTemplate.from_template(
        "다음 영어 단어를 한국어로 자세히 설명하세요: {english_word}"
    )

    # 체인 1: 번역
    chain1 = translate_prompt | llm | StrOutputParser()

    # 체인 2: 번역 결과를 입력으로 사용
    chain2 = (
        {"english_word": chain1}
        | explain_prompt
        | llm
        | StrOutputParser()
    )

    # 실행
    result = chain2.invoke({"korean_word": "인공지능"})
    print(result)


# Branching
def branching_chain():
    # 3단계 처리: 주제 분석 → 개요 작성 → 본문 작성
    analyze_prompt = ChatPromptTemplate.from_template(
        "다음 주제의 핵심 키워드 3개를 추출하세요: {topic}"
    )

    outline_prompt = ChatPromptTemplate.from_template(
        """다음 키워드를 바탕으로 글의 개요를 작성하세요:
    키워드: {keywords}
    원본 주제: {topic}"""
    )

    content_prompt = ChatPromptTemplate.from_template(
        """다음 개요를 바탕으로 300자 내외의 글을 작성하세요:
    개요: {outline}"""
    )

    # 체인 구성
    chain = (
        {"topic": RunnablePassthrough()}
        # | RunnableLambda(lambda x: (print(f"[after topic] {x}"), x)[1])
        | RunnablePassthrough.assign(
            keywords=analyze_prompt | llm | StrOutputParser()
        )
        # | RunnableLambda(lambda x: (print(f"[after keywords] {x}"), x)[1])
        | RunnablePassthrough.assign(
            outline=outline_prompt | llm | StrOutputParser()
        )
        # | RunnableLambda(lambda x: (print(f"[after outline] {x}"), x)[1])
        | content_prompt
        | llm
        | StrOutputParser()
    )

    result = chain.invoke("기후 변화와 지속 가능한 발전")
    print(result)



if __name__ == "__main__":
    # sequential_chain()
    # parallel_chain()
    branching_chain()

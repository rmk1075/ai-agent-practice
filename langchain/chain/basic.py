# LCEL (LangChain Expression Language)
import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


load_dotenv()

# 프롬프트
prompt = ChatPromptTemplate.from_template(
    "{topic}에 대해 간단히 설명해주세요."
)

# LLM
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-5"
)

# 체인 구성 - 프롬프트 | LLM | 출력 파서
chain = prompt | llm | StrOutputParser()

# 체인 실행 - 문자열 형식 결과 반환
# invoke(): 단일 입력 동기 실행
result = chain.invoke({"topic": "머신러닝"})
print(result)  # 문자열

# 체인 배치
# batch(): 다중 입력 병렬 실행
results = chain.batch([
    {"topic": "AI"},
    {"topic": "ML"},
    {"topic": "DL"},
])
for r in results:
    print(r)

# stream(): 토큰 단위 스트리밍
for chunk in chain.stream({"topic": "AI"}):
    print(chunk, end="", flush=True)

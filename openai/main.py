from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI()

response = client.responses.create(
    model="gpt-5.4",
    input="처음 만난 사람에게 하기 좋은 인사말 하나만 추천해 줘."
)

print(response.output_text)

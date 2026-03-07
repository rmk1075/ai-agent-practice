from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI()

# response = client.responses.create(
#     model="gpt-5.4",
#     input="처음 만난 사람에게 하기 좋은 인사말 하나만 추천해 줘."
# )

# print(response.output_text)

# # image url 분석
# response = client.responses.create(
#     model="gpt-5",
#     input=[
#         {
#             "role": "user",
#             "content": [
#                 {
#                     "type": "input_text",
#                     "text": "어떤 그림인지 설명해줘.",
#                 },
#                 {
#                     "type": "input_image",
#                     "image_url": "https://api.nga.gov/iiif/a2e6da57-3cd1-4235-b20e-95dcaefed6c8/full/!800,800/0/default.jpg"
#                 }
#             ]
#         }
#     ]
# )

# print(response.output_text)

# pdf url 분석
response = client.responses.create(
    model="gpt-5",
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "문서를 분석하고 내용을 요약해줘.",
                },
                {
                    "type": "input_file",
                    "file_url": "https://www.berkshirehathaway.com/letters/2024ltr.pdf",
                },
            ],
        },
    ]
)

print(response.output_text)

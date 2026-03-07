# OpenAI API

## OpenAI API Init

OpenAI API quickstart 가이드에 따라 API 사용환경 구성 및 사용예제 작성

- [OpenAI API Developer quickstart
](https://developers.openai.com/api/docs/quickstart)

### API Key 생성

OpenAI API 를 사용하려면 API Key 를 생성해야 한다. OpenAI 계정을 만들고 billing 등록 등을 수행해야 한다.

자세한 내용은 아래 링크를 참고하자.

- [create and export an api key](https://developers.openai.com/api/docs/quickstart#create-and-export-an-api-key)

Key 를 생성했으면 호스트에서 사용할 수 있도록 OPENAI_API_KEY 라는 시스템 환경변수로 등록하거나 .env 와 같은 환경변수 파일에 저장해두자.

### API Call in Python

Python 으로 OpenAI API 를 호출하는 예제를 만들어 보겠다.

#### Install OpenAI SDK

코드 작성에 앞서 OpenAI SDK 를 설치한다.

```shell
$ pip install openai
```

SDK 가 설치되면 아래와 같이 Python 코드에서 모듈을 호출하여 사용할 수 있다.

```python
from openai import OpenAI
```

#### Call OpenAI API

```shell
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI()

response = client.responses.create(
    model="gpt-5.4",
    input="처음 만난 사람에게 하기 좋은 인사말 하나만 추천해 줘."
)

print(response.output_text)
```

OpenAI client 를 생성하고 responses API 를 호출하는 예제이다.

.env 파일에 저장된 OPENAI_API_KEY 환경변수를 를 호출하기 위해 load_dotenv() 를 호출한다.

OpenAI client 를 생성하고, client.responses.create 를 통해 API 를 호출하고, API 의 응답 결과에서 output_text 를 추출하여 화면에 출력한다.

```text
안녕하세요, 처음 뵙겠습니다. 잘 부탁드립니다!
```

코드를 실행하면 input 으로 준 `"처음 만난 사람에게 하기 좋은 인사말 하나만 추천해 줘."` 요청에 대한 응답으로 `"안녕하세요, 처음 뵙겠습니다. 잘 부탁드립니다!"` 이 출력되는 것을 확인할 수 있다.

#### Analyze images and files

이미지 URL 이나 파일들, 또는 PDF 문서 등을 모델을 통해서 분석하거나 텍스트를 추출할 수도 있다.

```python
response = client.responses.create(
    model="gpt-5",
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "어떤 그림인지 설명해줘.",
                },
                {
                    "type": "input_image",
                    "image_url": "https://api.nga.gov/iiif/a2e6da57-3cd1-4235-b20e-95dcaefed6c8/full/!800,800/0/default.jpg"
                }
            ]
        }
    ]
)

print(response.output_text)
```

위 코드는 이미지 url 을 주고 이에 대한 설명을 부탁하고 있다. 해당 url 은 아래 이미지의 링크이다.

![예제 사진](https://api.nga.gov/iiif/a2e6da57-3cd1-4235-b20e-95dcaefed6c8/full/!800,800/0/default.jpg)

코드를 실행하면 아래와 같이 이미지에 대한 설명들이 출력되는 것을 확인할 수 있다.

```text
- 작품: 라 무스메(La Mousmé)  
- 화가/연도: 빈센트 반 고흐, 1888년(프랑스 아를)  
- 내용: 등받이가 둥근 의자에 소녀가 앉아 있고, 빨강·파랑 줄무늬 상의와 파란 바탕에 주황 점무늬 치마를 입었어요. 손에는 작은 꽃(올레앤더 한 줄기)을 들고 있습니다. 배경은 밝은 연녹색의 평평한 면으로 처리됐습니다.  
- 특징: 굵고 빠른 붓질, 강한 보색 대비(빨강–파랑, 파랑–주황), 단순화된 배경과 장식적 무늬가 어우러진 전형적인 후기인상주의적 초상. 제목의 ‘무스메’는 일본 소녀를 뜻하는 말로, 반 고흐의 일본 취향(자포니즘) 영향이 반영돼 있습니다.  
- 해석: 소녀와 꽃은 젊음·생기를 상징하며, 반 고흐가 밝은 색채와 패턴 실험을 한 시기의 의욕적인 초상화입니다.
```

이번에는 pdf 파일의 url 을 주고 이에 대한 분석을 요청해보겠다.

```python
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
```

이전 요청들보다 시간이 좀 걸리긴 했지만 아래와 같이 정확한 분석을 전달해주었다.

```text
다음은 2025년 2월 22일자 워런 버핏의 2024년 버크셔 해서웨이 주주 서한(발췌본) 분석 및 핵심 요약입니다.

한 줄 요약
- 2024년 버크셔는 보험 투자이익과 GEICO의 턴어라운드로 기대 이상 실적을 기록했고, 현금이 많다는 인식과 달리 여전히 자금을 주식(지배/부분지분)에 크게 배분하고 있습니다. 미국 연방 법인세 268억 달러를 납부하는 사상 최대 기록을 세웠고, 일본 상사 5개사 투자를 장기 확대 중입니다. 승계, 보험의 가격징계, 장기 복리와 자본주의에 대한 확고한 철학을 재확인했습니다.

경영 철학·거버넌스
- 실수에 대한 솔직함: 2019~23년 서한에서 “mistake/-error”를 16회 언급. “칭찬은 실명, 비판은 범주” 원칙 재확인. 문제는 미루지 말고 즉시 시정.
- 승계: 94세인 버핏은 곧 그렉 아벨이 CEO로서 서한을 쓰게 될 것이라며, 주주에게 ‘보고서’를 성실히 제공해야 한다는 철학을 공유한다고 강조.
- 인사 철학: 학벌은 보지 않음. 타고난 소질·성향의 비중이 크다고 판단. 피트 리글(포리스트 리버 설립자) 사례로 ‘신뢰·성과 중심’ 접근을 소개.

...
```

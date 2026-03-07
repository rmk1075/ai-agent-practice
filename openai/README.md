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

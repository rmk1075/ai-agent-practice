import random
import time


def fake_agent_stream(message: str):
    text = f"AI response to: {message}"

    for token in text.split(" "):
        time.sleep(0.3)
        yield token + " "

    for i in range(random.randint(0, 10)):
        time.sleep(0.3)
        yield str(i) + " "

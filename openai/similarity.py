from itertools import combinations

import numpy as np
from openai import OpenAI


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

if __name__ == "__main__":
    text = [
        "apple",
        "banana",
        "yellow",
        "iphone",
    ]

    client = OpenAI()

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    embeddings = [d.embedding for d in response.data]

    for i, j in combinations(range(len(text)), 2):
        similarity = cosine_similarity(embeddings[i], embeddings[j])
        print(f"{text[i]}:{text[j]} > similarity={similarity}")
import os
import requests
import re


def request(prompt: str, n_predict: int = 128) -> str:
    IS_PRODUCTION = os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/token")
    response = requests.post(
        (
            "http://llama.llama.cluster.local:8080/v1/chat/completions"
            if IS_PRODUCTION
            else "http://llama-llama-service:8080/v1/chat/completions"
        ),
        json={
            "messages": [
                {
                    "role": "system",
                    "content": """
                      Your are a helpful assistant that answers questions about the environment.
                      Your should give humanized short responses.
                      Your should not pretend to be a human or represent yourself with words like "I".
                      Your responses should be complete sentences.
                    """,
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": n_predict,
            "temperature": 0.7,
        },
        timeout=60,
    )
    content: str = response.json()["choices"][0]["message"]["content"]

    # Remove leading "\n" and trailing "\n"
    content = content.strip("\n")

    # Remove sentences that are incomplete,
    # via removing everything after a period that doesn't end a sentence
    content = re.sub(r"(?<!\.)\s+(?!\w)", "", content)

    # Remove leading and trailing quotes
    content = content.strip("\"'")

    return content

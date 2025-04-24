import os
import requests


def request(prompt: str, n_predict: int = 128) -> str:
    IS_PRODUCTION = os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/token")
    response = requests.post(
        (
            "http://llama.llama.cluster.local:8080/completion"
            if IS_PRODUCTION
            else "http://llama-llama-service:8080/completion"
        ),
        json={"prompt": prompt, "n_predict": n_predict},
        timeout=30,
    )

    return response.json()["content"]

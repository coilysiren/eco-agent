import os
import re

import requests
import structlog

from . import telemetry as _telemetry

logger = structlog.get_logger()
telemetry = _telemetry.Telemetry()


def request(prompt: str, n_predict: int = 128) -> str:
    logger.info(
        "prompt request starting",
        prompt=prompt,
        n_predict=n_predict,
    )

    with telemetry.tracer.start_as_current_span("PromptRequest") as span:
        IS_PRODUCTION = os.path.exists(
            "/var/run/secrets/kubernetes.io/serviceaccount/token"
        )
        response = requests.post(
            (
                "http://llama-service.llama.svc.cluster.local:8080/v1/chat/completions"
                if IS_PRODUCTION
                else "http://llama-llama-service:8080/v1/chat/completions"
            ),
            json={
                "messages": [
                    {
                        "role": "system",
                        "content": """
                        You are a helpful assistant that answers environmental questions.
                        Give short, clear, humanized answers in complete sentences.
                        Avoid self-references, meta-comments, and words like “input”, “prompt”, “output”, or “response”.
                        """,
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": n_predict,
                "temperature": 0.7,
            },
            timeout=60,
        )
        response.raise_for_status()
        content: str = response.json()["choices"][0]["message"]["content"]

        # Remove leading "\n" and trailing "\n"
        content = content.strip("\n")

        # Remove sentences that are incomplete,
        # via removing everything after a period that doesn't end a sentence
        content = re.sub(r"(?<!\.)\s+(?!\w)", "", content)

        # Remove leading and trailing quotes
        content = content.strip("\"'")

        span.set_attribute("prompt", prompt)
        span.set_attribute("content", content)

    logger.info(
        "prompt request completed",
        prompt=prompt,
        n_predict=n_predict,
        content=content,
    )

    return content

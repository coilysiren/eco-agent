import os

import fastapi
import opentelemetry.instrumentation.fastapi as otel_fastapi
import structlog
import structlog.processors
import boto3
import requests

from . import application
from . import discord

(app, limiter) = application.init()

structlog.configure(
    processors=[
        structlog.processors.JSONRenderer(sort_keys=True),
    ]
)


IS_PRODUCTION = os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/token")


@app.get("/")
@limiter.limit("1/second")
async def root(request: fastapi.Request):
    return ["hello", "world"]


@app.get("/explode")
@app.get("/explode/")
@limiter.limit("1/second")
async def trigger_error(request: fastapi.Request):
    return 1 / 0


@app.get("/health")
@app.get("/health/")
@limiter.limit("1/second")
async def health(request: fastapi.Request):
    ssm = boto3.client("ssm")
    token = ssm.get_parameter(Name="/eco/discord-bot-token", WithDecryption=True)["Parameter"]["Value"]
    server_id = ssm.get_parameter(Name="/discord/server-id", WithDecryption=True)["Parameter"]["Value"]
    bot_channel_id = ssm.get_parameter(Name="/discord/channel/bots", WithDecryption=True)["Parameter"]["Value"]

    response = requests.post(
        (
            "http://llama.llama.cluster.local:8080/completion"
            if IS_PRODUCTION
            else "http://llama-llama-service:8080/completion"
        ),
        json={"prompt": "Is the model healthy?", "n_predict": 128},
        timeout=30,
    )

    if response.status_code != 200:
        return {"status": "error", "message": "Model is not healthy"}

    content = response.json()["content"]

    (_, guild) = await discord.Client.init(token, int(server_id))

    channel = guild.get_channel(int(bot_channel_id))
    await channel.send(content)

    return {"status": "ok"}


otel_fastapi.FastAPIInstrumentor.instrument_app(app)

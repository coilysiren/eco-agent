import fastapi
import opentelemetry.instrumentation.fastapi as otel_fastapi
import structlog
import structlog.processors
import boto3
import requests

from . import application
from . import discord
from . import model

(app, limiter) = application.init()

structlog.configure(
    processors=[
        structlog.processors.JSONRenderer(sort_keys=True),
    ]
)


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

    model.request("Is the model healthy?")

    (_, guild) = await discord.Client.init(token, int(server_id))

    channel = guild.get_channel(int(bot_channel_id))
    await channel.send("model is healthy")

    return {"status": "ok"}


@app.post("/chat")
@app.post("/chat/")
@limiter.limit("1/second")
async def chat(request: fastapi.Request):
    # get the prompt from the request body
    data = await request.json()
    prompt = data["prompt"]

    # call the model
    response = model.request(prompt)

    return {"content": response}


otel_fastapi.FastAPIInstrumentor.instrument_app(app)

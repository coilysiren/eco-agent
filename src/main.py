import fastapi
import fastapi.responses
import opentelemetry.instrumentation.fastapi as otel_fastapi
import structlog
import structlog.processors
import boto3
import discord

from . import discord as _discord
from . import application
from . import model

(app, limiter) = application.init()

structlog.configure(
    processors=[
        structlog.processors.JSONRenderer(sort_keys=True),
    ]
)

discord_client = _discord.Client()


@app.get("/")
@limiter.limit("1/second")
async def root(request: fastapi.Request):
    return ["hello", "world"]


@app.get("/explode")
@app.get("/explode/")
@limiter.limit("1/second")
async def trigger_error(request: fastapi.Request):
    return 1 / 0


@app.post("/subscribe")
@app.post("/subscribe/")
@limiter.limit("1/second")
async def subscribe(request: fastapi.Request):
    ssm = boto3.client("ssm")
    token_response = ssm.get_parameter(Name="/eco/discord-bot-token", WithDecryption=True)
    token = token_response["Parameter"]["Value"]

    data = await request.json()
    channel_id = data["channel"]
    server_id = data["server"]

    # The client is a thread-safe singleton,
    # so we can init it once and then use it for all requests.
    client = await discord_client.init(token, int(server_id))

    # get the channel, if it doesn't exist, return a 400, if it exists, subscribe to it
    channel = client.get_channel(int(channel_id))
    if not channel:
        return fastapi.responses.JSONResponse(
            {"detail": "channel not found"}, status_code=400
        )
    client.subscribe(channel_id)

    return {"status": "ok"}


@app.get("/health")
@app.get("/health/")
@limiter.limit("1/second")
async def health(request: fastapi.Request):
    ssm = boto3.client("ssm")
    token = ssm.get_parameter(Name="/eco/discord-bot-token", WithDecryption=True)
    token = token["Parameter"]["Value"]
    server_id = ssm.get_parameter(Name="/discord/server-id", WithDecryption=True)
    server_id = server_id["Parameter"]["Value"]
    bot_channel_id = ssm.get_parameter(Name="/discord/channel/bots", WithDecryption=True)
    bot_channel_id = bot_channel_id["Parameter"]["Value"]

    model.request("model is healthy")

    await discord_client.init(token, int(server_id))
    channel = discord_client.get_channel(int(bot_channel_id))

    if channel is not None and isinstance(channel, discord.TextChannel):
        await channel.send("discord bot is healthy")

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

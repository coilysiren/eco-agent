import fastapi
import opentelemetry.instrumentation.fastapi as otel_fastapi
import structlog
import structlog.processors
import boto3

from . import application

(app, limiter) = application.init()

structlog.configure(
    processors=[
        structlog.processors.JSONRenderer(sort_keys=True),
    ]
)

ssm = boto3.client("ssm")


@app.get("/")
@limiter.limit("10/second")
async def root(request: fastapi.Request):
    return ["hello", "world"]


@app.get("/explode")
@app.get("/explode/")
async def trigger_error():
    return 1 / 0


@app.get("/health")
@app.get("/health/")
async def health():
    ssm.get_parameter(Name="/eco/discord-bot-token")["Parameter"]["Value"]
    return {"status": "ok"}


otel_fastapi.FastAPIInstrumentor.instrument_app(app)

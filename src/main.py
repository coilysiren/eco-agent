import fastapi
import opentelemetry.instrumentation.fastapi as otel_fastapi
import structlog
import structlog.processors

from . import application

(app, limiter) = application.init()

structlog.configure(
    processors=[
        structlog.processors.JSONRenderer(sort_keys=True),
    ]
)


@app.get("/")
@limiter.limit("10/second")
async def root(request: fastapi.Request):
    return ["hello", "world"]


@app.get("/explode")
@app.get("/explode/")
async def trigger_error():
    return 1 / 0


otel_fastapi.FastAPIInstrumentor.instrument_app(app)

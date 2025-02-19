from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from aws_lambda_powertools import Metrics, Logger
from aws_lambda_powertools.metrics import MetricUnit
import json
import os
from time import perf_counter
import traceback
import httpx


app = FastAPI()

logger = Logger(
    service=os.getenv("SERVICE_NAME", "my-boilerplate-service"),
    level=os.getenv("LOG_LEVEL", "INFO"),
)
metrics = Metrics(namespace="MyBoilerPlateNamespace")
metrics.set_default_dimensions(
    Service=os.getenv("SERVICE_NAME", "my-boilerplate-service"),
)

LITELLM_PROXY_URL = os.getenv("LITELLM_PROXY_URL")
LITELLM_PROXY_KEY = ""  # No key as of yet


@app.middleware("http")
async def add_metrics_and_logging(request: Request, call_next):
    if request.url.path == "/healthcheck":
        return await call_next(request)

    request.state.start_time = perf_counter()
    logger.info(
        "Request started",
        extra={
            "path": request.url.path,
            "method": request.method,
            "query_params": str(request.query_params),
        },
    )

    try:
        response = await call_next(request)
        duration = (perf_counter() - request.state.start_time) * 1000

        metrics.add_metric(
            name="ResponseTime", unit=MetricUnit.Milliseconds, value=duration
        )
        metrics.add_metric(name="RequestCount", unit=MetricUnit.Count, value=1)

        logger.info(
            "Request completed",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": duration,
            },
        )
        return response

    except Exception as e:
        logger.exception(
            "Request failed",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
        )

        metrics.add_metric(name="Errors", unit=MetricUnit.Count, value=1)

        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")

    finally:
        metrics.flush_metrics()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "HTTP exception occurred",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
    )
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "healthy"}


@app.get("/")
async def hello():
    logger.info("Processing hello request")

    metrics.add_metric(name="HelloEndpointCalled", unit=MetricUnit.Count, value=1)
    return {"message": "Hello from container <3"}


@app.get("/error")
async def trigger_error():
    logger.error("About to raise an error")
    raise HTTPException(status_code=400, detail="Test error")


@app.post("/v1/chat/completions")
async def chat_completion(request: Request):
    try:
        # Log request details
        headers = dict(request.headers)
        raw_body = await request.body()
        logger.debug(
            "Received request",
            extra={
                "headers": headers,
                "raw_body": raw_body.decode() if raw_body else None,
                "content_type": headers.get("content-type"),
                "content_length": headers.get("content-length"),
            },
        )

        if not raw_body:
            raise HTTPException(status_code=400, detail="Empty request body")

        try:
            body = await request.json()
        except json.JSONDecodeError as e:
            logger.error(
                "JSON decode error",
                extra={
                    "error": str(e),
                    "raw_body": raw_body.decode() if raw_body else None,
                },
            )
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

        logger.info(
            "Forwarding chat completion request to LiteLLM proxy",
            extra={"model": body.get("model")},
        )

        metrics.add_metric(
            name="ChatCompletionRequests", unit=MetricUnit.Count, value=1
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LITELLM_PROXY_URL}/v1/chat/completions",
                json=body,
                headers=(
                    {}
                    if not LITELLM_PROXY_KEY
                    else {"Authorization": f"Bearer {LITELLM_PROXY_KEY}"}
                ),
            )

            if response.status_code != 200:
                logger.error(
                    "LiteLLM proxy request failed",
                    extra={
                        "status_code": response.status_code,
                        "response": response.text,
                    },
                )
                raise HTTPException(
                    status_code=response.status_code, detail=response.text
                )

            return response.json()

    except Exception as e:
        logger.exception("Chat completion request failed")
        metrics.add_metric(name="ChatCompletionErrors", unit=MetricUnit.Count, value=1)
        raise HTTPException(status_code=500, detail=str(e))

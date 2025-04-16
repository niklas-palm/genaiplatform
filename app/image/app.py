from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from aws_lambda_powertools import Metrics, Logger
from aws_lambda_powertools.metrics import MetricUnit
import json
import os
from time import perf_counter
import traceback
import httpx
from httpx import TimeoutException

from schemas import ChatCompletionRequest

LONG_TIMEOUT = httpx.Timeout(timeout=120.0)  # 120 seconds

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
if not LITELLM_PROXY_URL:
    raise ValueError("LITELLM_PROXY_URL environment variable must be set")
    
# LiteLLM service API key if required - can be set via environment variable
LITELLM_PROXY_KEY = os.getenv("LITELLM_PROXY_KEY", "")


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
async def chat_completion(request: Request, chat_request: ChatCompletionRequest):
    try:
        # Log request details
        headers = dict(request.headers)
        logger.info(
            "Received request",
            extra={
                "headers": headers,
                "content_type": headers.get("content-type"),
                "content_length": headers.get("content-length"),
                "model": chat_request.model,
                "temperature": chat_request.temperature,
                "stream": chat_request.stream,
            },
        )

        logger.info(
            "Forwarding chat completion request to LiteLLM proxy",
            extra={"model": chat_request.model},
        )

        metrics.add_metric(
            name="ChatCompletionRequests", unit=MetricUnit.Count, value=1
        )

        async with httpx.AsyncClient(timeout=LONG_TIMEOUT) as client:
            try:
                response = await client.post(
                    f"{LITELLM_PROXY_URL}/v1/chat/completions",
                    json=chat_request.dict(),
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

            except TimeoutException as e:
                logger.error(f"Request to LiteLLM proxy timed out: {str(e)}")
                metrics.add_metric(
                    name="ChatCompletionTimeouts", unit=MetricUnit.Count, value=1
                )
                raise HTTPException(
                    status_code=504,
                    detail="Gateway Timeout: The request to the language model timed out.",
                )

    except HTTPException:
        # Re-raise HTTP exceptions (including our timeout exception)
        raise

    except Exception as e:
        logger.exception("Chat completion request failed")
        metrics.add_metric(name="ChatCompletionErrors", unit=MetricUnit.Count, value=1)
        raise HTTPException(status_code=500, detail=str(e))

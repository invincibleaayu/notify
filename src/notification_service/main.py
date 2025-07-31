"""Main FastAPI application for the notification service."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any

import structlog
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, REGISTRY
import uvicorn

from .config.settings import settings
from .presentation.api.v1 import notifications, health
from .infrastructure.fcm.fcm_client import FCMClient
from .infrastructure.valkey.valkey_client import ValkeyClient

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Create a custom registry to avoid conflicts
metrics_registry = CollectorRegistry()

# Metrics - register with custom registry
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP requests', 
    ['method', 'endpoint', 'status'],
    registry=metrics_registry
)
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds', 
    'HTTP request duration', 
    ['method', 'endpoint'],
    registry=metrics_registry
)
NOTIFICATION_SENT = Counter(
    'notifications_sent_total', 
    'Total notifications sent', 
    ['type', 'target'],
    registry=metrics_registry
)
NOTIFICATION_FAILED = Counter(
    'notifications_failed_total', 
    'Total notifications failed', 
    ['type', 'target'],
    registry=metrics_registry
)

# Global clients
fcm_client: FCMClient = None
valkey_client: ValkeyClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global fcm_client, valkey_client
    
    # Startup
    logger.info("Starting notification service", version=settings.app_version)
    
    try:
        # Initialize FCM client
        fcm_client = FCMClient()
        logger.info("FCM client initialized")
        
        # Initialize Valkey client
        valkey_client = ValkeyClient()
        await valkey_client.connect()
        logger.info("Valkey client initialized")
        
        yield
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise
    finally:
        # Shutdown
        logger.info("Shutting down notification service")
        
        if valkey_client:
            await valkey_client.disconnect()


# Create FastAPI app
app = FastAPI(
    title="Notification Service",
    description="A stateless notification management service using FastAPI and FCM",
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log all requests and track metrics."""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Log request
    logger.info(
        "HTTP request started",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    try:
        response = await call_next(request)
        
        # Track metrics
        duration = time.time() - start_time
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        # Log response
        logger.info(
            "HTTP request completed",
            request_id=request_id,
            status_code=response.status_code,
            duration=duration
        )
        
        return response
        
    except Exception as e:
        # Track failed requests
        duration = time.time() - start_time
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=500
        ).inc()
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        # Log error
        logger.error(
            "HTTP request failed",
            request_id=request_id,
            error=str(e),
            duration=duration
        )
        raise


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.error(
        "Unhandled exception",
        request_id=request_id,
        error=str(exc),
        method=request.method,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "request_id": request_id,
            "timestamp": time.time()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler."""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.warning(
        "HTTP exception",
        request_id=request_id,
        status_code=exc.status_code,
        detail=exc.detail,
        method=request.method,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail,
            "request_id": request_id,
            "timestamp": time.time()
        }
    )


# Dependency injection
def get_fcm_client() -> FCMClient:
    """Get FCM client dependency."""
    if fcm_client is None:
        raise HTTPException(status_code=503, detail="FCM client not available")
    return fcm_client


def get_valkey_client() -> ValkeyClient:
    """Get Valkey client dependency."""
    if valkey_client is None:
        raise HTTPException(status_code=503, detail="Valkey client not available")
    return valkey_client


# Include routers
app.include_router(
    notifications.router,
    prefix=f"{settings.api_prefix}/notifications",
    tags=["notifications"],
    dependencies=[Depends(get_fcm_client), Depends(get_valkey_client)]
)

app.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Notification Service",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs" if settings.debug else None
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(metrics_registry),
        media_type=CONTENT_TYPE_LATEST
    )


if __name__ == "__main__":
    uvicorn.run(
        "src.notification_service.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,  # Disable reload to avoid metric registration issues
        log_level=settings.log_level.lower()
    )
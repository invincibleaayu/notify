"""Health check API routes."""

import time
from datetime import datetime
from typing import Dict

import structlog
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from ....application.dto.notification_response import HealthCheckResponse
from ....infrastructure.fcm.fcm_client import FCMClient
from ....infrastructure.valkey.valkey_client import ValkeyClient

logger = structlog.get_logger()
router = APIRouter()

# Track startup time for uptime calculation
_startup_time = time.time()


@router.get("/", response_model=HealthCheckResponse)
async def health_check(
    fcm_client: FCMClient = Depends(),
    valkey_client: ValkeyClient = Depends()
):
    """Health check endpoint."""
    try:
        checks = {}
        
        # Check FCM client
        try:
            # Simple check - if client exists, consider it healthy
            checks["fcm"] = "healthy"
        except Exception as e:
            checks["fcm"] = f"unhealthy: {str(e)}"
        
        # Check Valkey client
        try:
            is_connected = await valkey_client.is_connected()
            checks["valkey"] = "healthy" if is_connected else "unhealthy: not connected"
        except Exception as e:
            checks["valkey"] = f"unhealthy: {str(e)}"
        
        # Determine overall status
        overall_status = "healthy" if all(
            status == "healthy" for status in checks.values()
        ) else "unhealthy"
        
        uptime_seconds = time.time() - _startup_time
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="0.1.0",
            uptime_seconds=uptime_seconds,
            checks=checks
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.get("/ready")
async def readiness_check(
    fcm_client: FCMClient = Depends(),
    valkey_client: ValkeyClient = Depends()
):
    """Readiness check endpoint."""
    try:
        # Check if all required services are ready
        valkey_ready = await valkey_client.is_connected()
        
        if not valkey_ready:
            raise HTTPException(status_code=503, detail="Valkey not ready")
        
        return {"status": "ready"}
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/live")
async def liveness_check():
    """Liveness check endpoint."""
    # Simple check - if we can respond, we're alive
    return {"status": "alive"}


@router.get("/info")
async def service_info():
    """Service information endpoint."""
    return {
        "service": "Notification Service",
        "version": "0.1.0",
        "description": "A stateless notification management service using FastAPI and FCM",
        "uptime_seconds": time.time() - _startup_time,
        "features": [
            "FCM integration",
            "Valkey event streaming",
            "Multi-platform support",
            "Topic-based messaging",
            "Batch notifications",
            "Health monitoring"
        ]
    } 
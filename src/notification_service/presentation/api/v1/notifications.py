"""Notification API routes."""

import time
import uuid
from typing import List

import structlog
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from ....application.dto.notification_request import (
    SendNotificationRequest,
    TopicNotificationRequest,
    BatchNotificationRequest,
    TopicSubscriptionRequest
)
from ....application.dto.notification_response import (
    SendNotificationResponse,
    TopicNotificationResponse,
    BatchNotificationResponse,
    TopicSubscriptionResponse,
    NotificationResult
)
from ....domain.entities.notification import Notification
from ....domain.value_objects.notification_type import NotificationType
from ....domain.value_objects.device_token import DeviceToken, DeviceTokenList
from ....domain.value_objects.topic import Topic
from ....domain.services.notification_service import NotificationDomainService
from ....infrastructure.fcm.fcm_client import FCMClient
from ....infrastructure.valkey.valkey_client import ValkeyClient
from ....config.settings import settings

logger = structlog.get_logger()
router = APIRouter()


@router.post("/send", response_model=SendNotificationResponse)
async def send_notification(
    request: SendNotificationRequest,
    fcm_client: FCMClient = Depends(),
    valkey_client: ValkeyClient = Depends(),
    http_request: Request = None
):
    """Send notification to device tokens."""
    start_time = time.time()
    notification_id = str(uuid.uuid4())
    
    try:
        # Convert request to domain objects
        logger.debug(f"Request: {request}")
        logger.debug(f"Request device tokens count: {len(request.device_tokens)}")
        if request.device_tokens:
            logger.debug(f"First device token: {request.device_tokens[0]}")
        device_tokens = DeviceTokenList(
            tokens=[
                DeviceToken(value=token.token, platform=token.platform)
                for token in request.device_tokens
            ],
            max_tokens=settings.max_tokens_per_request
        )
        logger.debug(f"Device tokens count: {len(device_tokens.tokens)}")
        if device_tokens.tokens:
            logger.debug(f"First device token value: {device_tokens.tokens[0].value}")
            logger.debug(f"First device token platform: {device_tokens.tokens[0].platform}")
        notification_type = NotificationType(
            value=request.notification_type,
            priority=request.priority
        )
        
        # Create notification using domain service
        domain_service = NotificationDomainService()
        notification = domain_service.create_notification(
            notification_type=notification_type,
            device_tokens=device_tokens,
            title=request.title,
            body=request.body,
            data=request.data,
            priority=request.priority,
            collapse_key=request.collapse_key,
            ttl=request.ttl,
            scheduled_at=request.scheduled_at
        )
        
        # Send notification via FCM
        device_token_values = [token.value for token in device_tokens.tokens]
        
        if len(device_token_values) == 1:
            # Single device
            result = await fcm_client.send_to_device(
                device_token=device_token_values[0],
                title=notification.title,
                body=notification.body,
                data=notification.data,
                priority=notification.priority,
                collapse_key=notification.collapse_key,
                ttl=notification.ttl
            )
            
            if result["success"]:
                notification.mark_sent()
                sent_count = 1
                failed_count = 0
                status = "success"
            else:
                notification.mark_failed(result["error"])
                sent_count = 0
                failed_count = 1
                status = "failed"
            
            results = [NotificationResult(
                notification_id=notification_id,
                status=status,
                sent_count=sent_count,
                failed_count=failed_count,
                error_message=result.get("error"),
                target_count=1
            )]
            
        else:
            # Multiple devices
            result = await fcm_client.send_to_multiple_devices(
                device_tokens=device_token_values,
                title=notification.title,
                body=notification.body,
                data=notification.data,
                priority=notification.priority,
                collapse_key=notification.collapse_key,
                ttl=notification.ttl
            )
            
            if result["success"]:
                notification.mark_sent(result["success_count"])
                if result["failure_count"] > 0:
                    notification.mark_failed("Some devices failed", result["failure_count"])
                
                sent_count = result["success_count"]
                failed_count = result["failure_count"]
                status = "partial" if failed_count > 0 else "success"
            else:
                notification.mark_failed(result["error"])
                sent_count = 0
                failed_count = len(device_token_values)
                status = "failed"
            
            results = [NotificationResult(
                notification_id=notification_id,
                status=status,
                sent_count=sent_count,
                failed_count=failed_count,
                error_message=result.get("error"),
                target_count=len(device_token_values)
            )]
        
        # Store notification status in Valkey
        notification_status = {
            "notification_id": notification_id,
            "type": notification.notification_type.value,
            "target_count": notification.get_target_count(),
            "sent_count": sent_count,
            "failed_count": failed_count,
            "status": status,
            "created_at": notification.created_at.isoformat(),
            "error_message": result.get("error"),
            "message_id": result.get("message_id")
        }
        
        await valkey_client.set(f"notification:{notification_id}", notification_status, ex=3600)  # Expire in 1 hour
        
        # Publish event to Valkey
        await valkey_client.publish(
            channel="notification.sent",
            message=notification_status
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return SendNotificationResponse(
            success=status != "failed",
            notification_id=notification_id,
            results=results,
            total_sent=sent_count,
            total_failed=failed_count,
            total_targets=notification.get_target_count(),
            processing_time_ms=processing_time,
            message=f"Notification sent successfully to {sent_count} devices"
        )
        
    except Exception as e:
        logger.error(
            f"Failed to send notification {e}",
            notification_id=notification_id,
            error=str(e),
            request_id=getattr(http_request.state, 'request_id', None)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/topic", response_model=TopicNotificationResponse)
async def send_topic_notification(
    request: TopicNotificationRequest,
    fcm_client: FCMClient = Depends(),
    valkey_client: ValkeyClient = Depends(),
    http_request: Request = None
):
    """Send notification to a topic."""
    start_time = time.time()
    notification_id = str(uuid.uuid4())
    
    try:
        # Convert request to domain objects
        topic = Topic(name=request.topic)
        notification_type = NotificationType(
            value=request.notification_type,
            priority=request.priority
        )
        
        # Create notification using domain service
        domain_service = NotificationDomainService()
        notification = domain_service.create_notification(
            notification_type=notification_type,
            topic=topic,
            title=request.title,
            body=request.body,
            data=request.data,
            priority=request.priority,
            collapse_key=request.collapse_key,
            ttl=request.ttl,
            scheduled_at=request.scheduled_at
        )
        
        # Send notification via FCM
        result = await fcm_client.send_to_topic(
            topic=topic.name,
            title=notification.title,
            body=notification.body,
            data=notification.data,
            priority=notification.priority
        )
        
        if result["success"]:
            notification.mark_sent()
            message_id = result["message_id"]
            status = "success"
        else:
            notification.mark_failed(result["error"])
            message_id = None
            status = "failed"
        
        # Store notification status in Valkey
        notification_status = {
            "notification_id": notification_id,
            "topic": topic.name,
            "type": notification.notification_type.value,
            "status": status,
            "message_id": message_id,
            "created_at": notification.created_at.isoformat(),
            "error_message": result.get("error")
        }
        
        await valkey_client.set(f"notification:{notification_id}", notification_status, ex=3600)  # Expire in 1 hour
        
        # Publish event to Valkey
        await valkey_client.publish(
            channel="notification.topic.sent",
            message=notification_status
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return TopicNotificationResponse(
            success=status == "success",
            notification_id=notification_id,
            topic=topic.name,
            message_id=message_id,
            processing_time_ms=processing_time,
            message=f"Topic notification sent successfully to {topic.name}"
        )
        
    except Exception as e:
        logger.error(
            "Failed to send topic notification",
            notification_id=notification_id,
            error=str(e),
            request_id=getattr(http_request.state, 'request_id', None)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=BatchNotificationResponse)
async def send_batch_notifications(
    request: BatchNotificationRequest,
    fcm_client: FCMClient = Depends(),
    valkey_client: ValkeyClient = Depends(),
    http_request: Request = None
):
    """Send batch notifications."""
    start_time = time.time()
    batch_id = str(uuid.uuid4())
    
    try:
        results = []
        successful_count = 0
        failed_count = 0
        
        for notification_request in request.notifications:
            try:
                # Convert request to domain objects
                device_tokens = DeviceTokenList(
                    tokens=[
                        DeviceToken(value=token.token, platform=token.platform)
                        for token in notification_request.device_tokens
                    ],
                    max_tokens=settings.max_tokens_per_request
                )
                
                notification_type = NotificationType(
                    value=notification_request.notification_type,
                    priority=notification_request.priority
                )
                
                # Create notification using domain service
                domain_service = NotificationDomainService()
                notification = domain_service.create_notification(
                    notification_type=notification_type,
                    device_tokens=device_tokens,
                    title=notification_request.title,
                    body=notification_request.body,
                    data=notification_request.data,
                    priority=notification_request.priority,
                    collapse_key=notification_request.collapse_key,
                    ttl=notification_request.ttl,
                    scheduled_at=notification_request.scheduled_at
                )
                
                # Send notification
                device_token_values = [token.value for token in device_tokens.tokens]
                
                if len(device_token_values) == 1:
                    result = await fcm_client.send_to_device(
                        device_token=device_token_values[0],
                        title=notification.title,
                        body=notification.body,
                        data=notification.data,
                        priority=notification.priority,
                        collapse_key=notification.collapse_key,
                        ttl=notification.ttl
                    )
                    
                    if result["success"]:
                        sent_count = 1
                        failed_count = 0
                        status = "success"
                        successful_count += 1
                    else:
                        sent_count = 0
                        failed_count = 1
                        status = "failed"
                        failed_count += 1
                else:
                    result = await fcm_client.send_to_multiple_devices(
                        device_tokens=device_token_values,
                        title=notification.title,
                        body=notification.body,
                        data=notification.data,
                        priority=notification.priority,
                        collapse_key=notification.collapse_key,
                        ttl=notification.ttl
                    )
                    
                    if result["success"]:
                        sent_count = result["success_count"]
                        failed_count = result["failure_count"]
                        status = "partial" if failed_count > 0 else "success"
                        successful_count += 1
                    else:
                        sent_count = 0
                        failed_count = len(device_token_values)
                        status = "failed"
                        failed_count += 1
                
                # Store notification status in Valkey
                notification_status = {
                    "notification_id": notification.id,
                    "type": notification.notification_type.value,
                    "target_count": len(device_token_values),
                    "sent_count": sent_count,
                    "failed_count": failed_count,
                    "status": status,
                    "created_at": notification.created_at.isoformat(),
                    "error_message": result.get("error"),
                    "message_id": result.get("message_id"),
                    "batch_id": batch_id
                }
                
                await valkey_client.set(f"notification:{notification.id}", notification_status, ex=3600)  # Expire in 1 hour
                
                notification_result = SendNotificationResponse(
                    success=status != "failed",
                    notification_id=str(uuid.uuid4()),
                    results=[NotificationResult(
                        notification_id=notification.id,
                        status=status,
                        sent_count=sent_count,
                        failed_count=failed_count,
                        error_message=result.get("error"),
                        target_count=len(device_token_values)
                    )],
                    total_sent=sent_count,
                    total_failed=failed_count,
                    total_targets=len(device_token_values),
                    processing_time_ms=0,  # Individual processing time not tracked
                    message=f"Batch notification {status}"
                )
                
                results.append(notification_result)
                
            except Exception as e:
                logger.error(f"Failed to process batch notification: {e}")
                failed_count += 1
                
                # Add failed result
                results.append(SendNotificationResponse(
                    success=False,
                    notification_id=str(uuid.uuid4()),
                    results=[],
                    total_sent=0,
                    total_failed=1,
                    total_targets=0,
                    processing_time_ms=0,
                    message=f"Failed to process notification: {str(e)}"
                ))
        
        # Publish batch event to Valkey
        await valkey_client.publish(
            channel="notification.batch.sent",
            message={
                "batch_id": batch_id,
                "total_notifications": len(request.notifications),
                "successful_count": successful_count,
                "failed_count": failed_count
            }
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return BatchNotificationResponse(
            success=failed_count == 0,
            batch_id=batch_id,
            total_notifications=len(request.notifications),
            successful_notifications=successful_count,
            failed_notifications=failed_count,
            results=results,
            processing_time_ms=processing_time,
            message=f"Batch processing completed: {successful_count} successful, {failed_count} failed"
        )
        
    except Exception as e:
        logger.error(
            "Failed to send batch notifications",
            batch_id=batch_id,
            error=str(e),
            request_id=getattr(http_request.state, 'request_id', None)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/topics/subscribe", response_model=TopicSubscriptionResponse)
async def subscribe_to_topic(
    request: TopicSubscriptionRequest,
    fcm_client: FCMClient = Depends(),
    valkey_client: ValkeyClient = Depends(),
    http_request: Request = None
):
    """Subscribe device tokens to a topic."""
    start_time = time.time()
    
    try:
        # Subscribe via FCM
        result = await fcm_client.subscribe_to_topic(
            topic=request.topic,
            device_tokens=request.device_tokens
        )
        
        if result["success"]:
            subscribed_count = result["success_count"]
            failed_count = result["failure_count"]
            failed_tokens = []
            
            # Extract failed tokens from errors
            if result.get("errors"):
                for error in result["errors"]:
                    if hasattr(error, 'index') and error.index < len(request.device_tokens):
                        failed_tokens.append(request.device_tokens[error.index])
            
            # Publish event to Valkey
            await valkey_client.publish(
                channel="topic.subscription",
                message={
                    "topic": request.topic,
                    "subscribed_count": subscribed_count,
                    "failed_count": failed_count,
                    "failed_tokens": failed_tokens
                }
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            return TopicSubscriptionResponse(
                success=True,
                topic=request.topic,
                subscribed_count=subscribed_count,
                failed_count=failed_count,
                failed_tokens=failed_tokens,
                processing_time_ms=processing_time,
                message=f"Successfully subscribed {subscribed_count} tokens to topic {request.topic}"
            )
        else:
            processing_time = (time.time() - start_time) * 1000
            
            return TopicSubscriptionResponse(
                success=False,
                topic=request.topic,
                subscribed_count=0,
                failed_count=len(request.device_tokens),
                failed_tokens=request.device_tokens,
                processing_time_ms=processing_time,
                message=f"Failed to subscribe tokens to topic {request.topic}: {result.get('error', 'Unknown error')}"
            )
        
    except Exception as e:
        logger.error(
            "Failed to subscribe to topic",
            topic=request.topic,
            error=str(e),
            request_id=getattr(http_request.state, 'request_id', None)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{notification_id}")
async def get_notification_status(
    notification_id: str,
    valkey_client: ValkeyClient = Depends(),
    http_request: Request = None
):
    """Get notification status from Valkey."""
    try:
        # Try to get status from Valkey
        status_data = await valkey_client.get(f"notification:{notification_id}")
        
        if status_data:
            return status_data
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
        
    except Exception as e:
        logger.error(
            "Failed to get notification status",
            notification_id=notification_id,
            error=str(e),
            request_id=getattr(http_request.state, 'request_id', None)
        )
        raise HTTPException(status_code=500, detail=str(e)) 
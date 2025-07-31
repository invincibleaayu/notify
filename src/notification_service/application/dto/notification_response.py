"""Notification response DTOs for API output formatting."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class NotificationResult(BaseModel):
    """Result of a single notification send operation."""
    
    notification_id: str = Field(..., description="Unique notification ID")
    status: str = Field(..., description="Send status (success, failed, partial)")
    sent_count: int = Field(0, description="Number of successful sends")
    failed_count: int = Field(0, description="Number of failed sends")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    target_count: int = Field(0, description="Total number of targets")
    delivery_time: Optional[datetime] = Field(None, description="Estimated delivery time")


class SendNotificationResponse(BaseModel):
    """Response model for sending notifications."""
    
    success: bool = Field(..., description="Overall success status")
    notification_id: str = Field(..., description="Unique notification ID")
    results: List[NotificationResult] = Field(..., description="Results for each target")
    total_sent: int = Field(0, description="Total successful sends")
    total_failed: int = Field(0, description="Total failed sends")
    total_targets: int = Field(0, description="Total number of targets")
    processing_time_ms: float = Field(0, description="Processing time in milliseconds")
    message: str = Field(..., description="Response message")


class TopicNotificationResponse(BaseModel):
    """Response model for topic notifications."""
    
    success: bool = Field(..., description="Overall success status")
    notification_id: str = Field(..., description="Unique notification ID")
    topic: str = Field(..., description="Target topic")
    message_id: Optional[str] = Field(None, description="FCM message ID")
    processing_time_ms: float = Field(0, description="Processing time in milliseconds")
    message: str = Field(..., description="Response message")


class BatchNotificationResponse(BaseModel):
    """Response model for batch notifications."""
    
    success: bool = Field(..., description="Overall success status")
    batch_id: str = Field(..., description="Unique batch ID")
    total_notifications: int = Field(0, description="Total notifications in batch")
    successful_notifications: int = Field(0, description="Successful notifications")
    failed_notifications: int = Field(0, description="Failed notifications")
    results: List[SendNotificationResponse] = Field(..., description="Results for each notification")
    processing_time_ms: float = Field(0, description="Total processing time in milliseconds")
    message: str = Field(..., description="Response message")


class TopicSubscriptionResponse(BaseModel):
    """Response model for topic subscription."""
    
    success: bool = Field(..., description="Overall success status")
    topic: str = Field(..., description="Topic name")
    subscribed_count: int = Field(0, description="Number of successfully subscribed tokens")
    failed_count: int = Field(0, description="Number of failed subscriptions")
    failed_tokens: List[str] = Field(default_factory=list, description="List of failed tokens")
    processing_time_ms: float = Field(0, description="Processing time in milliseconds")
    message: str = Field(..., description="Response message")


class NotificationStatusResponse(BaseModel):
    """Response model for notification status check."""
    
    notification_id: str = Field(..., description="Notification ID")
    status: str = Field(..., description="Current status")
    created_at: datetime = Field(..., description="Creation timestamp")
    sent_count: int = Field(0, description="Number of successful sends")
    failed_count: int = Field(0, description="Number of failed sends")
    total_targets: int = Field(0, description="Total number of targets")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    delivery_time: Optional[datetime] = Field(None, description="Estimated delivery time")


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Service version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    checks: Dict[str, str] = Field(..., description="Component health checks")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking") 
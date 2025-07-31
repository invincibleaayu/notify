"""Notification request DTOs for API input validation."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, validator


class DeviceTokenRequest(BaseModel):
    """Device token request model."""
    
    token: str = Field(..., description="Device token value")
    platform: str = Field(..., description="Platform (android, ios, web)")
    
    @validator("platform")
    def validate_platform(cls, v: str) -> str:
        """Validate platform value."""
        valid_platforms = ["android", "ios", "web"]
        if v.lower() not in valid_platforms:
            raise ValueError(f"Platform must be one of: {valid_platforms}")
        return v.lower()


class SendNotificationRequest(BaseModel):
    """Request model for sending notifications to device tokens."""
    
    device_tokens: List[DeviceTokenRequest] = Field(..., description="Target device tokens")
    notification_type: str = Field(..., description="Type of notification")
    title: Optional[str] = Field(None, description="Notification title")
    body: Optional[str] = Field(None, description="Notification body")
    data: Dict[str, Any] = Field(default_factory=dict, description="Custom data payload")
    priority: str = Field("normal", description="Notification priority")
    collapse_key: Optional[str] = Field(None, description="FCM collapse key")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")
    scheduled_at: Optional[datetime] = Field(datetime.now(timezone.utc), description="Scheduled delivery time")  # noqa: F821
    
    @validator("device_tokens")
    def validate_device_tokens(cls, v: List[DeviceTokenRequest]) -> List[DeviceTokenRequest]:
        """Validate device tokens list."""
        if not v:
            raise ValueError("At least one device token is required")
        
        if len(v) > 500:
            raise ValueError("Maximum 500 device tokens allowed per request")
        
        # Check for duplicates
        token_values = [token.token for token in v]
        if len(token_values) != len(set(token_values)):
            raise ValueError("Duplicate device tokens are not allowed")
        
        return v
    
    @validator("notification_type")
    def validate_notification_type(cls, v: str) -> str:
        """Validate notification type."""
        if not v or not v.strip():
            raise ValueError("Notification type cannot be empty")
        return v.lower()
    
    @validator("priority")
    def validate_priority(cls, v: str) -> str:
        """Validate priority value."""
        valid_priorities = ["high", "normal", "low"]
        if v.lower() not in valid_priorities:
            raise ValueError(f"Priority must be one of: {valid_priorities}")
        return v.lower()
    
    @validator("ttl")
    def validate_ttl(cls, v: Optional[int]) -> Optional[int]:
        """Validate TTL value."""
        if v is not None and (v < 0 or v > 2419200):  # 28 days in seconds
            raise ValueError("TTL must be between 0 and 2419200 seconds (28 days)")
        return v


class TopicNotificationRequest(BaseModel):
    """Request model for sending notifications to topics."""
    
    topic: str = Field(..., description="Target topic name")
    notification_type: str = Field(..., description="Type of notification")
    title: Optional[str] = Field(None, description="Notification title")
    body: Optional[str] = Field(None, description="Notification body")
    data: Dict[str, Any] = Field(default_factory=dict, description="Custom data payload")
    priority: str = Field("normal", description="Notification priority")
    collapse_key: Optional[str] = Field(None, description="FCM collapse key")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")
    scheduled_at: Optional[datetime] = Field(datetime.now(timezone.utc), description="Scheduled delivery time")  # noqa: F821
    
    @validator("topic")
    def validate_topic(cls, v: str) -> str:
        """Validate topic name."""
        if not v or not v.strip():
            raise ValueError("Topic name cannot be empty")
        
        # FCM topic name restrictions
        import re
        pattern = r"^[a-zA-Z0-9\-_\.~%]+$"
        if not re.match(pattern, v.strip()):
            raise ValueError(
                "Topic name must contain only letters, numbers, and "
                "characters: -_.~%"
            )
        
        if len(v.strip()) > 250:
            raise ValueError("Topic name cannot exceed 250 characters")
        
        return v.strip()
    
    @validator("notification_type")
    def validate_notification_type(cls, v: str) -> str:
        """Validate notification type."""
        if not v or not v.strip():
            raise ValueError("Notification type cannot be empty")
        return v.lower()
    
    @validator("priority")
    def validate_priority(cls, v: str) -> str:
        """Validate priority value."""
        valid_priorities = ["high", "normal", "low"]
        if v.lower() not in valid_priorities:
            raise ValueError(f"Priority must be one of: {valid_priorities}")
        return v.lower()
    
    @validator("ttl")
    def validate_ttl(cls, v: Optional[int]) -> Optional[int]:
        """Validate TTL value."""
        if v is not None and (v < 0 or v > 2419200):  # 28 days in seconds
            raise ValueError("TTL must be between 0 and 2419200 seconds (28 days)")
        return v


class BatchNotificationRequest(BaseModel):
    """Request model for sending batch notifications."""
    
    notifications: List[SendNotificationRequest] = Field(..., description="List of notifications")
    
    @validator("notifications")
    def validate_notifications(cls, v: List[SendNotificationRequest]) -> List[SendNotificationRequest]:
        """Validate notifications list."""
        if not v:
            raise ValueError("At least one notification is required")
        
        if len(v) > 100:
            raise ValueError("Maximum 100 notifications allowed per batch")
        
        return v


class TopicSubscriptionRequest(BaseModel):
    """Request model for topic subscription."""
    
    topic: str = Field(..., description="Topic name")
    device_tokens: List[str] = Field(..., description="Device tokens to subscribe")
    
    @validator("topic")
    def validate_topic(cls, v: str) -> str:
        """Validate topic name."""
        if not v or not v.strip():
            raise ValueError("Topic name cannot be empty")
        
        import re
        pattern = r"^[a-zA-Z0-9\-_\.~%]+$"
        if not re.match(pattern, v.strip()):
            raise ValueError(
                "Topic name must contain only letters, numbers, and "
                "characters: -_.~%"
            )
        
        return v.strip()
    
    @validator("device_tokens")
    def validate_device_tokens(cls, v: List[str]) -> List[str]:
        """Validate device tokens list."""
        if not v:
            raise ValueError("At least one device token is required")
        
        if len(v) > 1000:
            raise ValueError("Maximum 1000 device tokens per topic subscription")
        
        # Remove duplicates
        unique_tokens = list(set(v))
        if len(unique_tokens) != len(v):
            raise ValueError("Duplicate device tokens are not allowed")
        
        return unique_tokens 
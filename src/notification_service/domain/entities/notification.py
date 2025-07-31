"""Notification entity representing a notification message."""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from ..value_objects.notification_type import NotificationType
from ..value_objects.device_token import DeviceToken, DeviceTokenList
from ..value_objects.topic import Topic


class Notification(BaseModel):
    """Notification entity representing a complete notification message."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique notification ID")
    notification_type: NotificationType = Field(..., description="Type of notification")
    title: Optional[str] = Field(None, description="Notification title")
    body: Optional[str] = Field(None, description="Notification body")
    data: Dict[str, Any] = Field(default_factory=dict, description="Custom data payload")
    
    # Targeting
    device_tokens: Optional[DeviceTokenList] = Field(None, description="Target device tokens")
    topic: Optional[Topic] = Field(None, description="Target topic")
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled delivery time")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")
    
    # FCM specific
    priority: str = Field("normal", description="Notification priority")
    collapse_key: Optional[str] = Field(None, description="FCM collapse key")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")
    
    # Status tracking
    status: str = Field("pending", description="Notification status")
    sent_count: int = Field(0, description="Number of successful sends")
    failed_count: int = Field(0, description="Number of failed sends")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    @classmethod
    def create_device_notification(
        cls,
        notification_type: NotificationType,
        device_tokens: DeviceTokenList,
        title: Optional[str] = None,
        body: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        **kwargs
    ) -> "Notification":
        """Create a notification targeting specific device tokens."""
        return cls(
            notification_type=notification_type,
            device_tokens=device_tokens,
            title=title,
            body=body,
            data=data or {},
            priority=priority,
            **kwargs
        )
    
    @classmethod
    def create_topic_notification(
        cls,
        notification_type: NotificationType,
        topic: Topic,
        title: Optional[str] = None,
        body: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        **kwargs
    ) -> "Notification":
        """Create a notification targeting a topic."""
        return cls(
            notification_type=notification_type,
            topic=topic,
            title=title,
            body=body,
            data=data or {},
            priority=priority,
            **kwargs
        )
    
    def validate(self) -> List[str]:
        """Validate the notification and return list of errors."""
        errors = []
        
        # Check targeting
        if not self.device_tokens and not self.topic:
            errors.append("Notification must target either device tokens or a topic")
        
        if self.device_tokens and self.topic:
            errors.append("Notification cannot target both device tokens and topic")
        
        # Validate notification type requirements
        template_config = self.notification_type.get_template_config()
        
        if template_config.get("requires_title") and not self.title:
            errors.append(f"Notification type '{self.notification_type.value}' requires a title")
        
        if template_config.get("requires_body") and not self.body:
            errors.append(f"Notification type '{self.notification_type.value}' requires a body")
        
        if not template_config.get("supports_data") and self.data:
            errors.append(f"Notification type '{self.notification_type.value}' does not support custom data")
        
        # Validate timing
        current_time = datetime.now(timezone.utc)
        # Allow a small buffer (5 minutes) for network delays and processing time
        buffer_time = current_time.replace(second=0, microsecond=0) - timedelta(minutes=5)
        
        if self.scheduled_at and self.scheduled_at < buffer_time:
            errors.append("Scheduled time cannot be in the past (with 5-minute buffer)")
        
        if self.expires_at and self.expires_at < current_time:
            errors.append("Expiration time cannot be in the past")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if the notification is valid."""
        return len(self.validate()) == 0
    
    def get_target_count(self) -> int:
        """Get the number of targets for this notification."""
        if self.device_tokens:
            return len(self.device_tokens.tokens)
        elif self.topic:
            return 1  # Topic represents unlimited devices
        return 0
    
    def mark_sent(self, count: int = 1) -> None:
        """Mark notification as sent."""
        self.sent_count += count
        if self.status == "pending":
            self.status = "sent"
    
    def mark_failed(self, error_message: str, count: int = 1) -> None:
        """Mark notification as failed."""
        self.failed_count += count
        self.error_message = error_message
        self.status = "failed"
    
    def to_fcm_message(self) -> Dict[str, Any]:
        """Convert to FCM message format."""
        message = {
            "message": {
                "notification": {},
                "data": self.data,
                "android": {},
                "apns": {},
                "webpush": {}
            }
        }
        
        # Add notification content
        if self.title:
            message["message"]["notification"]["title"] = self.title
        if self.body:
            message["message"]["notification"]["body"] = self.body
        
        # Add targeting
        if self.device_tokens:
            message["message"]["token"] = self.device_tokens.tokens[0].value
            if len(self.device_tokens.tokens) > 1:
                # For multiple tokens, we'll need to send multiple messages
                pass
        elif self.topic:
            message["message"]["topic"] = self.topic.name
        
        # Add FCM options
        if self.priority:
            message["message"]["android"]["priority"] = self.priority
            message["message"]["apns"]["headers"]["apns-priority"] = "10" if self.priority == "high" else "5"
        
        if self.collapse_key:
            message["message"]["android"]["collapse_key"] = self.collapse_key
        
        if self.ttl:
            message["message"]["android"]["ttl"] = f"{self.ttl}s"
        
        return message
    
    class Config:
        frozen = False  # Allow status updates 
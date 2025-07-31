"""Notification type value object."""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, validator


class NotificationTypeEnum(str, Enum):
    """Predefined notification types."""
    
    ALERT = "alert"
    SILENT = "silent"
    CUSTOM = "custom"
    PROMOTIONAL = "promotional"
    TRANSACTIONAL = "transactional"


class NotificationType(BaseModel):
    """Value object representing a notification type."""
    
    value: str = Field(..., description="The notification type value")
    template_id: Optional[str] = Field(None, description="Template ID for this type")
    priority: str = Field("normal", description="Notification priority")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")
    
    @validator("value")
    def validate_notification_type(cls, v: str) -> str:
        """Validate notification type value."""
        if not v or not v.strip():
            raise ValueError("Notification type cannot be empty")
        
        # Check if it's a predefined type
        try:
            NotificationTypeEnum(v.lower())
        except ValueError:
            # Custom type - validate format
            if not v.replace("_", "").replace("-", "").isalnum():
                raise ValueError("Custom notification type must be alphanumeric")
        
        return v.lower()
    
    @validator("priority")
    def validate_priority(cls, v: str) -> str:
        """Validate priority value."""
        valid_priorities = ["high", "normal", "low"]
        if v.lower() not in valid_priorities:
            raise ValueError(f"Priority must be one of: {valid_priorities}")
        return v.lower()
    
    def is_predefined(self) -> bool:
        """Check if this is a predefined notification type."""
        try:
            NotificationTypeEnum(self.value)
            return True
        except ValueError:
            return False
    
    def get_template_config(self) -> Dict[str, Any]:
        """Get template configuration for this notification type."""
        if self.value == NotificationTypeEnum.ALERT:
            return {
                "requires_title": True,
                "requires_body": True,
                "supports_data": True,
                "default_priority": "high"
            }
        elif self.value == NotificationTypeEnum.SILENT:
            return {
                "requires_title": False,
                "requires_body": False,
                "supports_data": True,
                "default_priority": "normal"
            }
        elif self.value == NotificationTypeEnum.CUSTOM:
            return {
                "requires_title": False,
                "requires_body": False,
                "supports_data": True,
                "default_priority": "normal"
            }
        else:
            return {
                "requires_title": True,
                "requires_body": True,
                "supports_data": True,
                "default_priority": "normal"
            }
    
    class Config:
        frozen = True 
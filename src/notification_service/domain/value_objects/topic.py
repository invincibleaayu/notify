"""Topic value object for FCM topic-based messaging."""

import re
from typing import Optional
from pydantic import BaseModel, Field, validator


class Topic(BaseModel):
    """Value object representing an FCM topic."""
    
    name: str = Field(..., description="Topic name")
    description: Optional[str] = Field(None, description="Topic description")
    
    @validator("name")
    def validate_topic_name(cls, v: str) -> str:
        """Validate topic name format."""
        if not v or not v.strip():
            raise ValueError("Topic name cannot be empty")
        
        # FCM topic name restrictions
        # Must match pattern: [a-zA-Z0-9-_.~%]+
        pattern = r"^[a-zA-Z0-9\-_\.~%]+$"
        if not re.match(pattern, v.strip()):
            raise ValueError(
                "Topic name must contain only letters, numbers, and "
                "characters: -_.~%"
            )
        
        # Length restrictions
        if len(v.strip()) > 250:
            raise ValueError("Topic name cannot exceed 250 characters")
        
        return v.strip()
    
    def __str__(self) -> str:
        """String representation."""
        return self.name
    
    def __hash__(self) -> int:
        """Hash based on name."""
        return hash(self.name)
    
    def __eq__(self, other: object) -> bool:
        """Equality based on name."""
        if not isinstance(other, Topic):
            return False
        return self.name == other.name
    
    class Config:
        frozen = True


class TopicSubscription(BaseModel):
    """Topic subscription information."""
    
    topic: Topic = Field(..., description="The topic to subscribe to")
    device_tokens: list[str] = Field(..., description="Device tokens to subscribe")
    
    @validator("device_tokens")
    def validate_device_tokens(cls, v: list[str]) -> list[str]:
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
    
    class Config:
        frozen = True 
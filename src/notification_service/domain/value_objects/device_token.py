"""Device token value object."""

import re
from typing import List
from pydantic import BaseModel, Field, validator


class DeviceToken(BaseModel):
    """Value object representing a device token."""
    
    value: str = Field(..., description="The device token value")
    platform: str = Field(..., description="Platform (android, ios, web)")
    
    @validator("value")
    def validate_token(cls, v: str) -> str:
        """Validate device token format."""
        if not v or not v.strip():
            raise ValueError("Device token cannot be empty")
        
        # Basic validation - tokens should be reasonably long
        if len(v.strip()) < 32:
            raise ValueError("Device token appears to be too short")
        
        return v.strip()
    
    @validator("platform")
    def validate_platform(cls, v: str) -> str:
        """Validate platform value."""
        valid_platforms = ["android", "ios", "web"]
        if v.lower() not in valid_platforms:
            raise ValueError(f"Platform must be one of: {valid_platforms}")
        return v.lower()
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __hash__(self) -> int:
        """Hash based on value."""
        return hash(self.value)
    
    def __eq__(self, other: object) -> bool:
        """Equality based on value."""
        if not isinstance(other, DeviceToken):
            return False
        return self.value == other.value
    
    class Config:
        frozen = True


class DeviceTokenList(BaseModel):
    """Collection of device tokens with validation."""
    
    tokens: List[DeviceToken] = Field(..., description="List of device tokens")
    max_tokens: int = Field(500, description="Maximum number of tokens allowed")
    
    @validator("tokens")
    def validate_tokens(cls, v: List[DeviceToken], values: dict) -> List[DeviceToken]:
        """Validate token list."""
        if not v:
            raise ValueError("At least one device token is required")
        
        # Get max_tokens from the instance, fallback to class default
        max_tokens = values.get("max_tokens", 500)
        
        if len(v) > max_tokens:
            raise ValueError(f"Maximum {max_tokens} tokens allowed per request")
        
        # Check for duplicates
        token_values = [token.value for token in v]
        if len(token_values) != len(set(token_values)):
            raise ValueError("Duplicate device tokens are not allowed")
        
        return v
    
    def get_platforms(self) -> List[str]:
        """Get unique platforms from token list."""
        return list(set(token.platform for token in self.tokens))
    
    def group_by_platform(self) -> dict:
        """Group tokens by platform."""
        grouped = {}
        for token in self.tokens:
            if token.platform not in grouped:
                grouped[token.platform] = []
            grouped[token.platform].append(token.value)
        return grouped
    
    class Config:
        frozen = True 
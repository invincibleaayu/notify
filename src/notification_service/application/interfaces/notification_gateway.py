"""Notification gateway interface for FCM integration."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ...domain.entities.notification import Notification


class NotificationGateway(ABC):
    """Abstract interface for notification gateway (FCM)."""
    
    @abstractmethod
    async def send_to_device(
        self,
        notification: Notification,
        device_token: str
    ) -> Dict[str, Any]:
        """Send notification to a single device token."""
        pass
    
    @abstractmethod
    async def send_to_multiple_devices(
        self,
        notification: Notification,
        device_tokens: List[str]
    ) -> Dict[str, Any]:
        """Send notification to multiple device tokens."""
        pass
    
    @abstractmethod
    async def send_to_topic(
        self,
        notification: Notification,
        topic: str
    ) -> Dict[str, Any]:
        """Send notification to a topic."""
        pass
    
    @abstractmethod
    async def subscribe_to_topic(
        self,
        topic: str,
        device_tokens: List[str]
    ) -> Dict[str, Any]:
        """Subscribe device tokens to a topic."""
        pass
    
    @abstractmethod
    async def unsubscribe_from_topic(
        self,
        topic: str,
        device_tokens: List[str]
    ) -> Dict[str, Any]:
        """Unsubscribe device tokens from a topic."""
        pass
    
    @abstractmethod
    async def validate_device_token(
        self,
        device_token: str
    ) -> bool:
        """Validate if a device token is still valid."""
        pass
    
    @abstractmethod
    async def get_delivery_status(
        self,
        message_id: str
    ) -> Dict[str, Any]:
        """Get delivery status for a message."""
        pass 
"""Event publisher interface for Valkey integration."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ...domain.entities.notification import Notification


class EventPublisher(ABC):
    """Abstract interface for event publishing (Valkey)."""
    
    @abstractmethod
    async def publish_notification_event(
        self,
        notification: Notification,
        event_type: str = "notification.sent"
    ) -> bool:
        """Publish a notification event."""
        pass
    
    @abstractmethod
    async def publish_batch_event(
        self,
        batch_id: str,
        notifications: list[Notification],
        event_type: str = "notification.batch.sent"
    ) -> bool:
        """Publish a batch notification event."""
        pass
    
    @abstractmethod
    async def publish_delivery_status_event(
        self,
        notification_id: str,
        status: str,
        details: Dict[str, Any],
        event_type: str = "notification.delivery_status"
    ) -> bool:
        """Publish a delivery status event."""
        pass
    
    @abstractmethod
    async def publish_error_event(
        self,
        notification_id: str,
        error_message: str,
        error_details: Dict[str, Any],
        event_type: str = "notification.error"
    ) -> bool:
        """Publish an error event."""
        pass
    
    @abstractmethod
    async def publish_metrics_event(
        self,
        metrics: Dict[str, Any],
        event_type: str = "notification.metrics"
    ) -> bool:
        """Publish metrics event."""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if the event publisher is connected."""
        pass
    
    @abstractmethod
    async def get_queue_size(self, queue_name: str) -> int:
        """Get the size of a queue."""
        pass 
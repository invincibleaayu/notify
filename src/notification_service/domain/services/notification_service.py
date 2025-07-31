"""Domain service for notification business logic."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from ..entities.notification import Notification
from ..value_objects.notification_type import NotificationType
from ..value_objects.device_token import DeviceTokenList
from ..value_objects.topic import Topic


class NotificationDomainService:
    """Domain service for notification business logic."""
    
    def __init__(self):
        """Initialize the domain service."""
        pass
    
    def create_notification(
        self,
        notification_type: NotificationType,
        title: Optional[str] = None,
        body: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        device_tokens: Optional[DeviceTokenList] = None,
        topic: Optional[Topic] = None,
        priority: str = "normal",
        **kwargs
    ) -> Notification:
        """Create a notification with proper validation."""
        
        # Validate targeting
        if not device_tokens and not topic:
            raise ValueError("Must specify either device tokens or topic")
        
        if device_tokens and topic:
            raise ValueError("Cannot specify both device tokens and topic")
        
        # Create notification based on targeting
        if device_tokens:
            notification = Notification.create_device_notification(
                notification_type=notification_type,
                device_tokens=device_tokens,
                title=title,
                body=body,
                data=data or {},
                priority=priority,
                **kwargs
            )
        else:
            notification = Notification.create_topic_notification(
                notification_type=notification_type,
                topic=topic,
                title=title,
                body=body,
                data=data or {},
                priority=priority,
                **kwargs
            )
        
        # Validate the notification
        validation_errors = notification.validate()
        if validation_errors:
            raise ValueError(f"Invalid notification: {'; '.join(validation_errors)}")
        
        return notification
    
    def validate_notification_type_requirements(
        self,
        notification_type: NotificationType,
        title: Optional[str] = None,
        body: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Validate notification content against type requirements."""
        errors = []
        template_config = notification_type.get_template_config()
        
        if template_config.get("requires_title") and not title:
            errors.append(f"Notification type '{notification_type.value}' requires a title")
        
        if template_config.get("requires_body") and not body:
            errors.append(f"Notification type '{notification_type.value}' requires a body")
        
        if not template_config.get("supports_data") and data:
            errors.append(f"Notification type '{notification_type.value}' does not support custom data")
        
        return errors
    
    def process_notification_batch(
        self,
        notifications: List[Notification]
    ) -> Dict[str, Any]:
        """Process a batch of notifications and return summary."""
        total_count = len(notifications)
        valid_count = sum(1 for n in notifications if n.is_valid())
        invalid_count = total_count - valid_count
        
        # Group by type
        type_groups = {}
        for notification in notifications:
            notification_type = notification.notification_type.value
            if notification_type not in type_groups:
                type_groups[notification_type] = []
            type_groups[notification_type].append(notification)
        
        # Group by targeting method
        device_notifications = [n for n in notifications if n.device_tokens]
        topic_notifications = [n for n in notifications if n.topic]
        
        return {
            "total_count": total_count,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "type_groups": {k: len(v) for k, v in type_groups.items()},
            "device_notifications": len(device_notifications),
            "topic_notifications": len(topic_notifications),
            "total_targets": sum(n.get_target_count() for n in notifications)
        }
    
    def should_retry_notification(
        self,
        notification: Notification,
        max_retries: int = 3
    ) -> bool:
        """Determine if a failed notification should be retried."""
        if notification.status != "failed":
            return False
        
        # Check if we've exceeded max retries
        if notification.failed_count >= max_retries:
            return False
        
        # Check if notification has expired
        if notification.expires_at and notification.expires_at < datetime.now(timezone.utc):
            return False
        
        return True
    
    def get_notification_priority(
        self,
        notification_type: NotificationType,
        override_priority: Optional[str] = None
    ) -> str:
        """Get the appropriate priority for a notification type."""
        if override_priority:
            return override_priority
        
        template_config = notification_type.get_template_config()
        return template_config.get("default_priority", "normal")
    
    def estimate_delivery_time(
        self,
        notification: Notification,
        current_time: Optional[datetime] = None
    ) -> datetime:
        """Estimate when the notification will be delivered."""
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        if notification.scheduled_at:
            return notification.scheduled_at
        
        # Add some buffer for processing time
        return current_time.replace(microsecond=0)
    
    def calculate_notification_cost(
        self,
        notification: Notification
    ) -> Dict[str, Any]:
        """Calculate the cost/complexity of sending a notification."""
        base_cost = 1
        
        # Factor in target count
        target_count = notification.get_target_count()
        cost_multiplier = 1 + (target_count / 100)  # Scale with target count
        
        # Factor in priority
        if notification.priority == "high":
            cost_multiplier *= 1.5
        
        # Factor in notification type complexity
        if notification.notification_type.value == "custom":
            cost_multiplier *= 1.2
        
        # Factor in data payload size
        data_size = len(str(notification.data))
        if data_size > 1000:  # 1KB
            cost_multiplier *= 1.1
        
        return {
            "base_cost": base_cost,
            "cost_multiplier": cost_multiplier,
            "total_cost": base_cost * cost_multiplier,
            "target_count": target_count,
            "data_size": data_size,
            "priority_factor": 1.5 if notification.priority == "high" else 1.0
        } 
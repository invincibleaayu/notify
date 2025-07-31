"""Unit tests for the notification entity."""

import pytest
from datetime import datetime, timezone

from src.notification_service.domain.entities.notification import Notification
from src.notification_service.domain.value_objects.notification_type import NotificationType
from src.notification_service.domain.value_objects.device_token import DeviceToken, DeviceTokenList
from src.notification_service.domain.value_objects.topic import Topic


class TestNotificationEntity:
    """Test cases for the Notification entity."""
    
    def test_create_device_notification(self):
        """Test creating a notification targeting device tokens."""
        notification_type = NotificationType(value="alert", priority="high")
        device_tokens = DeviceTokenList(tokens=[
            DeviceToken(token="test_token_1", platform="android"),
            DeviceToken(token="test_token_2", platform="ios")
        ])
        
        notification = Notification.create_device_notification(
            notification_type=notification_type,
            device_tokens=device_tokens,
            title="Test Title",
            body="Test Body",
            data={"key": "value"}
        )
        
        assert notification.notification_type == notification_type
        assert notification.device_tokens == device_tokens
        assert notification.title == "Test Title"
        assert notification.body == "Test Body"
        assert notification.data == {"key": "value"}
        assert notification.topic is None
        assert notification.status == "pending"
    
    def test_create_topic_notification(self):
        """Test creating a notification targeting a topic."""
        notification_type = NotificationType(value="silent", priority="normal")
        topic = Topic(name="test_topic")
        
        notification = Notification.create_topic_notification(
            notification_type=notification_type,
            topic=topic,
            data={"key": "value"}
        )
        
        assert notification.notification_type == notification_type
        assert notification.topic == topic
        assert notification.device_tokens is None
        assert notification.data == {"key": "value"}
        assert notification.status == "pending"
    
    def test_validate_device_notification(self):
        """Test validation of device notification."""
        notification_type = NotificationType(value="alert", priority="high")
        device_tokens = DeviceTokenList(tokens=[
            DeviceToken(token="test_token", platform="android")
        ])
        
        notification = Notification.create_device_notification(
            notification_type=notification_type,
            device_tokens=device_tokens,
            title="Test Title",
            body="Test Body"
        )
        
        errors = notification.validate()
        assert len(errors) == 0
        assert notification.is_valid()
    
    def test_validate_topic_notification(self):
        """Test validation of topic notification."""
        notification_type = NotificationType(value="silent", priority="normal")
        topic = Topic(name="test_topic")
        
        notification = Notification.create_topic_notification(
            notification_type=notification_type,
            topic=topic,
            data={"key": "value"}
        )
        
        errors = notification.validate()
        assert len(errors) == 0
        assert notification.is_valid()
    
    def test_validate_invalid_notification_missing_targeting(self):
        """Test validation fails when no targeting is specified."""
        notification_type = NotificationType(value="alert", priority="high")
        
        notification = Notification(
            notification_type=notification_type,
            device_tokens=None,
            topic=None
        )
        
        errors = notification.validate()
        assert len(errors) > 0
        assert "must target either device tokens or a topic" in errors[0]
        assert not notification.is_valid()
    
    def test_validate_invalid_notification_both_targeting(self):
        """Test validation fails when both targeting methods are specified."""
        notification_type = NotificationType(value="alert", priority="high")
        device_tokens = DeviceTokenList(tokens=[
            DeviceToken(token="test_token", platform="android")
        ])
        topic = Topic(name="test_topic")
        
        notification = Notification(
            notification_type=notification_type,
            device_tokens=device_tokens,
            topic=topic
        )
        
        errors = notification.validate()
        assert len(errors) > 0
        assert "cannot target both device tokens and topic" in errors[0]
        assert not notification.is_valid()
    
    def test_validate_alert_type_requires_title_and_body(self):
        """Test that alert type requires title and body."""
        notification_type = NotificationType(value="alert", priority="high")
        device_tokens = DeviceTokenList(tokens=[
            DeviceToken(token="test_token", platform="android")
        ])
        
        # Missing title
        notification = Notification.create_device_notification(
            notification_type=notification_type,
            device_tokens=device_tokens,
            body="Test Body"
        )
        
        errors = notification.validate()
        assert len(errors) > 0
        assert "requires a title" in errors[0]
        
        # Missing body
        notification = Notification.create_device_notification(
            notification_type=notification_type,
            device_tokens=device_tokens,
            title="Test Title"
        )
        
        errors = notification.validate()
        assert len(errors) > 0
        assert "requires a body" in errors[0]
    
    def test_get_target_count(self):
        """Test getting target count."""
        # Device tokens
        device_tokens = DeviceTokenList(tokens=[
            DeviceToken(token="test_token_1", platform="android"),
            DeviceToken(token="test_token_2", platform="ios")
        ])
        
        notification = Notification.create_device_notification(
            notification_type=NotificationType(value="alert"),
            device_tokens=device_tokens
        )
        
        assert notification.get_target_count() == 2
        
        # Topic
        topic = Topic(name="test_topic")
        notification = Notification.create_topic_notification(
            notification_type=NotificationType(value="silent"),
            topic=topic
        )
        
        assert notification.get_target_count() == 1  # Topic represents unlimited devices
    
    def test_mark_sent(self):
        """Test marking notification as sent."""
        notification = Notification.create_device_notification(
            notification_type=NotificationType(value="alert"),
            device_tokens=DeviceTokenList(tokens=[
                DeviceToken(token="test_token", platform="android")
            ])
        )
        
        notification.mark_sent()
        assert notification.status == "sent"
        assert notification.sent_count == 1
        
        notification.mark_sent(5)
        assert notification.sent_count == 6
    
    def test_mark_failed(self):
        """Test marking notification as failed."""
        notification = Notification.create_device_notification(
            notification_type=NotificationType(value="alert"),
            device_tokens=DeviceTokenList(tokens=[
                DeviceToken(token="test_token", platform="android")
            ])
        )
        
        notification.mark_failed("Test error")
        assert notification.status == "failed"
        assert notification.failed_count == 1
        assert notification.error_message == "Test error"
        
        notification.mark_failed("Another error", 3)
        assert notification.failed_count == 4
        assert notification.error_message == "Another error"
    
    def test_to_fcm_message(self):
        """Test converting notification to FCM message format."""
        notification = Notification.create_device_notification(
            notification_type=NotificationType(value="alert", priority="high"),
            device_tokens=DeviceTokenList(tokens=[
                DeviceToken(token="test_token", platform="android")
            ]),
            title="Test Title",
            body="Test Body",
            data={"key": "value"},
            collapse_key="test_collapse",
            ttl=3600
        )
        
        fcm_message = notification.to_fcm_message()
        
        assert fcm_message["message"]["notification"]["title"] == "Test Title"
        assert fcm_message["message"]["notification"]["body"] == "Test Body"
        assert fcm_message["message"]["data"] == {"key": "value"}
        assert fcm_message["message"]["token"] == "test_token"
        assert fcm_message["message"]["android"]["priority"] == "high"
        assert fcm_message["message"]["android"]["collapse_key"] == "test_collapse"
        assert fcm_message["message"]["android"]["ttl"] == "3600s"
        assert fcm_message["message"]["apns"]["headers"]["apns-priority"] == "10" 
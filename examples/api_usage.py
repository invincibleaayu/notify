#!/usr/bin/env python3
"""
Example usage of the Notification Service API.

This script demonstrates how to interact with the notification service
using the REST API endpoints.
"""

import asyncio
import json
import httpx
from typing import Dict, Any


class NotificationServiceClient:
    """Client for interacting with the notification service API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def send_notification(
        self,
        device_tokens: list[Dict[str, str]],
        notification_type: str,
        title: str = None,
        body: str = None,
        data: Dict[str, Any] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Send notification to device tokens."""
        payload = {
            "device_tokens": device_tokens,
            "notification_type": notification_type,
            "title": title,
            "body": body,
            "data": data or {},
            "priority": priority
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/notifications/send",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def send_topic_notification(
        self,
        topic: str,
        notification_type: str,
        title: str = None,
        body: str = None,
        data: Dict[str, Any] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Send notification to a topic."""
        payload = {
            "topic": topic,
            "notification_type": notification_type,
            "title": title,
            "body": body,
            "data": data or {},
            "priority": priority
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/notifications/topic",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def subscribe_to_topic(
        self,
        topic: str,
        device_tokens: list[str]
    ) -> Dict[str, Any]:
        """Subscribe device tokens to a topic."""
        payload = {
            "topic": topic,
            "device_tokens": device_tokens
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/notifications/topics/subscribe",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def send_batch_notifications(
        self,
        notifications: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Send batch notifications."""
        payload = {
            "notifications": notifications
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/notifications/batch",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def get_notification_status(
        self,
        notification_id: str
    ) -> Dict[str, Any]:
        """Get notification status."""
        response = await self.client.get(
            f"{self.base_url}/api/v1/notifications/status/{notification_id}"
        )
        response.raise_for_status()
        return response.json()
    
    async def health_check(self) -> Dict[str, Any]:
        """Get service health status."""
        response = await self.client.get(f"{self.base_url}/health/")
        response.raise_for_status()
        return response.json()


async def main():
    """Main function demonstrating API usage."""
    client = NotificationServiceClient()
    
    try:
        # Check service health
        print("🔍 Checking service health...")
        health = await client.health_check()
        print(f"Service status: {health['status']}")
        print(f"Uptime: {health['uptime_seconds']:.2f} seconds")
        print()
        
        # Example 1: Send alert notification to device tokens
        print("📱 Example 1: Sending alert notification to device tokens")
        device_tokens = [
            {"token": "device_token_1", "platform": "android"},
            {"token": "device_token_2", "platform": "ios"}
        ]
        
        result = await client.send_notification(
            device_tokens=device_tokens,
            notification_type="alert",
            title="Important Alert",
            body="This is an important notification",
            data={"alert_id": "123", "category": "urgent"},
            priority="high"
        )
        
        print(f"✅ Notification sent successfully!")
        print(f"   Notification ID: {result['notification_id']}")
        print(f"   Total sent: {result['total_sent']}")
        print(f"   Total failed: {result['total_failed']}")
        print(f"   Processing time: {result['processing_time_ms']:.2f}ms")
        print()
        
        # Example 2: Send silent notification to topic
        print("📢 Example 2: Sending silent notification to topic")
        topic_result = await client.send_topic_notification(
            topic="news",
            notification_type="silent",
            data={
                "news_id": "456",
                "category": "technology",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        )
        
        print(f"✅ Topic notification sent successfully!")
        print(f"   Notification ID: {topic_result['notification_id']}")
        print(f"   Topic: {topic_result['topic']}")
        print(f"   Message ID: {topic_result['message_id']}")
        print()
        
        # Example 3: Subscribe devices to topic
        print("📋 Example 3: Subscribing devices to topic")
        subscribe_result = await client.subscribe_to_topic(
            topic="news",
            device_tokens=["device_token_1", "device_token_2", "device_token_3"]
        )
        
        print(f"✅ Topic subscription completed!")
        print(f"   Topic: {subscribe_result['topic']}")
        print(f"   Subscribed: {subscribe_result['subscribed_count']}")
        print(f"   Failed: {subscribe_result['failed_count']}")
        print()
        
        # Example 4: Send batch notifications
        print("📦 Example 4: Sending batch notifications")
        batch_notifications = [
            {
                "device_tokens": [
                    {"token": "batch_token_1", "platform": "android"}
                ],
                "notification_type": "alert",
                "title": "Batch Notification 1",
                "body": "First notification in batch",
                "priority": "normal"
            },
            {
                "device_tokens": [
                    {"token": "batch_token_2", "platform": "ios"}
                ],
                "notification_type": "silent",
                "data": {"batch_id": "789", "sequence": 2},
                "priority": "normal"
            }
        ]
        
        batch_result = await client.send_batch_notifications(batch_notifications)
        
        print(f"✅ Batch processing completed!")
        print(f"   Batch ID: {batch_result['batch_id']}")
        print(f"   Total notifications: {batch_result['total_notifications']}")
        print(f"   Successful: {batch_result['successful_notifications']}")
        print(f"   Failed: {batch_result['failed_notifications']}")
        print()
        
        # Example 5: Get notification status
        if result['notification_id']:
            print("📊 Example 5: Getting notification status")
            status = await client.get_notification_status(result['notification_id'])
            print(f"   Status: {status}")
            print()
        
        print("🎉 All examples completed successfully!")
        
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    print("🚀 Notification Service API Examples")
    print("=" * 50)
    print()
    
    asyncio.run(main()) 
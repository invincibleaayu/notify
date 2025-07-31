"""FCM client implementation using Firebase Admin SDK."""

import json
import logging
from typing import Any, Dict, List, Optional
import firebase_admin
from firebase_admin import credentials, messaging
from firebase_admin.exceptions import FirebaseError

from ...config.settings import settings

logger = logging.getLogger(__name__)


class FCMClient:
    """FCM client for sending notifications via Firebase Cloud Messaging."""
    
    def __init__(self):
        """Initialize FCM client with Firebase credentials."""
        self._app = None
        self._messaging = None
        self._initialize_firebase()
    
    def _initialize_firebase(self) -> None:
        """Initialize Firebase Admin SDK."""
        try:
            # Check if Firebase is already initialized
            try:
                self._app = firebase_admin.get_app()
                logger.info("Using existing Firebase app")
            except ValueError:
                # Firebase not initialized, create new app
                # Create service account credentials
                cred_dict = {
                    "type": "service_account",
                    "project_id": settings.fcm_project_id,
                    "private_key_id": settings.fcm_private_key_id,
                    "private_key": settings.fcm_private_key.replace("\\n", "\n"),
                    "client_email": settings.fcm_client_email,
                    "client_id": "",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{settings.fcm_client_email}"
                }
                
                cred = credentials.Certificate(cred_dict)
                
                # Initialize Firebase app
                self._app = firebase_admin.initialize_app(cred)
                logger.info("FCM client initialized successfully")
            
            self._messaging = messaging
            
        except Exception as e:
            logger.error(f"Failed to initialize FCM client: {e}")
            raise
    
    async def send_to_device(
        self,
        device_token: str,
        title: Optional[str] = None,
        body: Optional[str] = None,
        data: Optional[Dict[str, str]] = None,
        priority: str = "normal",
        collapse_key: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """Send notification to a single device."""
        try:
            # Prepare notification
            notification = messaging.Notification(
                title=title,
                body=body
            ) if title or body else None
            
            # Prepare message
            message = messaging.Message(
                notification=notification,
                data=data,
                token=device_token,
                android=messaging.AndroidConfig(
                    priority=priority,
                    collapse_key=collapse_key,
                    ttl=ttl if ttl else None
                ) if priority or collapse_key or ttl else None,
                apns=messaging.APNSConfig(
                    headers={"apns-priority": "10" if priority == "high" else "5"}
                ) if priority else None
            )
            
            # Send message
            response = self._messaging.send(message)
            
            logger.info(f"Successfully sent notification to device {device_token}: {response}")
            
            return {
                "success": True,
                "message_id": response,
                "device_token": device_token,
                "error": None
            }
            
        except FirebaseError as e:
            error_msg = f"FCM error for device {device_token}: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "message_id": None,
                "device_token": device_token,
                "error": str(e)
            }
        except Exception as e:
            error_msg = f"Unexpected error sending to device {device_token}: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "message_id": None,
                "device_token": device_token,
                "error": str(e)
            }
    
    async def send_to_multiple_devices(
        self,
        device_tokens: List[str],
        title: Optional[str] = None,
        body: Optional[str] = None,
        data: Optional[Dict[str, str]] = None,
        priority: str = "normal",
        collapse_key: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """Send notification to multiple devices."""
        try:
            # Prepare notification
            notification = messaging.Notification(
                title=title,
                body=body
            ) if title or body else None
            
            # Prepare message
            message = messaging.MulticastMessage(
                notification=notification,
                data=data,
                tokens=device_tokens,
                android=messaging.AndroidConfig(
                    priority=priority,
                    collapse_key=collapse_key,
                    ttl=ttl if ttl else None
                ) if priority or collapse_key or ttl else None,
                apns=messaging.APNSConfig(
                    headers={"apns-priority": "10" if priority == "high" else "5"}
                ) if priority else None
            )
            
            # Send message
            response = self._messaging.send_multicast(message)
            
            logger.info(f"Successfully sent notification to {response.success_count}/{len(device_tokens)} devices")
            
            return {
                "success": True,
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "responses": response.responses,
                "error": None
            }
            
        except FirebaseError as e:
            error_msg = f"FCM error for multiple devices: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "success_count": 0,
                "failure_count": len(device_tokens),
                "responses": [],
                "error": str(e)
            }
        except Exception as e:
            error_msg = f"Unexpected error sending to multiple devices: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "success_count": 0,
                "failure_count": len(device_tokens),
                "responses": [],
                "error": str(e)
            }
    
    async def send_to_topic(
        self,
        topic: str,
        title: Optional[str] = None,
        body: Optional[str] = None,
        data: Optional[Dict[str, str]] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Send notification to a topic."""
        try:
            # Prepare notification
            notification = messaging.Notification(
                title=title,
                body=body
            ) if title or body else None
            
            # Prepare message
            message = messaging.Message(
                notification=notification,
                data=data,
                topic=topic,
                android=messaging.AndroidConfig(
                    priority=priority
                ) if priority else None,
                apns=messaging.APNSConfig(
                    headers={"apns-priority": "10" if priority == "high" else "5"}
                ) if priority else None
            )
            
            # Send message
            response = self._messaging.send(message)
            
            logger.info(f"Successfully sent notification to topic {topic}: {response}")
            
            return {
                "success": True,
                "message_id": response,
                "topic": topic,
                "error": None
            }
            
        except FirebaseError as e:
            error_msg = f"FCM error for topic {topic}: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "message_id": None,
                "topic": topic,
                "error": str(e)
            }
        except Exception as e:
            error_msg = f"Unexpected error sending to topic {topic}: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "message_id": None,
                "topic": topic,
                "error": str(e)
            }
    
    async def subscribe_to_topic(
        self,
        topic: str,
        device_tokens: List[str]
    ) -> Dict[str, Any]:
        """Subscribe device tokens to a topic."""
        try:
            response = self._messaging.subscribe_to_topic(device_tokens, topic)
            
            logger.info(f"Successfully subscribed {response.success_count}/{len(device_tokens)} tokens to topic {topic}")
            
            return {
                "success": True,
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "errors": response.errors,
                "topic": topic
            }
            
        except FirebaseError as e:
            error_msg = f"FCM error subscribing to topic {topic}: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "success_count": 0,
                "failure_count": len(device_tokens),
                "errors": [str(e)],
                "topic": topic
            }
        except Exception as e:
            error_msg = f"Unexpected error subscribing to topic {topic}: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "success_count": 0,
                "failure_count": len(device_tokens),
                "errors": [str(e)],
                "topic": topic
            }
    
    async def unsubscribe_from_topic(
        self,
        topic: str,
        device_tokens: List[str]
    ) -> Dict[str, Any]:
        """Unsubscribe device tokens from a topic."""
        try:
            response = self._messaging.unsubscribe_from_topic(device_tokens, topic)
            
            logger.info(f"Successfully unsubscribed {response.success_count}/{len(device_tokens)} tokens from topic {topic}")
            
            return {
                "success": True,
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "errors": response.errors,
                "topic": topic
            }
            
        except FirebaseError as e:
            error_msg = f"FCM error unsubscribing from topic {topic}: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "success_count": 0,
                "failure_count": len(device_tokens),
                "errors": [str(e)],
                "topic": topic
            }
        except Exception as e:
            error_msg = f"Unexpected error unsubscribing from topic {topic}: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "success_count": 0,
                "failure_count": len(device_tokens),
                "errors": [str(e)],
                "topic": topic
            }
    
    def cleanup(self):
        """Cleanup Firebase app. Call this when shutting down."""
        if self._app:
            try:
                firebase_admin.delete_app(self._app)
                logger.info("Firebase app cleaned up successfully")
            except Exception as e:
                logger.warning(f"Error during Firebase app cleanup: {e}") 
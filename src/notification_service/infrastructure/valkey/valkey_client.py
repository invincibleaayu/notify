"""Valkey client implementation for Redis-compatible operations."""

import json
import logging
import asyncio
from typing import Any, Dict, List, Optional
import redis.asyncio as redis
from redis.exceptions import RedisError

from ...config.settings import settings

logger = logging.getLogger(__name__)


class ValkeyClient:
    """Valkey client for Redis-compatible operations."""
    
    def __init__(self):
        """Initialize Valkey client."""
        self._redis: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to Valkey/Redis server."""
        try:
            self._redis = redis.from_url(
                settings.valkey_url,
                db=settings.valkey_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            await self._redis.ping()
            self._connected = True
            
            logger.info("Successfully connected to Valkey/Redis")
            
        except Exception as e:
            logger.error(f"Failed to connect to Valkey/Redis: {e}")
            self._connected = False
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Valkey/Redis server."""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("Disconnected from Valkey/Redis")
    
    async def is_connected(self) -> bool:
        """Check if connected to Valkey/Redis."""
        if not self._redis or not self._connected:
            return False
        
        try:
            await self._redis.ping()
            return True
        except Exception:
            self._connected = False
            return False
    
    async def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """Publish message to a channel."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            message_json = json.dumps(message)
            subscribers = await self._redis.publish(channel, message_json)
            logger.debug(f"Published message to channel {channel}: {subscribers} subscribers")
            return subscribers
        except RedisError as e:
            logger.error(f"Failed to publish to channel {channel}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error publishing to channel {channel}: {e}")
            raise
    
    async def subscribe(self, channel: str) -> redis.Redis:
        """Subscribe to a channel."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            pubsub = self._redis.pubsub()
            await pubsub.subscribe(channel)
            logger.debug(f"Subscribed to channel {channel}")
            return pubsub
        except RedisError as e:
            logger.error(f"Failed to subscribe to channel {channel}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error subscribing to channel {channel}: {e}")
            raise
    
    async def lpush(self, queue: str, message: Dict[str, Any]) -> int:
        """Push message to the left of a list (queue)."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            message_json = json.dumps(message)
            length = await self._redis.lpush(queue, message_json)
            logger.debug(f"Pushed message to queue {queue}, length: {length}")
            return length
        except RedisError as e:
            logger.error(f"Failed to push to queue {queue}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error pushing to queue {queue}: {e}")
            raise
    
    async def rpop(self, queue: str, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """Pop message from the right of a list (queue)."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            if timeout > 0:
                result = await self._redis.brpop(queue, timeout)
                if result:
                    message_json = result[1]
                    return json.loads(message_json)
            else:
                message_json = await self._redis.rpop(queue)
                if message_json:
                    return json.loads(message_json)
            
            return None
        except RedisError as e:
            logger.error(f"Failed to pop from queue {queue}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error popping from queue {queue}: {e}")
            raise
    
    async def llen(self, queue: str) -> int:
        """Get the length of a list (queue)."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            length = await self._redis.llen(queue)
            return length
        except RedisError as e:
            logger.error(f"Failed to get length of queue {queue}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting length of queue {queue}: {e}")
            raise
    
    async def xadd(self, stream: str, fields: Dict[str, Any], max_len: Optional[int] = None) -> str:
        """Add message to a stream."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            # Convert fields to string values
            stream_fields = {k: str(v) for k, v in fields.items()}
            
            if max_len:
                message_id = await self._redis.xadd(stream, stream_fields, maxlen=max_len)
            else:
                message_id = await self._redis.xadd(stream, stream_fields)
            
            logger.debug(f"Added message to stream {stream}: {message_id}")
            return message_id
        except RedisError as e:
            logger.error(f"Failed to add to stream {stream}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error adding to stream {stream}: {e}")
            raise
    
    async def xread(self, streams: Dict[str, str], count: Optional[int] = None, block: Optional[int] = None) -> List[Dict[str, Any]]:
        """Read messages from streams."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            if block:
                messages = await self._redis.xread(streams, count=count, block=block)
            else:
                messages = await self._redis.xread(streams, count=count)
            
            result = []
            for stream_name, stream_messages in messages:
                for message_id, fields in stream_messages:
                    result.append({
                        "stream": stream_name,
                        "id": message_id,
                        "fields": fields
                    })
            
            logger.debug(f"Read {len(result)} messages from streams")
            return result
        except RedisError as e:
            logger.error(f"Failed to read from streams: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error reading from streams: {e}")
            raise
    
    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set a key-value pair with optional expiration."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            if isinstance(value, dict):
                value = json.dumps(value)
            
            result = await self._redis.set(key, value, ex=ex)
            return result
        except RedisError as e:
            logger.error(f"Failed to set key {key}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error setting key {key}: {e}")
            raise
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value by key."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            value = await self._redis.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except RedisError as e:
            logger.error(f"Failed to get key {key}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting key {key}: {e}")
            raise
    
    async def delete(self, key: str) -> int:
        """Delete a key."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            result = await self._redis.delete(key)
            return result
        except RedisError as e:
            logger.error(f"Failed to delete key {key}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting key {key}: {e}")
            raise
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            result = await self._redis.exists(key)
            return bool(result)
        except RedisError as e:
            logger.error(f"Failed to check existence of key {key}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error checking existence of key {key}: {e}")
            raise
    
    async def incr(self, key: str) -> int:
        """Increment a counter."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            result = await self._redis.incr(key)
            return result
        except RedisError as e:
            logger.error(f"Failed to increment key {key}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error incrementing key {key}: {e}")
            raise
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            result = await self._redis.expire(key, seconds)
            return bool(result)
        except RedisError as e:
            logger.error(f"Failed to set expiration for key {key}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error setting expiration for key {key}: {e}")
            raise 
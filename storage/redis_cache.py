"""
Centralized Redis operations for JSON serialization/deserialization
Reduces code duplication across the application
"""
import json
from typing import Any, Optional, Dict
from storage.redis_client import get_redis


def get_json(key: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Retrieve JSON data from Redis, return default if not found
    
    Args:
        key: Redis key to retrieve
        default: Default value if key not found (default: empty dict)
    
    Returns:
        Parsed JSON data or default value
    """
    try:
        r = get_redis()
        data = r.get(key)
        if data:
            return json.loads(data)
        return default or {}
    except Exception as e:
        print(f"⚠️ Error retrieving JSON from Redis: {e}")
        return default or {}


def set_json(key: str, value: Dict[str, Any], expire: Optional[int] = None) -> bool:
    """
    Store JSON data in Redis with optional expiration
    
    Args:
        key: Redis key to set
        value: Dictionary to store as JSON
        expire: Optional expiration time in seconds
    
    Returns:
        True if successful, False otherwise
    """
    try:
        r = get_redis()
        serialized = json.dumps(value)
        r.set(key, serialized)
        if expire:
            r.expire(key, expire)
        return True
    except Exception as e:
        print(f"⚠️ Error storing JSON in Redis: {e}")
        return False


def update_json(key: str, updates: Dict[str, Any], expire: Optional[int] = None) -> Dict[str, Any]:
    """
    Update existing JSON data in Redis, preserving non-updated fields
    
    Args:
        key: Redis key to update
        updates: Dictionary containing fields to update
        expire: Optional expiration time in seconds
    
    Returns:
        Updated dictionary
    """
    try:
        r = get_redis()
        existing = get_json(key, {})
        existing.update(updates)
        set_json(key, existing, expire)
        return existing
    except Exception as e:
        print(f"⚠️ Error updating JSON in Redis: {e}")
        return updates


def delete_json(key: str) -> bool:
    """
    Delete JSON data from Redis
    
    Args:
        key: Redis key to delete
    
    Returns:
        True if successful or key didn't exist, False on error
    """
    try:
        r = get_redis()
        r.delete(key)
        return True
    except Exception as e:
        print(f"⚠️ Error deleting JSON from Redis: {e}")
        return False


def exists_json(key: str) -> bool:
    """
    Check if JSON key exists in Redis
    
    Args:
        key: Redis key to check
    
    Returns:
        True if key exists, False otherwise
    """
    try:
        r = get_redis()
        return r.exists(key) > 0
    except Exception as e:
        print(f"⚠️ Error checking Redis key: {e}")
        return False


def batch_get_json(keys: list) -> Dict[str, Dict[str, Any]]:
    """
    Retrieve multiple JSON values efficiently using pipeline
    
    Args:
        keys: List of Redis keys to retrieve
    
    Returns:
        Dictionary mapping keys to their JSON values
    """
    try:
        r = get_redis()
        pipe = r.pipeline()
        for key in keys:
            pipe.get(key)
        results = pipe.execute()
        
        return {
            key: json.loads(result) if result else {}
            for key, result in zip(keys, results)
        }
    except Exception as e:
        print(f"⚠️ Error batch retrieving JSON from Redis: {e}")
        return {key: {} for key in keys}

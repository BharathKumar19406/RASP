"""
Cryptographic utilities for consistent hashing and security operations
Centralizes hashing logic used across the application
"""
import hashlib
from typing import Tuple


def hash_ip(ip: str, length: int = 16) -> str:
    """
    Hash an IP address using SHA256 for anonymization
    
    Args:
        ip: IP address to hash
        length: Length of hash to return (default 16)
    
    Returns:
        Hashed IP address
    
    Example:
        >>> hash_ip("192.168.1.1")
        'a1b2c3d4e5f6g7h8'
    """
    if not ip:
        return "unknown"
    try:
        return hashlib.sha256(ip.encode()).hexdigest()[:length]
    except Exception as e:
        print(f"⚠️ Error hashing IP: {e}")
        return "error"


def hash_endpoint(endpoint: str, method: str = "GET", length: int = 16) -> str:
    """
    Hash an endpoint and method for consistent identification
    
    Args:
        endpoint: API endpoint URL
        method: HTTP method (GET, POST, etc.)
        length: Length of hash to return
    
    Returns:
        Hashed endpoint identifier
    """
    if not endpoint:
        return "unknown"
    try:
        combined = f"{method}:{endpoint}"
        return hashlib.sha256(combined.encode()).hexdigest()[:length]
    except Exception as e:
        print(f"⚠️ Error hashing endpoint: {e}")
        return "error"


def hash_body(body: str, length: int = 16) -> str:
    """
    Hash request body for fingerprinting and deduplication
    
    Args:
        body: Request body content
        length: Length of hash to return
    
    Returns:
        Hashed body fingerprint
    """
    if not body:
        return hashlib.sha256(b"").hexdigest()[:length]
    try:
        return hashlib.sha256(body.encode()).hexdigest()[:length]
    except Exception as e:
        print(f"⚠️ Error hashing body: {e}")
        return "error"


def hash_user(user_id: str, salt: str = "", length: int = 16) -> str:
    """
    Hash user identifier with optional salt
    
    Args:
        user_id: User identifier
        salt: Optional salt for additional security
        length: Length of hash to return
    
    Returns:
        Hashed user identifier
    """
    if not user_id:
        return "unknown"
    try:
        data = f"{user_id}{salt}".encode()
        return hashlib.sha256(data).hexdigest()[:length]
    except Exception as e:
        print(f"⚠️ Error hashing user: {e}")
        return "error"


def hash_request_signature(ip: str, endpoint: str, method: str, body_hash: str) -> str:
    """
    Create a signature representing a unique request pattern
    
    Args:
        ip: Client IP
        endpoint: API endpoint
        method: HTTP method
        body_hash: Hash of request body
    
    Returns:
        Request signature
    """
    try:
        signature = f"{ip}:{endpoint}:{method}:{body_hash}"
        return hashlib.sha256(signature.encode()).hexdigest()[:16]
    except Exception as e:
        print(f"⚠️ Error creating request signature: {e}")
        return "error"


def verify_data_integrity(data: str, known_hash: str) -> bool:
    """
    Verify data integrity by comparing computed hash with known hash
    
    Args:
        data: Data to verify
        known_hash: Expected hash value
    
    Returns:
        True if hashes match, False otherwise
    """
    try:
        computed_hash = hashlib.sha256(data.encode()).hexdigest()
        return computed_hash == known_hash
    except Exception as e:
        print(f"⚠️ Error verifying data integrity: {e}")
        return False

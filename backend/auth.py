"""
PIN-based authentication with JWT tokens.
"""
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# Security scheme
security = HTTPBearer()


class AuthManager:
    """Manages PIN authentication and JWT tokens."""

    def __init__(
        self,
        pin: str,
        secret_key: str,
        algorithm: str = "HS256",
        expiration_hours: int = 24
    ):
        """
        Initialize the authentication manager.

        Args:
            pin: Plain text PIN (will be hashed)
            secret_key: Secret key for JWT signing
            algorithm: JWT algorithm
            expiration_hours: Token expiration time in hours
        """
        # Hash the PIN using bcrypt
        self.pin_hash = bcrypt.hashpw(pin.encode('utf-8'), bcrypt.gensalt())
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_hours = expiration_hours

    def verify_pin(self, pin: str) -> bool:
        """
        Verify a PIN against the stored hash.

        Args:
            pin: Plain text PIN to verify

        Returns:
            True if PIN matches, False otherwise
        """
        return bcrypt.checkpw(pin.encode('utf-8'), self.pin_hash)

    def create_token(self, data: dict) -> str:
        """
        Create a JWT token.

        Args:
            data: Data to encode in the token

        Returns:
            JWT token string
        """
        to_encode = data.copy()

        # Add expiration
        expire = datetime.utcnow() + timedelta(hours=self.expiration_hours)
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})

        # Create token
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )

        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token data if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError:
            return None

    def authenticate(self, pin: str) -> Optional[str]:
        """
        Authenticate with PIN and return a JWT token.

        Args:
            pin: Plain text PIN

        Returns:
            JWT token if authentication successful, None otherwise
        """
        if not self.verify_pin(pin):
            return None

        # Create token with basic payload
        token = self.create_token({"sub": "user", "authenticated": True})
        return token


# Global auth manager instance (will be initialized in app.py)
_auth_manager: Optional[AuthManager] = None


def init_auth(
    pin: str,
    secret_key: str,
    algorithm: str = "HS256",
    expiration_hours: int = 24
):
    """
    Initialize the global authentication manager.

    Args:
        pin: Plain text PIN
        secret_key: Secret key for JWT signing
        algorithm: JWT algorithm
        expiration_hours: Token expiration time in hours
    """
    global _auth_manager
    _auth_manager = AuthManager(pin, secret_key, algorithm, expiration_hours)


def get_auth_manager() -> AuthManager:
    """
    Get the global authentication manager instance.

    Returns:
        AuthManager instance

    Raises:
        RuntimeError: If auth manager not initialized
    """
    if _auth_manager is None:
        raise RuntimeError("Auth manager not initialized. Call init_auth() first.")
    return _auth_manager


async def verify_auth_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    FastAPI dependency to verify authentication token.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    auth_manager = get_auth_manager()

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing"
        )

    token = credentials.credentials
    payload = auth_manager.verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return payload


def require_auth(token_payload: dict = Depends(verify_auth_token)) -> dict:
    """
    FastAPI dependency for routes that require authentication.

    Args:
        token_payload: Token payload from verify_auth_token

    Returns:
        Token payload

    Raises:
        HTTPException: If not authenticated
    """
    if not token_payload.get("authenticated"):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    return token_payload

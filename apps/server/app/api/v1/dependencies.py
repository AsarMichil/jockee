from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token
from app.core.spotify import SpotifyClient
import redis
from app.core.config import settings

security = HTTPBearer(auto_error=False)

# Redis client for session storage
redis_client = redis.from_url(settings.REDIS_URL)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """
    Get current user from JWT token.
    For Phase 1, this is optional - we'll implement proper auth in Phase 2.
    """
    if not credentials:
        return None

    token = credentials.credentials
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


def get_spotify_client(
    request: Request, current_user: Optional[str] = Depends(get_current_user)
) -> SpotifyClient:
    """
    Get Spotify client with access token from session.
    """
    # For Phase 1, we'll store Spotify tokens in Redis sessions
    # In Phase 2, we'll implement proper user accounts

    session_id = request.session.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No Spotify session found. Please authenticate with Spotify first.",
        )

    # Get access token from Redis
    token_key = f"spotify_token:{session_id}"
    token_data = redis_client.get(token_key)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Spotify session expired. Please re-authenticate.",
        )

    import json

    token_info = json.loads(token_data)
    access_token = token_info.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Spotify token. Please re-authenticate.",
        )

    return SpotifyClient(access_token=access_token)


def get_spotify_access_token(request: Request) -> str:
    """
    Get Spotify access token from session.
    Used for background tasks that need the token.
    """
    session_id = request.session.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No Spotify session found"
        )

    token_key = f"spotify_token:{session_id}"
    token_data = redis_client.get(token_key)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Spotify session expired"
        )

    import json

    token_info = json.loads(token_data)
    access_token = token_info.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Spotify token"
        )

    return access_token

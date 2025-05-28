from fastapi import APIRouter, HTTPException, Request, Query, Depends
from app.core.spotify import SpotifyClient
from app.api.v1.dependencies import redis_client, get_spotify_client
import uuid
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/spotify")
async def spotify_auth(request: Request):
    """
    Initiate Spotify OAuth flow.
    """
    try:
        # Generate a unique state parameter for this auth flow
        state = str(uuid.uuid4())
        
        spotify_client = SpotifyClient()
        auth_url = spotify_client.get_authorization_url(state=state)

        logger.info(f"Spotify auth URL: {auth_url}")

        # Get or create session ID
        session_id = request.session.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session["session_id"] = session_id

        # Store the state and session mapping in Redis for 10 minutes
        state_key = f"spotify_state:{state}"
        redis_client.setex(state_key, 600, session_id)  # 10 minutes

        logger.info(f"Starting Spotify auth for session {session_id} with state {state}")

        return {"auth_url": auth_url, "session_id": session_id, "state": state}

    except Exception as e:
        logger.error(f"Error initiating Spotify auth: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to initiate Spotify authentication"
        )


@router.get("/spotify/callback")
async def spotify_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from Spotify"),
    state: str = Query(None, description="State parameter"),
    error: str = Query(None, description="Error from Spotify"),
):
    """
    Handle Spotify OAuth callback.
    """
    if error:
        logger.error(f"Spotify auth error: {error}")
        raise HTTPException(
            status_code=400, detail=f"Spotify authentication failed: {error}"
        )

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    if not state:
        raise HTTPException(status_code=400, detail="Missing state parameter")

    try:
        # Validate state parameter and get session ID
        state_key = f"spotify_state:{state}"
        session_id = redis_client.get(state_key)
        
        if not session_id:
            logger.error(f"Invalid or expired state parameter: {state}")
            raise HTTPException(status_code=400, detail="Invalid or expired authentication session")
        
        session_id = session_id.decode('utf-8')
        
        # Clean up the state key
        redis_client.delete(state_key)

        # Set the session ID in the current session
        request.session["session_id"] = session_id

        # Exchange code for tokens
        spotify_client = SpotifyClient()
        token_info = spotify_client.get_access_token(code)

        # Store tokens in Redis with expiration
        token_key = f"spotify_token:{session_id}"
        redis_client.setex(
            token_key,
            3600,  # 1 hour expiration
            json.dumps(token_info),
        )

        logger.info(f"Spotify auth successful for session {session_id}")

        return {
            "message": "Spotify authentication successful",
            "session_id": session_id,
            "expires_in": token_info.get("expires_in", 3600),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Spotify callback: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to complete Spotify authentication"
        )


@router.get("/me")
async def get_current_user(
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    """
    Get current user profile from Spotify.
    """
    try:
        user_data = spotify_client.get_current_user()
        
        return {
            "id": user_data["id"],
            "display_name": user_data.get("display_name"),
            "email": user_data.get("email"),
            "country": user_data.get("country"),
            "followers": user_data.get("followers", {}).get("total", 0),
            "images": user_data.get("images", []),
            "external_urls": user_data.get("external_urls", {}),
        }
        
    except Exception as e:
        logger.error(f"Error fetching current user: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch user profile"
        )


@router.get("/status")
async def auth_status(request: Request):
    """
    Check authentication status.
    """
    session_id = request.session.get("session_id")
    if not session_id:
        return {"authenticated": False, "spotify_connected": False, "session_id": None}

    # Check if Spotify token exists and is valid
    token_key = f"spotify_token:{session_id}"
    token_data = redis_client.get(token_key)

    spotify_connected = False
    if token_data:
        try:
            json.loads(token_data)  # Just validate JSON format
            # Could add token validation here
            spotify_connected = True
        except (json.JSONDecodeError, ValueError):
            pass

    return {
        "authenticated": True,
        "spotify_connected": spotify_connected,
        "session_id": session_id,
    }


@router.post("/logout")
async def logout(request: Request):
    """
    Logout and clear session.
    """
    session_id = request.session.get("session_id")

    if session_id:
        # Clear Spotify token from Redis
        token_key = f"spotify_token:{session_id}"
        redis_client.delete(token_key)

        # Clear session
        request.session.clear()

        logger.info(f"User logged out, session {session_id} cleared")

    return {"message": "Logged out successfully"}


@router.post("/refresh")
async def refresh_token(request: Request):
    """
    Refresh Spotify access token.
    """
    session_id = request.session.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="No active session")

    token_key = f"spotify_token:{session_id}"
    token_data = redis_client.get(token_key)

    if not token_data:
        raise HTTPException(status_code=401, detail="No Spotify token found")

    try:
        token_info = json.loads(token_data)
        refresh_token = token_info.get("refresh_token")

        if not refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token available")

        # Refresh the token
        spotify_client = SpotifyClient()
        new_token_info = spotify_client.refresh_access_token(refresh_token)

        # Update stored token
        redis_client.setex(
            token_key,
            3600,  # 1 hour expiration
            json.dumps(new_token_info),
        )

        logger.info(f"Token refreshed for session {session_id}")

        return {
            "message": "Token refreshed successfully",
            "expires_in": new_token_info.get("expires_in", 3600),
        }

    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh token")

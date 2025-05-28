import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import Dict, List, Optional, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class SpotifyClient:
    """Spotify API client wrapper."""

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self._client = None

    def get_auth_manager(self) -> SpotifyOAuth:
        """Get Spotify OAuth manager."""
        return SpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI,
            scope="playlist-read-private playlist-read-collaborative user-library-read user-read-email",
            cache_path=None,  # Don't cache tokens to file
        )

    def get_client(self) -> spotipy.Spotify:
        """Get authenticated Spotify client."""
        if not self._client and self.access_token:
            self._client = spotipy.Spotify(auth=self.access_token)
        return self._client

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get Spotify authorization URL."""
        auth_manager = self.get_auth_manager()
        return auth_manager.get_authorize_url(state=state)

    def get_access_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        auth_manager = self.get_auth_manager()
        token_info = auth_manager.get_access_token(code)
        return token_info

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        auth_manager = self.get_auth_manager()
        token_info = auth_manager.refresh_access_token(refresh_token)
        return token_info

    def get_current_user(self) -> Dict[str, Any]:
        """Get current user profile."""
        client = self.get_client()
        if not client:
            raise ValueError("No authenticated Spotify client available")
        
        return client.current_user()

    def get_user_playlists(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get current user's playlists."""
        client = self.get_client()
        if not client:
            raise ValueError("No authenticated Spotify client available")
        
        return client.current_user_playlists(limit=limit, offset=offset)

    def search_playlists(self, query: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Search for playlists."""
        client = self.get_client()
        if not client:
            raise ValueError("No authenticated Spotify client available")
        
        results = client.search(q=query, type='playlist', limit=limit, offset=offset)
        return results['playlists']

    def get_playlist_details(self, playlist_id: str) -> Dict[str, Any]:
        """Get detailed playlist information."""
        client = self.get_client()
        if not client:
            raise ValueError("No authenticated Spotify client available")
        
        return client.playlist(playlist_id)

    def extract_playlist_id(self, playlist_url: str) -> Optional[str]:
        """Extract playlist ID from Spotify URL."""
        try:
            # Handle different URL formats
            if "playlist/" in playlist_url:
                playlist_id = playlist_url.split("playlist/")[1].split("?")[0]
                return playlist_id
            elif "open.spotify.com" in playlist_url:
                # Handle web player URLs
                parts = playlist_url.split("/")
                if "playlist" in parts:
                    idx = parts.index("playlist")
                    if idx + 1 < len(parts):
                        return parts[idx + 1].split("?")[0]
            return None
        except Exception as e:
            logger.error(f"Error extracting playlist ID from URL {playlist_url}: {e}")
            return None

    def get_playlist_tracks(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Get all tracks from a playlist."""
        client = self.get_client()
        if not client:
            raise ValueError("No authenticated Spotify client available")

        tracks = []
        results = client.playlist_tracks(playlist_id)

        while results:
            for item in results["items"]:
                if item["track"] and item["track"]["type"] == "track":
                    track = item["track"]
                    tracks.append(
                        {
                            "spotify_id": track["id"],
                            "title": track["name"],
                            "artist": ", ".join(
                                [artist["name"] for artist in track["artists"]]
                            ),
                            "album": track["album"]["name"],
                            "duration_ms": track["duration_ms"],
                            "preview_url": track["preview_url"],
                            "external_urls": track["external_urls"],
                            "popularity": track["popularity"],
                        }
                    )

            if results["next"]:
                results = client.next(results)
            else:
                break

        return tracks

    def get_playlist_info(self, playlist_id: str) -> Dict[str, Any]:
        """Get playlist metadata."""
        client = self.get_client()
        if not client:
            raise ValueError("No authenticated Spotify client available")

        playlist = client.playlist(playlist_id)
        return {
            "id": playlist["id"],
            "name": playlist["name"],
            "description": playlist["description"],
            "owner": playlist["owner"]["display_name"],
            "total_tracks": playlist["tracks"]["total"],
            "public": playlist["public"],
            "external_urls": playlist["external_urls"],
        }

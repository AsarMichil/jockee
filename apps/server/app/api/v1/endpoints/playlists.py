from fastapi import APIRouter, HTTPException, Depends, Query
from app.api.v1.dependencies import get_spotify_client
from app.core.spotify import SpotifyClient
from app.schemas.playlist import (
    PlaylistsResponse,
    PlaylistDetailsResponse,
    SpotifyPlaylist,
    SpotifyImage,
    SpotifyOwner,
    SpotifyTracks,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=PlaylistsResponse)
async def get_user_playlists(
    limit: int = Query(50, ge=1, le=50, description="Number of playlists to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    """
    Get current user's playlists.
    """
    try:
        # Fetch playlists from Spotify
        playlists_data = spotify_client.get_user_playlists(limit=limit, offset=offset)
        
        # Convert to our schema format
        playlists = []
        for item in playlists_data.get("items", []):
            playlist = SpotifyPlaylist(
                id=item["id"],
                name=item["name"],
                description=item.get("description"),
                public=item.get("public"),
                collaborative=item.get("collaborative", False),
                images=[
                    SpotifyImage(
                        url=img["url"],
                        height=img.get("height"),
                        width=img.get("width")
                    ) for img in item.get("images", [])
                ],
                owner=SpotifyOwner(
                    id=item["owner"]["id"],
                    display_name=item["owner"].get("display_name"),
                    external_urls=item["owner"]["external_urls"]
                ),
                tracks=SpotifyTracks(
                    total=item["tracks"]["total"],
                    href=item["tracks"]["href"]
                ),
                external_urls=item["external_urls"],
                snapshot_id=item["snapshot_id"]
            )
            playlists.append(playlist)
        
        return PlaylistsResponse(
            items=playlists,
            total=playlists_data.get("total", len(playlists)),
            limit=playlists_data.get("limit", limit),
            offset=playlists_data.get("offset", offset),
            next=playlists_data.get("next"),
            previous=playlists_data.get("previous"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user playlists: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user playlists")


@router.get("/search", response_model=PlaylistsResponse)
async def search_playlists(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Number of playlists to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    """
    Search for playlists on Spotify.
    """
    try:
        # Search playlists from Spotify
        playlists_data = spotify_client.search_playlists(query=q, limit=limit, offset=offset)
        
        # Convert to our schema format
        playlists = []
        for item in playlists_data.get("items", []):
            playlist = SpotifyPlaylist(
                id=item["id"],
                name=item["name"],
                description=item.get("description"),
                public=item.get("public"),
                collaborative=item.get("collaborative", False),
                images=[
                    SpotifyImage(
                        url=img["url"],
                        height=img.get("height"),
                        width=img.get("width")
                    ) for img in item.get("images", [])
                ],
                owner=SpotifyOwner(
                    id=item["owner"]["id"],
                    display_name=item["owner"].get("display_name"),
                    external_urls=item["owner"]["external_urls"]
                ),
                tracks=SpotifyTracks(
                    total=item["tracks"]["total"],
                    href=item["tracks"]["href"]
                ),
                external_urls=item["external_urls"],
                snapshot_id=item["snapshot_id"]
            )
            playlists.append(playlist)
        
        return PlaylistsResponse(
            items=playlists,
            total=playlists_data.get("total", len(playlists)),
            limit=playlists_data.get("limit", limit),
            offset=playlists_data.get("offset", offset),
            next=playlists_data.get("next"),
            previous=playlists_data.get("previous"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching playlists: {e}")
        raise HTTPException(status_code=500, detail="Failed to search playlists")


@router.get("/{playlist_id}", response_model=PlaylistDetailsResponse)
async def get_playlist_details(
    playlist_id: str,
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    """
    Get detailed playlist information.
    """
    try:
        playlist_data = spotify_client.get_playlist_details(playlist_id)
        
        return PlaylistDetailsResponse(
            id=playlist_data["id"],
            name=playlist_data["name"],
            description=playlist_data.get("description"),
            public=playlist_data.get("public"),
            collaborative=playlist_data.get("collaborative", False),
            images=[
                SpotifyImage(
                    url=img["url"],
                    height=img.get("height"),
                    width=img.get("width")
                ) for img in playlist_data.get("images", [])
            ],
            owner=SpotifyOwner(
                id=playlist_data["owner"]["id"],
                display_name=playlist_data["owner"].get("display_name"),
                external_urls=playlist_data["owner"]["external_urls"]
            ),
            tracks=SpotifyTracks(
                total=playlist_data["tracks"]["total"],
                href=playlist_data["tracks"]["href"]
            ),
            external_urls=playlist_data["external_urls"],
            snapshot_id=playlist_data["snapshot_id"],
            followers=playlist_data.get("followers", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting playlist details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get playlist details")

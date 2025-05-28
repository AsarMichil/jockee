from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class SpotifyImage(BaseModel):
    """Spotify image object."""
    url: str
    height: Optional[int] = None
    width: Optional[int] = None


class SpotifyOwner(BaseModel):
    """Spotify playlist owner."""
    id: str
    display_name: Optional[str] = None
    external_urls: Dict[str, str]


class SpotifyTracks(BaseModel):
    """Spotify tracks summary."""
    total: int
    href: str


class SpotifyPlaylist(BaseModel):
    """Spotify playlist object."""
    id: str
    name: str
    description: Optional[str] = None
    public: Optional[bool] = None
    collaborative: bool = False
    images: List[SpotifyImage] = []
    owner: SpotifyOwner
    tracks: SpotifyTracks
    external_urls: Dict[str, str]
    snapshot_id: str


class PlaylistsResponse(BaseModel):
    """Response for user playlists."""
    items: List[SpotifyPlaylist]
    total: int
    limit: int
    offset: int
    next: Optional[str] = None
    previous: Optional[str] = None


class PlaylistDetailsResponse(BaseModel):
    """Detailed playlist information."""
    id: str
    name: str
    description: Optional[str] = None
    public: Optional[bool] = None
    collaborative: bool = False
    images: List[SpotifyImage] = []
    owner: SpotifyOwner
    tracks: SpotifyTracks
    external_urls: Dict[str, str]
    snapshot_id: str
    followers: Dict[str, Any] 
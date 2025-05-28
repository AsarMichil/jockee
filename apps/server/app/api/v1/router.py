from fastapi import APIRouter
from app.api.v1.endpoints import auth, playlists, tracks, jobs

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(playlists.router, prefix="/playlists", tags=["playlists"])
api_router.include_router(tracks.router, prefix="/tracks", tags=["tracks"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

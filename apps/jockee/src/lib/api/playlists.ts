import { apiClient } from "./client";
import { SpotifyPlaylist, PlaylistsResponse } from "../types";

export const playlistsApi = {
  // Get user's playlists
  getUserPlaylists: async (
    limit: number = 50,
    offset: number = 0
  ): Promise<PlaylistsResponse> => {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString()
    });
    return await apiClient.get<PlaylistsResponse>(
      `/api/v1/playlists?${params}`
    );
  },

  // Search playlists
  searchPlaylists: async (
    query: string,
    limit: number = 20
  ): Promise<PlaylistsResponse> => {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString()
    });
    return await apiClient.get<PlaylistsResponse>(
      `/api/v1/playlists/search?${params}`
    );
  },

  // Get playlist details
  getPlaylist: async (playlistId: string): Promise<SpotifyPlaylist> => {
    return await apiClient.get<SpotifyPlaylist>(
      `/api/v1/playlists/${playlistId}`
    );
  },

  // {
  //   "spotify_playlist_url": "string",
  //   "options": {
  //     "auto_fetch_missing": true,
  //     "max_tracks": 50,
  //     "skip_analysis_if_exists": true,
  //     "download_timeout": 300
  //   }
  // }

  // Submit playlist for analysis
  analyzePlaylist: async (playlistUrl: string): Promise<{ id: string }> => {
    return await apiClient.post<{ id: string }>("/api/v1/jobs/analyze", {
      spotify_playlist_url: playlistUrl,
      options: {
        auto_fetch_missing: true,
        max_tracks: 50,
        skip_analysis_if_exists: false,
        download_timeout: 300
      }
    });
  }
};

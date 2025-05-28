import { apiClient } from './client';
import { SpotifyPlaylist, PlaylistsResponse } from '../types';

export const playlistsApi = {
  // Get user's playlists
  getUserPlaylists: async (
    limit: number = 50,
    offset: number = 0
  ): Promise<PlaylistsResponse> => {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    return await apiClient.get<PlaylistsResponse>(`/api/v1/playlists?${params}`);
  },

  // Search playlists
  searchPlaylists: async (
    query: string,
    limit: number = 20
  ): Promise<PlaylistsResponse> => {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString(),
    });
    return await apiClient.get<PlaylistsResponse>(`/api/v1/playlists/search?${params}`);
  },

  // Get playlist details
  getPlaylist: async (playlistId: string): Promise<SpotifyPlaylist> => {
    return await apiClient.get<SpotifyPlaylist>(`/api/v1/playlists/${playlistId}`);
  },

  // Submit playlist for analysis
  analyzePlaylist: async (playlistUrl: string): Promise<{ job_id: string }> => {
    return await apiClient.post<{ job_id: string }>('/api/v1/jobs/analyze', {
      spotify_playlist_url: playlistUrl,
    });
  },
}; 
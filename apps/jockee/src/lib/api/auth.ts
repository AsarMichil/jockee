import { apiClient } from './client';
import { SpotifyUser } from '../types';

export interface AuthStatus {
  authenticated: boolean;
  spotify_connected: boolean;
  session_id: string | null;
}

export const authApi = {
  // Check authentication status
  getStatus: async (): Promise<AuthStatus> => {
    return await apiClient.get<AuthStatus>('/api/v1/auth/status');
  },

  // Get current user profile (this would need to be implemented on the server)
  getCurrentUser: async (): Promise<SpotifyUser> => {
    return await apiClient.get<SpotifyUser>('/api/v1/auth/me');
  },

  // Refresh access token
  refreshToken: async (): Promise<{ message: string; expires_in: number }> => {
    return await apiClient.post<{ message: string; expires_in: number }>('/api/v1/auth/refresh');
  },

  // Logout
  logout: async (): Promise<{ message: string }> => {
    return await apiClient.post<{ message: string }>('/api/v1/auth/logout');
  },
};

// Session management helpers (no more localStorage)
export const sessionManager = {
  // Check if user is authenticated by calling the server
  checkAuth: async (): Promise<boolean> => {
    try {
      const status = await authApi.getStatus();
      return status.authenticated && status.spotify_connected;
    } catch (error) {
      return false;
    }
  },

  // Clear session (logout)
  clearSession: async (): Promise<void> => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
  },
}; 
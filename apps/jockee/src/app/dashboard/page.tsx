'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authApi, sessionManager } from '../../lib/api/auth';
import { playlistsApi } from '../../lib/api/playlists';
import { analysisApi } from '../../lib/api/analysis';
import { SpotifyUser, SpotifyPlaylist, AnalysisJob } from '../../lib/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<SpotifyUser | null>(null);
  const [playlists, setPlaylists] = useState<SpotifyPlaylist[]>([]);
  const [recentJobs, setRecentJobs] = useState<AnalysisJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const initializeDashboard = async () => {
      try {
        // Check authentication status first
        const isAuthenticated = await sessionManager.checkAuth();
        if (!isAuthenticated) {
          router.push('/login');
          return;
        }

        // Fetch user profile (you'll need to implement this endpoint on the server)
        try {
          const userProfile = await authApi.getCurrentUser();
          setUser(userProfile);
        } catch (err) {
          console.log('User profile not available yet');
        }

        // Fetch user's playlists
        const playlistsResponse = await playlistsApi.getUserPlaylists(20, 0);
        setPlaylists(playlistsResponse.items);

        // Fetch recent analysis jobs
        const jobs = await analysisApi.getUserJobs();
        setRecentJobs(jobs.slice(0, 5)); // Show last 5 jobs

      } catch (err) {
        console.error('Dashboard initialization error:', err);
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    initializeDashboard();
  }, [router]);

  const handleAnalyzePlaylist = async (playlist: SpotifyPlaylist) => {
    try {
      const response = await playlistsApi.analyzePlaylist(playlist.external_urls.spotify);
      router.push(`/analysis/${response.job_id}`);
    } catch (err) {
      console.error('Failed to start analysis:', err);
      setError('Failed to start playlist analysis');
    }
  };

  const handleLogout = async () => {
    try {
      await sessionManager.clearSession();
      router.push('/login');
    } catch (err) {
      console.error('Logout error:', err);
      router.push('/login');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={() => window.location.reload()}>
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold text-gray-900">Auto DJ</h1>
            <div className="flex items-center space-x-4">
              {user && (
                <span className="text-sm text-gray-600">
                  Welcome, {user.display_name}
                </span>
              )}
              <Button variant="outline" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent Mixes */}
          <div>
            <Card>
              <CardHeader>
                <CardTitle>Recent Mixes</CardTitle>
                <CardDescription>Your latest AI-generated mixes</CardDescription>
              </CardHeader>
              <CardContent>
                {recentJobs.length === 0 ? (
                  <p className="text-gray-500">No mixes yet. Analyze a playlist to get started!</p>
                ) : (
                  <div className="space-y-3">
                    {recentJobs.map((job) => (
                      <div
                        key={job.id}
                        className="p-3 border rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                        onClick={() => router.push(`/mix/${job.id}`)}
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium text-sm truncate">
                              Mix #{job.id}
                            </p>
                            <p className="text-xs text-gray-500">
                              {job.total_tracks} tracks
                            </p>
                          </div>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            job.status === 'completed' 
                              ? 'bg-green-100 text-green-800' 
                              : job.status === 'failed'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {job.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Playlists */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Your Playlists</CardTitle>
                <CardDescription>Select a playlist to create an AI-powered mix</CardDescription>
              </CardHeader>
              <CardContent>
                {playlists.length === 0 ? (
                  <p className="text-gray-500">No playlists found. Make sure you have playlists in your Spotify account.</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {playlists.map((playlist) => (
                      <div
                        key={playlist.id}
                        className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start space-x-3">
                          {playlist.images?.[0] && (
                            <img
                              src={playlist.images[0].url}
                              alt={playlist.name}
                              className="w-16 h-16 rounded-lg object-cover"
                            />
                          )}
                          <div className="flex-1 min-w-0">
                            <h3 className="font-medium text-gray-900 truncate">
                              {playlist.name}
                            </h3>
                            <p className="text-sm text-gray-500">
                              {playlist.tracks.total} tracks
                            </p>
                            {/* <p className="text-xs text-gray-400 truncate">
                              by {playlist.owner.display_name}
                            </p> */}
                          </div>
                        </div>
                        <Button
                          className="w-full mt-3"
                          onClick={() => handleAnalyzePlaylist(playlist)}
                        >
                          Create Mix
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
} 
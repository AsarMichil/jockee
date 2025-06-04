import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { authApi, sessionManager } from "../lib/api/auth";
import { playlistsApi } from "../lib/api/playlists";
import { analysisApi } from "../lib/api/analysis";
import { SpotifyUser, SpotifyPlaylist, AnalysisJob } from "../lib/types";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "../components/ui/card";
import { Button } from "../components/ui/button";

export default function DashboardPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState<SpotifyUser | null>(null);
  const [playlists, setPlaylists] = useState<SpotifyPlaylist[]>([]);
  const [recentJobs, setRecentJobs] = useState<AnalysisJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const initializeDashboard = async () => {
      try {
        // Check authentication status first
        const isAuthenticated = await sessionManager.checkAuth();
        if (!isAuthenticated) {
          navigate("/login");
          return;
        }

        // Fetch user profile (you'll need to implement this endpoint on the server)
        try {
          const userProfile = await authApi.getCurrentUser();
          setUser(userProfile);
        } catch (error) {
          console.error("Error fetching user profile:", error);
        }

        // Fetch user's playlists
        const playlistsResponse = await playlistsApi.getUserPlaylists(20, 0);
        setPlaylists(playlistsResponse.items);

        // Fetch recent analysis jobs
        const jobs = await analysisApi.getUserJobs();
        setRecentJobs(jobs.slice(0, 5)); // Show last 5 jobs
      } catch (err) {
        console.error("Dashboard initialization error:", err);
        setError("Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    };

    initializeDashboard();
  }, [navigate]);

  const handleAnalyzePlaylist = async (playlist: SpotifyPlaylist) => {
    try {
      const response = await playlistsApi.analyzePlaylist(
        playlist.external_urls.spotify
      );
      navigate(`/analysis/${response.job_id}`);
    } catch (err) {
      console.error("Failed to start analysis:", err);
      setError("Failed to start playlist analysis");
    }
  };

  const handleLogout = async () => {
    try {
      await sessionManager.clearSession();
      navigate("/login");
    } catch (err) {
      console.error("Logout error:", err);
      navigate("/login");
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
            <Button onClick={() => window.location.reload()}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
              {user && (
                <span className="ml-4 text-gray-600">
                  Welcome, {user.display_name}
                </span>
              )}
            </div>
            <Button variant="outline" onClick={handleLogout}>
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Jobs */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Analysis Jobs</CardTitle>
              <CardDescription>
                Your latest playlist analysis results
              </CardDescription>
            </CardHeader>
            <CardContent>
              {recentJobs.length === 0 ? (
                <p className="text-gray-500 text-center py-4">
                  No analysis jobs yet. Start by analyzing a playlist!
                </p>
              ) : (
                <div className="space-y-3">
                  {recentJobs.map((job) => (
                    <div
                      key={job.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
                      onClick={() => {
                        if (job.status === "completed") {
                          navigate(`/mix/${job.id}`);
                        } else {
                          navigate(`/analysis/${job.id}`);
                        }
                      }}
                    >
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">
                          {job.playlist_name}
                        </h4>
                        <p className="text-sm text-gray-500">
                          {job.total_tracks} tracks
                        </p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div
                          className={`px-2 py-1 rounded-full text-xs font-medium ${
                            job.status === "completed"
                              ? "bg-green-100 text-green-800"
                              : job.status === "processing"
                              ? "bg-blue-100 text-blue-800"
                              : job.status === "failed"
                              ? "bg-red-100 text-red-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {job.status}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Playlists */}
          <Card>
            <CardHeader>
              <CardTitle>Your Playlists</CardTitle>
              <CardDescription>
                Select a playlist to analyze and create mixes
              </CardDescription>
            </CardHeader>
            <CardContent>
              {playlists.length === 0 ? (
                <p className="text-gray-500 text-center py-4">
                  No playlists found. Make sure your Spotify account has
                  playlists.
                </p>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {playlists.map((playlist) => (
                    <div
                      key={playlist.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center space-x-3 flex-1">
                        {playlist.images?.[0] && (
                          <img
                            src={playlist.images[0].url}
                            alt={playlist.name}
                            className="w-12 h-12 rounded-lg object-cover"
                          />
                        )}
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-gray-900 truncate">
                            {playlist.name}
                          </h4>
                          <p className="text-sm text-gray-500">
                            {playlist.tracks.total} tracks
                          </p>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => handleAnalyzePlaylist(playlist)}
                        className="ml-3"
                      >
                        Analyze
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
} 
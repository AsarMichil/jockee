import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "../components/ui/card";

export default function LoginPage() {
  let currentUrl;
  if (window !== undefined) {
    currentUrl = window.location.origin;
  } else {
    currentUrl = undefined;
  }

  const handleSpotifyLogin = async () => {
    try {
      console.log(currentUrl);
      // Prepare the auth URL with optional redirect parameter
      const authUrl = new URL("http://localhost:8000/api/v1/auth/spotify");
      if (currentUrl) {
        authUrl.searchParams.set("redirect", currentUrl);
      }

      // Call the server-side auth endpoint
      const response = await fetch(authUrl.toString(), {
        method: "GET",
        credentials: "include" // Include cookies for session management
      });

      if (!response.ok) {
        throw new Error("Failed to initiate Spotify authentication");
      }

      const data = await response.json();

      // Redirect to the auth URL provided by the server
      window.location.href = data.auth_url;
    } catch (error) {
      console.error("Error initiating Spotify login:", error);
      // You might want to show an error message to the user here
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <div className="w-full max-w-md p-6">
        <Card className="backdrop-blur-sm bg-white/10 border-white/20">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold text-white mb-2">
              Welcome to Jockee
            </CardTitle>
            <CardDescription className="text-gray-300">
              Connect your Spotify account to start mixing your playlists
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={handleSpotifyLogin}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-4 rounded-lg transition-colors"
            >
              <svg
                className="w-5 h-5 mr-2"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.42 1.56-.299.421-1.02.599-1.559.3z" />
              </svg>
              Connect with Spotify
            </Button>
            <p className="text-xs text-gray-400 text-center">
              We&apos;ll use your Spotify account to access your playlists and
              create amazing mixes
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

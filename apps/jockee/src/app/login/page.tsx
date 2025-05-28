'use client';

import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';

export default function LoginPage() {
  const handleSpotifyLogin = async () => {
    try {
      // Call the server-side auth endpoint
      const response = await fetch('http://localhost:8000/api/v1/auth/spotify', {
        method: 'GET',
        credentials: 'include', // Include cookies for session management
      });
      
      if (!response.ok) {
        throw new Error('Failed to initiate Spotify authentication');
      }
      
      const data = await response.json();
      
      // Redirect to the auth URL provided by the server
      window.location.href = data.auth_url;
    } catch (error) {
      console.error('Error initiating Spotify login:', error);
      // You might want to show an error message to the user here
    }
  };
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <div className="w-full max-w-md p-6">
        <Card className="backdrop-blur-sm bg-white/10 border-white/20">
          <CardHeader className="text-center space-y-4">
            <div className="mx-auto w-20 h-20 bg-gradient-to-br from-green-400 to-blue-500 rounded-full flex items-center justify-center">
              <svg
                className="w-10 h-10 text-white"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
            </div>
            <CardTitle className="text-3xl font-bold text-white">
              Auto DJ
            </CardTitle>
            <CardDescription className="text-gray-300">
              Create seamless DJ mixes from your Spotify playlists using AI-powered analysis and automatic crossfading.
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div className="flex items-center space-x-3 text-gray-300">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-sm">Analyze your playlists</span>
              </div>
              <div className="flex items-center space-x-3 text-gray-300">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-sm">Generate perfect transitions</span>
              </div>
              <div className="flex items-center space-x-3 text-gray-300">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-sm">Play seamless mixes</span>
              </div>
            </div>
            
            <Button 
              onClick={handleSpotifyLogin} 
              className="w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-3 text-lg"
              size="lg"
            >
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.42 1.56-.299.421-1.02.599-1.559.3z"/>
              </svg>
              Connect with Spotify
            </Button>
            
            <p className="text-xs text-gray-400 text-center">
              We'll only access your playlists and basic profile information. 
              No personal data is stored permanently.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 
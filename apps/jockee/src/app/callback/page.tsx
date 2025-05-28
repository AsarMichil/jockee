'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';

export default function CallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const error = searchParams.get('error');

        if (error) {
          setError(`Spotify authorization failed: ${error}`);
          setStatus('error');
          return;
        }

        if (!code || !state) {
          setError('Missing authorization parameters from Spotify');
          setStatus('error');
          return;
        }

        // Call the server callback endpoint with the code and state
        const response = await fetch(`http://localhost:8000/api/v1/auth/spotify/callback?code=${code}&state=${state}`, {
          method: 'GET',
          credentials: 'include', // Important: include cookies for session management
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
          throw new Error(errorData.detail || 'Authentication failed');
        }

        const data = await response.json();
        console.log('Authentication successful:', data);

        setStatus('success');
        
        // Redirect to dashboard after a short delay
        setTimeout(() => {
          router.push('/dashboard');
        }, 2000);

      } catch (err) {
        console.error('Authentication error:', err);
        setError(err instanceof Error ? err.message : 'Failed to authenticate with Spotify. Please try again.');
        setStatus('error');
      }
    };

    handleCallback();
  }, [searchParams, router]);

  const handleRetry = () => {
    router.push('/login');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <div className="w-full max-w-md p-6">
        <Card className="backdrop-blur-sm bg-white/10 border-white/20">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-white">
              {status === 'loading' && 'Connecting to Spotify...'}
              {status === 'success' && 'Successfully Connected!'}
              {status === 'error' && 'Connection Failed'}
            </CardTitle>
            <CardDescription className="text-gray-300">
              {status === 'loading' && 'Please wait while we set up your account'}
              {status === 'success' && 'Redirecting to your dashboard...'}
              {status === 'error' && 'There was a problem connecting your account'}
            </CardDescription>
          </CardHeader>
          
          <CardContent className="text-center">
            {status === 'loading' && (
              <div className="flex justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
              </div>
            )}
            
            {status === 'success' && (
              <div className="text-green-400">
                <svg className="w-16 h-16 mx-auto mb-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                <p className="text-white">Welcome to Auto DJ!</p>
              </div>
            )}
            
            {status === 'error' && (
              <div className="space-y-4">
                <div className="text-red-400">
                  <svg className="w-16 h-16 mx-auto mb-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                  </svg>
                  <p className="text-white mb-2">Connection Error</p>
                  <p className="text-sm text-gray-300 mb-4">{error}</p>
                </div>
                <button
                  onClick={handleRetry}
                  className="w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                >
                  Try Again
                </button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 
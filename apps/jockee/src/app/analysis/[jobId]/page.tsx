'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { analysisApi } from '../../../lib/api/analysis';
import { AnalysisJob } from '../../../lib/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Progress } from '../../../components/ui/progress';

export default function AnalysisPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.jobId as string;
  
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (!jobId) return;

    const fetchJobStatus = async () => {
      try {
        const jobData = await analysisApi.getJobStatus(jobId);
        setJob(jobData);
        
        // If job is completed, redirect to mix page after a short delay
        if (jobData.status === 'completed') {
          setTimeout(() => {
            router.push(`/mix/${jobId}`);
          }, 2000);
        }
      } catch (err) {
        console.error('Failed to fetch job status:', err);
        setError('Failed to load analysis status');
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchJobStatus();

    // Poll for updates if job is still processing
    const interval = setInterval(() => {
      if (job?.status === 'processing' || job?.status === 'pending') {
        fetchJobStatus();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId, router, job?.status]);

  const handleCancel = async () => {
    if (!job) return;
    
    try {
      await analysisApi.cancelJob(job.id);
      router.push('/dashboard');
    } catch (err) {
      console.error('Failed to cancel job:', err);
      setError('Failed to cancel analysis');
    }
  };

  const handleRetry = () => {
    router.push('/dashboard');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">{error || 'Analysis job not found'}</p>
            <Button onClick={handleRetry}>
              Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const progress = job.total_tracks > 0 ? (job.analyzed_tracks / job.total_tracks) * 100 : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold text-gray-900">Analysis Progress</h1>
            <Button variant="outline" onClick={() => router.push('/dashboard')}>
              Back to Dashboard
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* Main Status Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Analyzing: {job.playlist_name}</span>
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                  job.status === 'completed' ? 'bg-green-100 text-green-800' :
                  job.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                  job.status === 'failed' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {job.status === 'completed' ? 'Completed' :
                   job.status === 'processing' ? 'Processing' :
                   job.status === 'failed' ? 'Failed' : 'Pending'}
                </div>
              </CardTitle>
              <CardDescription>
                {job.status === 'completed' && 'Analysis complete! Redirecting to your mix...'}
                {job.status === 'processing' && 'Analyzing tracks and generating mix instructions...'}
                {job.status === 'failed' && 'Analysis failed. Please try again.'}
                {job.status === 'pending' && 'Analysis queued and will start shortly...'}
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-6">
              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Progress</span>
                  <span>{job.analyzed_tracks} / {job.total_tracks} tracks</span>
                </div>
                <Progress value={progress} className="w-full" />
              </div>

              {/* Status Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{job.downloaded_tracks}</div>
                  <div className="text-sm text-gray-600">Downloaded</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{job.analyzed_tracks}</div>
                  <div className="text-sm text-gray-600">Analyzed</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">{job.failed_tracks}</div>
                  <div className="text-sm text-gray-600">Failed</div>
                </div>
              </div>

              {/* Error Message */}
              {job.status === 'failed' && job.error_message && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <h4 className="font-medium text-red-800 mb-2">Error Details</h4>
                  <p className="text-sm text-red-700">{job.error_message}</p>
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-center space-x-4">
                {job.status === 'processing' && (
                  <Button variant="outline" onClick={handleCancel}>
                    Cancel Analysis
                  </Button>
                )}
                
                {job.status === 'failed' && (
                  <Button onClick={handleRetry}>
                    Try Another Playlist
                  </Button>
                )}
                
                {job.status === 'completed' && (
                  <Button onClick={() => router.push(`/mix/${job.id}`)}>
                    View Mix
                  </Button>
                )}
              </div>

              {/* Processing Animation */}
              {job.status === 'processing' && (
                <div className="flex justify-center">
                  <div className="flex space-x-2">
                    <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce"></div>
                    <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Tips Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">While You Wait...</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm text-gray-600">
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <p>Our AI analyzes each track's BPM, key, and energy level to create perfect transitions</p>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <p>Tracks are downloaded from YouTube for the best audio quality</p>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <p>Mix instructions include crossfade timing and BPM adjustments</p>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <p>Analysis typically takes 1-2 minutes per track</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
} 
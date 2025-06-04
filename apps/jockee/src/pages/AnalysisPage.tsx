import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { analysisApi } from '../lib/api/analysis';
import { AnalysisJob } from '../lib/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';

export default function AnalysisPage() {
  const navigate = useNavigate();
  const { jobId } = useParams<{ jobId: string }>();
  
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
            navigate(`/mix/${jobId}`);
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
  }, [jobId, navigate, job?.status]);

  const handleCancel = async () => {
    if (!job) return;
    
    try {
      await analysisApi.cancelJob(job.id);
      navigate('/dashboard');
    } catch (err) {
      console.error('Failed to cancel job:', err);
      setError('Failed to cancel analysis');
    }
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
            <p className="text-gray-600 mb-4">{error || 'Job not found'}</p>
            <Button onClick={() => navigate('/dashboard')}>Back to Dashboard</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold text-gray-900">Analysis Progress</h1>
            <Button variant="outline" onClick={() => navigate('/dashboard')}>
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
            <CardContent>
              <div className="space-y-4">
                {/* Progress Bar */}
                {job.status === 'processing' && (
                  <div>
                    <div className="flex justify-between text-sm text-gray-600 mb-2">
                      <span>Progress</span>
                      <span>{Math.round((job.analyzed_tracks / job.total_tracks) * 100)}%</span>
                    </div>
                    <Progress 
                      value={(job.analyzed_tracks / job.total_tracks) * 100} 
                      className="w-full"
                    />
                    <p className="text-sm text-gray-500 mt-2">
                      {job.analyzed_tracks} of {job.total_tracks} tracks processed
                    </p>
                  </div>
                )}

                {/* Track Count */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Total Tracks:</span>
                    <span className="ml-2 font-medium">{job.total_tracks}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Processed:</span>
                    <span className="ml-2 font-medium">{job.analyzed_tracks}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-4">
                  {job.status === 'processing' || job.status === 'pending' ? (
                    <Button variant="destructive" onClick={handleCancel}>
                      Cancel Analysis
                    </Button>
                  ) : job.status === 'completed' ? (
                    <Button onClick={() => navigate(`/mix/${job.id}`)}>
                      View Mix
                    </Button>
                  ) : job.status === 'failed' ? (
                    <Button onClick={() => navigate('/dashboard')}>
                      Back to Dashboard
                    </Button>
                  ) : null}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Analysis Details */}
          <Card>
            <CardHeader>
              <CardTitle>Job Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Job ID:</span>
                  <span className="font-mono">{job.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Created:</span>
                  <span>{new Date(job.created_at).toLocaleString()}</span>
                </div>
                {job.completed_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Completed:</span>
                    <span>{new Date(job.completed_at).toLocaleString()}</span>
                  </div>
                )}
                {job.error_message && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
                    <span className="text-red-600 font-medium">Error:</span>
                    <p className="text-red-700 mt-1">{job.error_message}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
} 
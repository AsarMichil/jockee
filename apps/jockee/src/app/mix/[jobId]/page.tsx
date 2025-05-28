"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { analysisApi } from "../../../lib/api/analysis";
import { MixInstructions, AnalysisJob } from "../../../lib/types";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "../../../components/ui/card";
import { Button } from "../../../components/ui/button";
import { Slider } from "../../../components/ui/slider";
import {
  formatDuration,
  getBpmColor,
  getEnergyColor,
  getCompatibilityColor
} from "../../../lib/utils";
import { useAudioPlayer } from "../../../hooks/useAudioPlayer";
import { AudioVisualizer } from "../../../components/AudioVisualizer";
import { TrackProgress } from "../../../components/TrackProgress";
import { useKeyboardShortcuts } from "../../../hooks/useKeyboardShortcuts";

export default function MixPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.jobId as string;

  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [mixInstructions, setMixInstructions] =
    useState<MixInstructions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [showShortcuts, setShowShortcuts] = useState(false);

  // Use the audio player hook
  const {
    isLoading: audioLoading,
    loadingProgress,
    error: audioError,
    isAudioInitialized,
    handlePlayPause,
    handleSeek,
    handleVolumeChange,
    isPlaying,
    currentTime,
    duration,
    volume,
  } = useAudioPlayer({ mixInstructions, jobId });

  // Add keyboard shortcuts
  useKeyboardShortcuts({
    onPlayPause: handlePlayPause,
    onSeek: handleSeek,
    currentTime,
    duration: duration || mixInstructions?.total_duration || 0,
    isLoading: audioLoading || !isAudioInitialized,
  });

  // Memoize slider values to prevent infinite re-renders
  const progressSliderValue = useMemo(() => [currentTime], [currentTime]);
  const volumeSliderValue = useMemo(() => [volume * 100], [volume]);
  const maxDuration = useMemo(() => duration || mixInstructions?.total_duration || 0, [duration, mixInstructions?.total_duration]);

  // Memoize slider handlers
  const handleSeekChange = useCallback((value: number[]) => {
    handleSeek(value[0]);
  }, [handleSeek]);

  const handleVolumeSliderChange = useCallback((value: number[]) => {
    handleVolumeChange(value[0]);
  }, [handleVolumeChange]);

  // Close shortcuts tooltip when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showShortcuts && !(event.target as Element).closest('.shortcuts-tooltip')) {
        setShowShortcuts(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showShortcuts]);

  useEffect(() => {
    if (!jobId) return;

    const fetchMixData = async () => {
      try {
        const jobData = await analysisApi.getJobStatus(jobId);
        setJob(jobData);

        if (jobData.status === "completed") {
          const mixData = await analysisApi.getMixInstructions(jobId);
          setMixInstructions(mixData);
        }
      } catch (err) {
        console.error("Failed to fetch mix data:", err);
        setError("Failed to load mix data");
      } finally {
        setLoading(false);
      }
    };

    fetchMixData();
  }, [jobId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !job || !mixInstructions) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">
              {error || "Mix not found or not ready"}
            </p>
            <Button onClick={() => router.push("/dashboard")}>
              Back to Dashboard
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
            <h1 className="text-2xl font-bold text-gray-900">Mix Player</h1>
            <div className="flex items-center space-x-2">
              {/* Keyboard Shortcuts Help */}
              <div className="relative">
                <Button 
                  variant="ghost" 
                  size="icon"
                  onClick={() => setShowShortcuts(!showShortcuts)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M11 17h2v-6h-2v6zm1-15C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15h2v-2h-2v2zm0-4h2V8h-2v5z"/>
                  </svg>
                </Button>
                
                {showShortcuts && (
                  <div className="shortcuts-tooltip absolute right-0 top-full mt-2 w-64 bg-white rounded-lg shadow-lg border p-4 z-10">
                    <h3 className="font-medium text-gray-900 mb-2">Keyboard Shortcuts</h3>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Play/Pause</span>
                        <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">Space</kbd>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Seek ±10s</span>
                        <div className="space-x-1">
                          <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">←</kbd>
                          <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">→</kbd>
                        </div>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Seek ±30s</span>
                        <div className="space-x-1">
                          <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">↑</kbd>
                          <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">↓</kbd>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              <Button variant="outline" onClick={() => router.push("/dashboard")}>
                Back to Dashboard
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* Mix Info */}
          <Card>
            <CardHeader>
              <CardTitle>{job.playlist_name}</CardTitle>
              <CardDescription>
                {mixInstructions.metadata.track_count} tracks •{" "}
                {formatDuration(mixInstructions.total_duration)} •{" "}
                {mixInstructions.metadata.transition_count} transitions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Avg BPM</p>
                  <p
                    className={`font-semibold ${getBpmColor(
                      mixInstructions.metadata.avg_bpm
                    )}`}
                  >
                    {Math.round(mixInstructions.metadata.avg_bpm)}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Avg Energy</p>
                  <p
                    className={`font-semibold ${getEnergyColor(
                      mixInstructions.metadata.avg_energy
                    )}`}
                  >
                    {(mixInstructions.metadata.avg_energy * 100).toFixed(0)}%
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Compatibility</p>
                  <p
                    className={`font-semibold ${getCompatibilityColor(
                      mixInstructions.metadata.avg_compatibility
                    )}`}
                  >
                    {(mixInstructions.metadata.avg_compatibility * 100).toFixed(
                      0
                    )}
                    %
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Keys Used</p>
                  <p className="font-semibold">
                    {mixInstructions.metadata.keys_used.length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Audio Loading State */}
          {(audioLoading || !isAudioInitialized) && (
            <Card>
              <CardContent className="p-6">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  {!isAudioInitialized ? (
                    <p className="text-gray-600 mb-2">Initializing audio system...</p>
                  ) : (
                    <>
                      <p className="text-gray-600 mb-2">Loading audio tracks...</p>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${loadingProgress}%` }}
                        ></div>
                      </div>
                      <p className="text-sm text-gray-500 mt-2">
                        {Math.round(loadingProgress)}% complete
                      </p>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Audio Error */}
          {audioError && (
            <Card>
              <CardContent className="p-6">
                <div className="text-center text-red-600">
                  <p className="font-medium">Audio Error</p>
                  <p className="text-sm">{audioError}</p>
                  {!isAudioInitialized && (
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="mt-2"
                      onClick={() => window.location.reload()}
                    >
                      Retry
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Audio Player */}
          <Card>
            <CardContent className="p-6">
              {/* Progress Bar */}
              <div className="mb-4">
                <Slider
                  value={progressSliderValue}
                  max={maxDuration}
                  step={0.1}
                  onValueChange={handleSeekChange}
                  className="w-full"
                  disabled={audioLoading || !isAudioInitialized}
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>{formatDuration(currentTime)}</span>
                  <span>{formatDuration(duration || mixInstructions.total_duration)}</span>
                </div>
              </div>

              {/* Controls */}
              <div className="flex items-center justify-center space-x-4 mb-4">
                <Button variant="ghost" size="icon" disabled={audioLoading || !isAudioInitialized}>
                  <svg
                    className="w-4 h-4"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z" />
                  </svg>
                </Button>

                <Button
                  variant="default"
                  size="icon"
                  onClick={handlePlayPause}
                  className="w-12 h-12"
                  disabled={audioLoading || !isAudioInitialized}
                >
                  {isPlaying ? (
                    <svg
                      className="w-6 h-6"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                    </svg>
                  ) : (
                    <svg
                      className="w-6 h-6"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  )}
                </Button>

                <Button variant="ghost" size="icon" disabled={audioLoading || !isAudioInitialized}>
                  <svg
                    className="w-4 h-4"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z" />
                  </svg>
                </Button>
              </div>

              {/* Audio Visualizer */}
              <div className="flex justify-center mb-4">
                <AudioVisualizer isPlaying={isPlaying && isAudioInitialized} />
              </div>

              {/* Volume Control */}
              <div className="flex items-center space-x-2">
                <svg
                  className="w-4 h-4 text-gray-500"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
                </svg>
                <Slider
                  value={volumeSliderValue}
                  max={100}
                  step={1}
                  onValueChange={handleVolumeSliderChange}
                  className="w-24"
                  disabled={audioLoading || !isAudioInitialized}
                />
                <span className="text-xs text-gray-500 w-8">
                  {Math.round(volume * 100)}%
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Track Progress */}
          <TrackProgress 
            mixInstructions={mixInstructions}
            currentTime={currentTime}
          />

          {/* Transitions List */}
          <Card>
            <CardHeader>
              <CardTitle>Transitions</CardTitle>
              <CardDescription>
                AI-generated crossfade points and techniques
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mixInstructions.transitions.map((transition, index) => (
                  <div key={transition.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <h4 className="font-medium">
                          {transition.track_a.title} →{" "}
                          {transition.track_b.title}
                        </h4>
                        <p className="text-sm text-gray-500">
                          {transition.track_a.artist} →{" "}
                          {transition.track_b.artist}
                        </p>
                      </div>
                      <div
                        className={`px-2 py-1 rounded text-xs font-medium ${getCompatibilityColor(
                          transition.overall_score
                        )}`}
                      >
                        {(transition.overall_score * 100).toFixed(0)}% match
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                      <div>
                        <p className="text-gray-500">Technique</p>
                        <p className="font-medium">{transition.technique}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Duration</p>
                        <p className="font-medium">
                          {transition.transition_duration.toFixed(1)}s
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500">BPM Adjust</p>
                        <p className="font-medium">
                          {transition.bpm_adjustment > 0 ? "+" : ""}
                          {transition.bpm_adjustment.toFixed(1)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500">Start Time</p>
                        <p className="font-medium">
                          {formatDuration(transition.transition_start)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
 
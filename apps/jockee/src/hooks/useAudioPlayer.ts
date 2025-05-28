import { useEffect, useRef, useState, useCallback } from "react";
import { useAudioStore } from "../stores/audioStore";
import { AudioContextManager } from "../lib/audio/AudioContextManager";
import { MixScheduler, AudioTrack } from "../lib/audio/MixScheduler";
import { analysisApi } from "../lib/api/analysis";
import { MixInstructions } from "../lib/types";

interface UseAudioPlayerProps {
  mixInstructions: MixInstructions | null;
  jobId: string;
}

export const useAudioPlayer = ({
  mixInstructions,
  jobId
}: UseAudioPlayerProps) => {
  const audioStore = useAudioStore();
  const mixSchedulerRef = useRef<MixScheduler | null>(null);
  const audioManagerRef = useRef<AudioContextManager | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const audioTracksRef = useRef<Map<string, AudioTrack>>(new Map());

  const [isLoading, setIsLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [error, setError] = useState<string>("");
  const [isAudioInitialized, setIsAudioInitialized] = useState(false);

  // Initialize audio system
  useEffect(() => {
    const initializeAudio = async () => {
      try {
        setIsAudioInitialized(false);
        audioManagerRef.current = AudioContextManager.getInstance();
        await audioManagerRef.current.initialize();

        mixSchedulerRef.current = new MixScheduler();
        await mixSchedulerRef.current.initialize();

        setIsAudioInitialized(true);
      } catch (err) {
        console.error("Failed to initialize audio:", err);
        setError("Failed to initialize audio system");
        setIsAudioInitialized(false);
      }
    };

    initializeAudio();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (mixSchedulerRef.current) {
        mixSchedulerRef.current.stop();
      }
    };
  }, []);

  // Ensure audio system is initialized before use
  const ensureAudioInitialized = useCallback(async (): Promise<boolean> => {
    if (!isAudioInitialized || !mixSchedulerRef.current) {
      try {
        setError("");
        audioManagerRef.current = AudioContextManager.getInstance();
        await audioManagerRef.current.initialize();

        mixSchedulerRef.current = new MixScheduler();
        await mixSchedulerRef.current.initialize();

        setIsAudioInitialized(true);
        return true;
      } catch (err) {
        console.error("Failed to initialize audio:", err);
        setError("Failed to initialize audio system");
        setIsAudioInitialized(false);
        return false;
      }
    }
    return true;
  }, [isAudioInitialized]);

  // Load audio tracks
  const loadAudioTracks = useCallback(async () => {
    if (!mixInstructions || !mixSchedulerRef.current) return;

    setIsLoading(true);
    setLoadingProgress(0);
    setError("");

    try {
      const tracks = mixInstructions.transitions.flatMap((t) => [
        t.track_a,
        t.track_b
      ]);
      const uniqueTracks = tracks.filter(
        (track, index, self) =>
          index === self.findIndex((t) => t.id === track.id)
      );

      const totalTracks = uniqueTracks.length;
      let loadedTracks = 0;

      for (const track of uniqueTracks) {
        try {
          // Get audio URL from API
          const { url } = await analysisApi.getTrackAudioUrl(track.id);

          // Load audio buffer
          const buffer = await mixSchedulerRef.current!.loadAudioBuffer(url);

          // Store in cache
          audioTracksRef.current.set(track.id, {
            buffer,
            track
          });

          loadedTracks++;
          setLoadingProgress((loadedTracks / totalTracks) * 100);
        } catch (err) {
          console.error(`Failed to load track ${track.title}:`, err);
          // Continue loading other tracks
        }
      }

      setIsLoading(false);
    } catch (err) {
      console.error("Failed to load audio tracks:", err);
      setError("Failed to load audio tracks");
      setIsLoading(false);
    }
  }, [mixInstructions]);

  // Update current time - fixed to prevent infinite re-renders
  const updateCurrentTime = useCallback(() => {
    if (mixSchedulerRef.current) {
      const store = useAudioStore.getState();
      if (store.isPlaying) {
        const currentTime = mixSchedulerRef.current.getCurrentTime();
        store.setCurrentTime(currentTime);

        // Check if we need to trigger a transition
        // Get mixInstructions from the current scope instead of stale closure
        const currentMixInstructions = mixInstructions;
        if (currentMixInstructions) {
          checkAndTriggerTransitions(currentTime);
        }

        animationFrameRef.current = requestAnimationFrame(updateCurrentTime);
      }
    }
  }, [mixInstructions]); // Include mixInstructions dependency

  // Check and trigger transitions based on current time
  const checkAndTriggerTransitions = useCallback(
    (currentTime: number) => {
      if (!mixInstructions || !mixSchedulerRef.current) return;

      // Debug: Log current time and transition data every few seconds
      if (Math.floor(currentTime) % 5 === 0 && currentTime % 1 < 0.1) {
        console.log("=== TRANSITION DEBUG ===");
        console.log("Current time:", currentTime);
        console.log("Total transitions:", mixInstructions.transitions.length);

        // Calculate absolute timeline positions for debugging
        let absoluteTime = 0;
        mixInstructions.transitions.forEach((t, i) => {
          const absoluteTransitionStart = absoluteTime + t.transition_start;
          const absoluteTransitionEnd =
            absoluteTransitionStart + t.transition_duration;
          console.log(
            `Transition ${i}: ${t.track_a.title} -> ${t.track_b.title}`
          );
          console.log(
            `  Relative start: ${t.transition_start}, Duration: ${t.transition_duration}`
          );
          console.log(
            `  Absolute start: ${absoluteTransitionStart}, Absolute end: ${absoluteTransitionEnd}`
          );
          console.log(`  BPM adjustment: ${t.bpm_adjustment}%`);

          // Update absolute time for next transition
          if (i === 0) {
            absoluteTime = absoluteTransitionStart + t.transition_duration;
          } else {
            absoluteTime = absoluteTransitionEnd;
          }
        });
        console.log("========================");
      }

      // Calculate absolute timeline positions and check for transitions
      let absoluteTime = 0;

      for (let i = 0; i < mixInstructions.transitions.length; i++) {
        const transition = mixInstructions.transitions[i];
        const absoluteTransitionStart =
          absoluteTime + transition.transition_start;
        const absoluteTransitionEnd =
          absoluteTransitionStart + transition.transition_duration;

        // Check if we're at the start of this transition
        if (
          currentTime >= absoluteTransitionStart &&
          currentTime <= absoluteTransitionEnd
        ) {
          console.log("🎵 TRANSITION DETECTED!", {
            currentTime,
            absoluteTransitionStart,
            absoluteTransitionEnd,
            trackA: transition.track_a.title,
            trackB: transition.track_b.title,
            bpmAdjustment: transition.bpm_adjustment
          });

          const trackB = audioTracksRef.current.get(transition.track_b.id);
          if (trackB) {
            // Calculate crossfade progress (0 to 1)
            const progress =
              (currentTime - absoluteTransitionStart) /
              transition.transition_duration;

            // Calculate gradual BPM adjustment based on progress
            const gradualBpmAdjustment = transition.bpm_adjustment * progress;

            console.log(
              "Crossfade progress:",
              progress,
              "Gradual BPM adjustment:",
              gradualBpmAdjustment,
              "Track B loaded:",
              !!trackB
            );

            // Start playing track B if not already playing
            if (
              !mixSchedulerRef.current.isTrackPlaying(transition.track_b.id)
            ) {
              console.log("🚀 STARTING TRANSITION:", {
                trackAId: transition.track_a.id,
                trackBId: transition.track_b.id,
                technique: transition.technique,
                bpmAdjustment: transition.bpm_adjustment
              });

              // Track B starts from the beginning during transition
              const trackBStartTime = 0;
              mixSchedulerRef.current.startTransition(
                transition.track_a.id,
                trackB,
                trackBStartTime,
                transition.transition_duration,
                transition.technique,
                0 // Start with no BPM adjustment, will be applied gradually
              );
            }

            // Apply gradual BPM adjustment to track A
            mixSchedulerRef.current.setBpmAdjustment(
              transition.track_a.id,
              gradualBpmAdjustment
            );

            // Update crossfade position
            mixSchedulerRef.current.setCrossfadeProgress(progress);
          } else {
            console.error(
              "❌ Track B not found in cache:",
              transition.track_b.id
            );
          }
          break; // Only handle one transition at a time
        }

        // Update absolute time for next transition
        if (i === 0) {
          // First transition: time advances to start of transition + transition duration
          absoluteTime =
            absoluteTransitionStart + transition.transition_duration;
        } else {
          // Subsequent transitions: time advances to end of this transition
          absoluteTime = absoluteTransitionEnd;
        }
      }
    },
    [mixInstructions]
  );

  // Play/pause functionality
  const handlePlayPause = useCallback(async () => {
    console.log("handlePlayPause", mixSchedulerRef.current, mixInstructions);

    // Ensure audio is initialized first
    const audioReady = await ensureAudioInitialized();
    if (!audioReady || !mixSchedulerRef.current || !mixInstructions) {
      console.log("Audio not ready:", {
        audioReady,
        scheduler: !!mixSchedulerRef.current,
        instructions: !!mixInstructions
      });
      return;
    }

    try {
      const store = useAudioStore.getState();

      if (store.isPlaying) {
        // Pause
        mixSchedulerRef.current.pause();
        store.pausePlayback();

        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
          animationFrameRef.current = null;
        }
      } else {
        // Resume audio context if needed
        await audioManagerRef.current?.resume();

        // If no tracks loaded, load them first
        if (audioTracksRef.current.size === 0) {
          await loadAudioTracks();
        }

        // Start playback from current time
        await startPlaybackFromTime(store.currentTime);
        store.resumePlayback();

        // Start time updates
        animationFrameRef.current = requestAnimationFrame(updateCurrentTime);
      }
    } catch (err) {
      console.error("Playback error:", err);
      setError("Playback failed");
    }
  }, [
    mixInstructions,
    loadAudioTracks,
    updateCurrentTime,
    ensureAudioInitialized
  ]);

  // Start playback from a specific time, handling transitions
  const startPlaybackFromTime = useCallback(
    async (time: number) => {
      if (!mixSchedulerRef.current || !mixInstructions) return;

      console.log("🎬 Starting playback from time:", time);
      console.log("Available transitions:", mixInstructions.transitions.length);

      // Find which track(s) should be playing at this time using absolute timeline
      let currentTrackA: AudioTrack | null = null;
      let currentTrackB: AudioTrack | null = null;
      let trackAOffset = 0;
      let trackBOffset = 0;
      let crossfadeProgress = 0;
      let bpmAdjustment = 0;
      let absoluteTime = 0;

      // Find the current position in the mix using absolute timeline
      for (let i = 0; i < mixInstructions.transitions.length; i++) {
        const transition = mixInstructions.transitions[i];
        const absoluteTransitionStart =
          absoluteTime + transition.transition_start;
        const absoluteTransitionEnd =
          absoluteTransitionStart + transition.transition_duration;

        console.log(
          `Checking transition ${i}: absolute start=${absoluteTransitionStart}, absolute end=${absoluteTransitionEnd}, time=${time}`
        );

        if (time < absoluteTransitionStart) {
          // We're in track A before transition
          currentTrackA =
            audioTracksRef.current.get(transition.track_a.id) || null;
          trackAOffset = time - absoluteTime;
          console.log(
            `📀 Selected track A: ${transition.track_a.title} (offset: ${trackAOffset})`
          );
          break;
        } else if (
          time >= absoluteTransitionStart &&
          time <= absoluteTransitionEnd
        ) {
          // We're in a transition
          currentTrackA =
            audioTracksRef.current.get(transition.track_a.id) || null;
          currentTrackB =
            audioTracksRef.current.get(transition.track_b.id) || null;

          trackAOffset = time - absoluteTime;
          // Track B starts from beginning during transition, offset by how far into transition we are
          trackBOffset = time - absoluteTransitionStart;
          crossfadeProgress =
            (time - absoluteTransitionStart) / transition.transition_duration;
          bpmAdjustment = transition.bpm_adjustment; // Get BPM adjustment for this transition
          console.log(
            "🔄 In transition - track A:",
            transition.track_a.title,
            "track B:",
            transition.track_b.title
          );
          console.log(
            "Seeking to transition position, BPM adjustment:",
            bpmAdjustment
          );
          break;
        } else if (i === mixInstructions.transitions.length - 1) {
          // We're in the final track B after all transitions
          currentTrackA =
            audioTracksRef.current.get(transition.track_b.id) || null;
          // Calculate how far into track B we are after the last transition
          trackAOffset = time - absoluteTransitionStart;
          console.log(
            `📀 Selected final track B: ${transition.track_b.title} (offset: ${trackAOffset})`
          );
          break;
        }

        // Update absolute time for next transition
        if (i === 0) {
          // First transition: time advances to start of transition + transition duration
          absoluteTime =
            absoluteTransitionStart + transition.transition_duration;
        } else {
          // Subsequent transitions: time advances to end of this transition
          absoluteTime = absoluteTransitionEnd;
        }
      }

      // Start playback
      if (currentTrackA) {
        // Apply gradual BPM adjustment to track A if we're in a transition
        const trackABpmAdjustment = currentTrackB
          ? bpmAdjustment * crossfadeProgress
          : 0;
        console.log(
          "🎵 Starting track A:",
          currentTrackA.track.title,
          "with gradual BPM adjustment:",
          trackABpmAdjustment
        );
        await mixSchedulerRef.current.playTrack(
          currentTrackA,
          trackAOffset,
          trackABpmAdjustment
        );

        if (currentTrackB) {
          // We're in a transition, start track B at natural tempo
          console.log(
            "🎵 Starting track B:",
            currentTrackB.track.title,
            "at natural tempo"
          );
          await mixSchedulerRef.current.playSecondTrack(
            currentTrackB,
            trackBOffset,
            0 // Track B plays at natural tempo
          );
          mixSchedulerRef.current.setCrossfadeProgress(crossfadeProgress);
          console.log(
            "Started transition playback - track A with gradual BPM adjustment:",
            trackABpmAdjustment,
            "track B at natural tempo"
          );
        }
      } else {
        console.error("❌ No track found to play at time:", time);
      }
    },
    [mixInstructions]
  );

  // Seek functionality
  const handleSeek = useCallback(
    async (time: number) => {
      // Ensure audio is initialized first
      const audioReady = await ensureAudioInitialized();
      if (!audioReady || !mixSchedulerRef.current || !mixInstructions) return;

      try {
        const store = useAudioStore.getState();
        store.setCurrentTime(time);

        if (store.isPlaying) {
          // Stop current playback
          mixSchedulerRef.current.stop();

          // Start playback from new time
          await startPlaybackFromTime(time);
        }
      } catch (err) {
        console.error("Seek error:", err);
        setError("Seek failed");
      }
    },
    [mixInstructions, startPlaybackFromTime, ensureAudioInitialized]
  );

  // Volume control
  const handleVolumeChange = useCallback(
    async (volume: number) => {
      const store = useAudioStore.getState();
      store.setVolume(volume / 100);

      // Ensure audio is initialized before setting volume
      const audioReady = await ensureAudioInitialized();
      if (audioReady && mixSchedulerRef.current) {
        mixSchedulerRef.current.setVolume(volume / 100);
      }
    },
    [ensureAudioInitialized]
  );

  // Crossfader control
  const handleCrossfaderChange = useCallback(
    async (position: number) => {
      const store = useAudioStore.getState();
      store.setCrossfaderPosition(position);

      // Ensure audio is initialized before setting crossfader
      const audioReady = await ensureAudioInitialized();
      if (audioReady && mixSchedulerRef.current) {
        mixSchedulerRef.current.setCrossfaderPosition(position);
      }
    },
    [ensureAudioInitialized]
  );

  // Auto-load tracks when mix instructions are available
  useEffect(() => {
    if (
      mixInstructions &&
      audioTracksRef.current.size === 0 &&
      isAudioInitialized
    ) {
      loadAudioTracks();
    }
  }, [mixInstructions, loadAudioTracks, isAudioInitialized]);

  // Set total duration when mix instructions are loaded
  useEffect(() => {
    if (mixInstructions) {
      const store = useAudioStore.getState();
      store.setDuration(mixInstructions.total_duration);
    }
  }, [mixInstructions]);

  return {
    // State
    isLoading,
    loadingProgress,
    error,
    isAudioInitialized,

    // Actions
    handlePlayPause,
    handleSeek,
    handleVolumeChange,
    handleCrossfaderChange,
    loadAudioTracks,

    // Audio store state
    isPlaying: audioStore.isPlaying,
    currentTime: audioStore.currentTime,
    duration: audioStore.duration,
    volume: audioStore.volume,
    crossfaderPosition: audioStore.crossfaderPosition
  };
};

import { create } from 'zustand';
import { AudioState, PlaybackState, Track, Transition } from '../lib/types';

interface AudioStore extends AudioState, PlaybackState {
  // Actions
  setIsPlaying: (isPlaying: boolean) => void;
  setCurrentTime: (time: number) => void;
  setDuration: (duration: number) => void;
  setCurrentTrackIndex: (index: number) => void;
  setVolume: (volume: number) => void;
  setCrossfaderPosition: (position: number) => void;
  setCurrentTrack: (track: Track | null) => void;
  setNextTrack: (track: Track | null) => void;
  setIsTransitioning: (isTransitioning: boolean) => void;
  setTransitionProgress: (progress: number) => void;
  
  // Complex actions
  playTrack: (track: Track, index: number) => void;
  pausePlayback: () => void;
  resumePlayback: () => void;
  stopPlayback: () => void;
  seekTo: (time: number) => void;
  goToNextTrack: () => void;
  goToPreviousTrack: () => void;
}

export const useAudioStore = create<AudioStore>((set, get) => ({
  // Initial state
  isPlaying: false,
  currentTime: 0,
  duration: 0,
  currentTrackIndex: 0,
  volume: 0.8,
  crossfaderPosition: 0,
  currentTrack: null,
  nextTrack: null,
  isTransitioning: false,
  transitionProgress: 0,

  // Basic setters
  setIsPlaying: (isPlaying) => set({ isPlaying }),
  setCurrentTime: (currentTime) => set({ currentTime }),
  setDuration: (duration) => set({ duration }),
  setCurrentTrackIndex: (currentTrackIndex) => set({ currentTrackIndex }),
  setVolume: (volume) => set({ volume }),
  setCrossfaderPosition: (crossfaderPosition) => set({ crossfaderPosition }),
  setCurrentTrack: (currentTrack) => set({ currentTrack }),
  setNextTrack: (nextTrack) => set({ nextTrack }),
  setIsTransitioning: (isTransitioning) => set({ isTransitioning }),
  setTransitionProgress: (transitionProgress) => set({ transitionProgress }),

  // Complex actions
  playTrack: (track, index) => {
    set({
      currentTrack: track,
      currentTrackIndex: index,
      isPlaying: true,
      currentTime: 0,
      duration: track.duration,
    });
  },

  pausePlayback: () => {
    set({ isPlaying: false });
  },

  resumePlayback: () => {
    set({ isPlaying: true });
  },

  stopPlayback: () => {
    set({
      isPlaying: false,
      currentTime: 0,
      currentTrack: null,
      nextTrack: null,
      isTransitioning: false,
      transitionProgress: 0,
    });
  },

  seekTo: (time) => {
    set({ currentTime: time });
  },

  goToNextTrack: () => {
    const { currentTrackIndex } = get();
    set({
      currentTrackIndex: currentTrackIndex + 1,
      currentTime: 0,
    });
  },

  goToPreviousTrack: () => {
    const { currentTrackIndex } = get();
    if (currentTrackIndex > 0) {
      set({
        currentTrackIndex: currentTrackIndex - 1,
        currentTime: 0,
      });
    }
  },
})); 
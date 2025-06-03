import { createStore } from "zustand/vanilla";
import { AudioContextManager } from "./AudioContextManager";
import { analysisApi } from "../api/analysis";

export interface Track {
  id: string;
  spotify_id: string;
  title: string;
  artist: string;
  duration: number;
  file_source: "local" | "youtube" | "unavailable";
  bpm: number;
  key: string;
  energy: number;
  
  // Beat analysis fields for beat matching
  beat_timestamps?: number[];
  beat_intervals?: number[];
  beat_confidence?: number;
  beat_confidence_scores?: number[];
  beat_regularity?: number;
  average_beat_interval?: number;
  
  // Additional audio analysis fields
  danceability?: number;
  valence?: number;
  acousticness?: number;
  instrumentalness?: number;
  liveness?: number;
  speechiness?: number;
  loudness?: number;
}

export interface DeckState {
  track: Track | null;
  audioElement: HTMLAudioElement | null;
  isLoading: boolean;
  isLoaded: boolean;
  cuePoint: number;
  isAnimating: boolean;
}

/**
 * QueueState - Simple queue management for dual-deck system
 * Basic track queue without complex mixing logic
 */
export interface QueueState {
  /** Main track queue */
  queue: Track[];
  /** Current queue position */
  currentIndex: number;
  /** Queue playback mode */
  playbackMode: "sequential" | "shuffle" | "repeat";
  /** History of played tracks */
  playHistory: Track[];
}

interface AudioPlayerStoreState {
  masterVolume: number;
  audioContextManager: AudioContextManager | null;
  audioContext: AudioContext | null; // probably dont use this
  tracks: Track[];

  // Deck States
  deckA: DeckState | null;
  deckB: DeckState | null;
  autoplay: boolean;

  /** Queue management state */
  queue: QueueState;
}

export type AudioPlayerStoreActions = {
  setDeckA: (deckA: DeckState) => void; // probably avoid using these directly
  setDeckB: (deckB: DeckState) => void; // probably avoid using these directly

  // Load track onto deck
  loadTrack: (track: Track, deck: "deckA" | "deckB") => Promise<void>;
  playDeck: (deck: "deckA" | "deckB", trackId: string, offset?: number) => void;
  scrubDeck: (deck: "deckA" | "deckB", position: number) => void;
  pauseDeck: (deck: "deckA" | "deckB") => void;
  setDeckVolume: (deck: "deckA" | "deckB", volume: number) => void;
  setDeckBpm: (deck: "deckA" | "deckB", bpm: number) => void;

  setMasterVolume: (volume: number) => void;

  // Queue actions
  setQueuedTracks: (tracks: Track[]) => void;
  advanceQueue: () => void;
  autoplayNextTrack: (deck: "deckA" | "deckB") => Promise<void>;

  recalculateDeckPosition: (deck: "deckA" | "deckB") => void;
};

export type AudioPlayerStore = AudioPlayerStoreState & AudioPlayerStoreActions;

// === DEFAULT INITIAL STATES ===

const defaultQueueState: QueueState = {
  queue: [],
  currentIndex: 0,
  playbackMode: "sequential",
  playHistory: []
};

export const defaultInitState: AudioPlayerStoreState = {
  masterVolume: 0.8,
  audioContextManager: null,
  audioContext: null,
  deckA: null,
  deckB: null,
  tracks: [],
  queue: defaultQueueState,
  autoplay: true
};

export const initializeAudioStore =
  async (): Promise<AudioPlayerStoreState> => {
    if (typeof window === "undefined") {
      return defaultInitState;
    }
    const audioContextManager = AudioContextManager.getInstance();
    const audioContext = await audioContextManager.initialize();
    return {
      ...defaultInitState,
      audioContextManager,
      audioContext
    };
  };

export const createAudioPlayerStore = (
  initState: Promise<AudioPlayerStoreState>
) => {
  const store = createStore<AudioPlayerStore>()((set, get) => ({
    ...defaultInitState,
    setDeckA: (deckA: DeckState) => set({ deckA }),
    setDeckB: (deckB: DeckState) => set({ deckB }),

    setMasterVolume: (volume: number) => {
      set(() => ({ masterVolume: volume }));
      // Also update the actual audio context master volume
      const { audioContextManager } = get();
      if (audioContextManager) {
        audioContextManager.setMasterVolume(volume);
      }
    },

    // Queue actions
    setQueuedTracks: (tracks: Track[]) =>
      set((state) => ({ queue: { ...state.queue, queue: tracks } })),
    advanceQueue: () =>
      set((state) => ({
        queue: {
          ...state.queue,
          currentIndex: Math.min(
            state.queue.currentIndex + 1,
            state.queue.queue.length - 1
          )
        }
      })),

    // === ENHANCED DECK MANAGEMENT ===
    loadTrack: async (track: Track, deck: "deckA" | "deckB") => {
      console.log("loadTrack", track, deck);
      try {
        const deckState = get()[deck];
        if (deckState?.isLoading) {
          console.log(`Track "${track.title}" is already loading`);
          return;
        }
        if (deckState?.track?.id === track.id) {
          console.log(`Track "${track.title}" is already loaded onto ${deck}`);
          return;
        }

        // Clean up old audio element
        if (deckState?.audioElement) {
          deckState.audioElement.pause();
          deckState.audioElement.src = "";
          deckState.audioElement.load();
        }

        // Set loading state
        set(() => ({
          [deck]: {
            ...deckState,
            isLoading: true,
            isLoaded: false,
            audioElement: null
          }
        }));

        const newDeckState = await loadTrack(track);
        set(() => ({ [deck]: newDeckState }));
        console.log(`Track "${track.title}" loaded onto ${deck}`);
      } catch (error) {
        console.error(`Failed to load track onto ${deck}:`, error);
        // Set error state on deck
        set((state) => ({
          ...state,
          [deck]: {
            ...state[deck],
            track,
            isLoaded: false,
            audioElement: null,
            isLoading: false
          }
        }));
        throw error;
      }
    },

    scrubDeck: (deck: "deckA" | "deckB", position: number) => {
      const deckState = get()[deck];
      console.log("scrubDeck", deck, position);
      if (!deckState?.audioElement) {
        console.log(`Deck ${deck} audio element not found`);
        return;
      }

      // Set the audio element's current time directly
      deckState.audioElement.currentTime = position;
    },

    autoplayNextTrack: async (deck: "deckA" | "deckB") => {
      console.log("autoplayNextTrack", deck);
      const deckState = get()[deck];
      const queue = get().queue;
      console.log("queue is currently", queue);
      if (!deckState) {
        console.log(`Deck ${deck} not found`);
        return;
      }
      const queuePositionBefore = queue.currentIndex;
      get().advanceQueue();
      const queuePositionAfter = get().queue.currentIndex;
      if (queuePositionAfter === queuePositionBefore) {
        console.log("queue is empty clearing deck:", deck);
        // Clean up audio element
        if (deckState.audioElement) {
          deckState.audioElement.pause();
          deckState.audioElement.src = "";
          deckState.audioElement.load();
        }
        const newDeckState = {
          ...deckState,
          isLoading: false,
          isLoaded: false,
          track: null,
          audioElement: null
        };
        set(() => ({ [deck]: newDeckState, autoplay: false }));
        return;
      }
      await get().loadTrack(queue.queue[queuePositionAfter], deck);
      get().playDeck(deck, queue.queue[queuePositionAfter].id);
      console.log("autoplayed next track", deck);
    },

    playDeck: (
      deck: "deckA" | "deckB",
      trackId: string,
      offset: number | undefined
    ) => {
      const deckState = get()[deck];
      if (!deckState?.audioElement) {
        console.log(`Deck ${deck} audio element not found`);
        return;
      }

      if (!deckState.isLoaded) {
        console.log(`Deck ${deck} is not loaded`);
        return;
      }

      // Set offset if provided
      if (offset !== undefined) {
        deckState.audioElement.currentTime = offset;
      }

      // Add ended event listener for autoplay functionality
      const handleEnded = () => {
        console.log(`Track ended on ${deck}`);
        if (get().autoplay) {
          get().autoplayNextTrack(deck);
        } else {
          // Clear the track and reset the deck state
          const newDeckState = {
            ...deckState,
            isLoading: false,
            isLoaded: false,
            track: null,
            audioElement: null
          };
          set(() => ({ [deck]: newDeckState }));
        }
      };

      const handlePlaying = () => {
        console.log(`Track started on ${deck}`);
        set((state) => ({ [deck]: { ...state[deck], isPlaying: true } }));
      };
      const handlePaused = () => {
        console.log(`Track paused on ${deck}`);
        set((state) => ({ [deck]: { ...state[deck], isPlaying: false } }));
      };

      // Remove any existing ended listener and add new one
      deckState.audioElement.removeEventListener("ended", handleEnded);
      deckState.audioElement.addEventListener("ended", handleEnded);
      deckState.audioElement.removeEventListener("playing", handlePlaying);
      deckState.audioElement.removeEventListener("pause", handlePaused);
      deckState.audioElement.addEventListener("playing", handlePlaying);
      deckState.audioElement.addEventListener("pause", handlePaused);

      // Play the audio element
      deckState.audioElement.play().catch((error) => {
        console.error(`Failed to play deck ${deck}:`, error);
      });
    },

    pauseDeck: (deck: "deckA" | "deckB") => {
      const deckState = get()[deck];
      if (!deckState?.audioElement) {
        console.log(`Deck ${deck} audio element not found`);
        return;
      }

      if (!deckState.isLoaded) {
        console.log(`Deck ${deck} is not loaded`);
        return;
      }

      // Pause the audio element
      deckState.audioElement.pause();
      console.log(
        `paused deck ${deck} at: ${deckState.audioElement.currentTime}`
      );
    },

    setDeckVolume: (deck: "deckA" | "deckB", volume: number) => {
      const deckState = get()[deck];
      if (!deckState?.audioElement) {
        throw new Error(`Deck ${deck} audio element not found`);
      }

      // Set volume directly on audio element
      deckState.audioElement.volume = volume;
    },

    setDeckBpm: (deck: "deckA" | "deckB", bpm: number) => {
      const deckState = get()[deck];
      if (!deckState?.audioElement) {
        throw new Error(`Deck ${deck} audio element not found`);
      }
      const trackBpm = deckState.track?.bpm;
      if (!trackBpm) {
        throw new Error(`Track ${deckState.track?.title} has no BPM`);
      }
      if (bpm < 0) {
        throw new Error(`BPM cannot be less than 0, not in spec`);
      }
      const playbackRate = bpm / trackBpm; // 1.0 is normal speed
      deckState.audioElement.playbackRate = playbackRate;
    },

    recalculateDeckPosition: (deck: "deckA" | "deckB") => {
      // This is no longer needed as audio element maintains currentTime automatically
      // but keeping for compatibility - audio elements handle position tracking internally
      const deckState = get()[deck];
      if (deckState?.audioElement) {
        // No-op: audio element maintains currentTime automatically
      }
    }
  }));

  initState.then((initState) => {
    console.log("Audio store initialized", initState);
    store.setState(initState);
  });

  return store;
};

const loadTrack = async (track: Track): Promise<DeckState> => {
  // Get audio URL
  const audioUrl = await analysisApi.getTrackAudioUrl(track.id);

  // Create audio element
  const audioElement = new Audio();
  audioElement.src = audioUrl.url;
  audioElement.preload = "auto";
  audioElement.crossOrigin = "anonymous";
  audioElement.defaultPlaybackRate = 1.0;

  // Wait for audio to be ready
  await new Promise<void>((resolve, reject) => {
    const handleCanPlay = () => {
      audioElement.removeEventListener("canplaythrough", handleCanPlay);
      audioElement.removeEventListener("error", handleError);
      resolve();
    };

    const handleError = () => {
      audioElement.removeEventListener("canplaythrough", handleCanPlay);
      audioElement.removeEventListener("error", handleError);
      reject(new Error("Failed to load audio"));
    };

    audioElement.addEventListener("canplaythrough", handleCanPlay);
    audioElement.addEventListener("error", handleError);

    // Start loading
    audioElement.load();
  });

  console.log(`Audio loaded successfully. Duration: ${audioElement.duration}s`);

  // Create new deck state
  const newDeckState: DeckState = {
    track,
    audioElement,
    isLoading: false,
    isLoaded: true,
    cuePoint: 0,
    isAnimating: true
  };

  return newDeckState;
};

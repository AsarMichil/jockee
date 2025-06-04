import { createStore } from "zustand/vanilla";
import { AudioContextManager } from "./AudioContextManager";
import { analysisApi } from "../api/analysis";
import WaveSurfer from "wavesurfer.js";

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
  isLoading: boolean;
  isLoaded: boolean;
  cuePoint: number;
  isAnimating: boolean;
  audioUrl?: string;
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

  // Audio Elements (separated from deck state) - always defined
  deckAAudioElement: HTMLAudioElement;
  deckBAudioElement: HTMLAudioElement;

  deckAWavesurfer: WaveSurfer | null;
  deckBWavesurfer: WaveSurfer | null;

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
};

export type AudioPlayerStore = AudioPlayerStoreState & AudioPlayerStoreActions;

// === DEFAULT INITIAL STATES ===
const createAudioStore = () => {
  console.log("This happened");
  return createStore<AudioPlayerStore>()((set, get) => ({
    tracks: [],
    masterVolume: 0.8,
    audioContextManager: null,
    audioContext: null,
    deckA: null,
    deckB: null,
    deckAAudioElement: new Audio(),
    deckBAudioElement: new Audio(),
    deckAWavesurfer: null,
    deckBWavesurfer: null,
    autoplay: true,
    queue: {
      queue: [],
      currentIndex: 0,
      playbackMode: "sequential",
      playHistory: []
    },
    setDeckA: (deckA: DeckState) => set({ deckA }),
    setDeckB: (deckB: DeckState) => set({ deckB }),

    setMasterVolume: (volume: number) => {
      set({ masterVolume: volume });
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
      try {
        const deckState = get()[deck];
        const audioElementKey =
          deck === "deckA" ? "deckAAudioElement" : "deckBAudioElement";
        const audioElement = get()[audioElementKey];
        console.log("loadTrack", track, deck, audioElement);

        if (deckState?.isLoading) {
          console.log(`Track "${track.title}" is already loading`);
          return;
        }
        if (deckState?.track?.id === track.id) {
          console.log(`Track "${track.title}" is already loaded onto ${deck}`);
          return;
        }

        // Clean up old audio element
        audioElement.pause();
        audioElement.src = "";

        // Set loading state
        set(() => ({
          [deck]: {
            ...deckState,
            isLoading: true,
            isLoaded: false
          }
        }));

        const newDeckState = await loadTrack(track, audioElement);
        set(() => ({
          [deck]: newDeckState
        }));
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
            isLoading: false
          }
        }));
        throw error;
      }
    },

    scrubDeck: (deck: "deckA" | "deckB", position: number) => {
      const audioElementKey =
        deck === "deckA" ? "deckAAudioElement" : "deckBAudioElement";
      const audioElement = get()[audioElementKey];
      console.log("scrubDeck", deck, position);

      // Set the audio element's current time directly
      audioElement.currentTime = position;
    },

    autoplayNextTrack: async (deck: "deckA" | "deckB") => {
      console.log("autoplayNextTrack", deck);
      const deckState = get()[deck];
      const audioElementKey =
        deck === "deckA" ? "deckAAudioElement" : "deckBAudioElement";
      const audioElement = get()[audioElementKey];
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
        audioElement.pause();
        audioElement.src = "";
        audioElement.load();

        const newDeckState = {
          ...deckState,
          isLoading: false,
          isLoaded: false,
          track: null
        };
        set(() => ({
          [deck]: newDeckState,
          autoplay: false
        }));
        return;
      }
      await get().loadTrack(queue.queue[queuePositionAfter], deck);
      get().playDeck(deck, queue.queue[queuePositionAfter].id);
      console.log("autoplayed next track", deck);
    },

    playDeck: (
      deck: "deckA" | "deckB",
      _trackId: string,
      offset: number | undefined
    ) => {
      const deckState = get()[deck];
      const audioElementKey =
        deck === "deckA" ? "deckAAudioElement" : "deckBAudioElement";
      const audioElement = get()[audioElementKey];

      if (!deckState?.isLoaded) {
        console.log(`Deck ${deck} is not loaded`);
        return;
      }

      // Set offset if provided
      if (offset !== undefined) {
        audioElement.currentTime = offset;
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
            track: null
          };
          set(() => ({
            [deck]: newDeckState
          }));
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
      audioElement.removeEventListener("ended", handleEnded);
      audioElement.addEventListener("ended", handleEnded);
      audioElement.removeEventListener("playing", handlePlaying);
      audioElement.removeEventListener("pause", handlePaused);
      audioElement.addEventListener("playing", handlePlaying);
      audioElement.addEventListener("pause", handlePaused);

      // Play the audio element
      audioElement.play().catch((error) => {
        console.error(`Failed to play deck ${deck}:`, error);
      });
    },

    pauseDeck: (deck: "deckA" | "deckB") => {
      const audioElementKey =
        deck === "deckA" ? "deckAAudioElement" : "deckBAudioElement";
      const audioElement = get()[audioElementKey];
      // Pause the audio element
      audioElement.pause();
      console.log(`paused deck ${deck} at: ${audioElement.currentTime}`);
    },

    setDeckVolume: (deck: "deckA" | "deckB", volume: number) => {
      const audioElementKey =
        deck === "deckA" ? "deckAAudioElement" : "deckBAudioElement";
      const audioElement = get()[audioElementKey];

      // Set volume directly on audio element
      audioElement.volume = volume;
    },

    setDeckBpm: (deck: "deckA" | "deckB", bpm: number) => {
      const audioElementKey =
        deck === "deckA" ? "deckAAudioElement" : "deckBAudioElement";
      const audioElement = get()[audioElementKey];
      const deckState = get()[deck];

      const trackBpm = deckState?.track?.bpm;
      if (!trackBpm) {
        throw new Error(`Track ${deckState?.track?.title} has no BPM`);
      }
      if (bpm < 0) {
        throw new Error(`BPM cannot be less than 0, not in spec`);
      }
      const playbackRate = bpm / trackBpm; // 1.0 is normal speed
      audioElement.playbackRate = playbackRate;
    }
  }));
};

export const store = createAudioStore();
export const setDeckWavesurfer = (
  deck: "deckA" | "deckB",
  wavesurfer: WaveSurfer
) => {
  console.log("Setting wavesurfer for deck", deck);
  const state = store.getState();
  if (deck === "deckA") {
    store.setState({ ...state, deckAWavesurfer: wavesurfer });
  } else {
    store.setState({ ...state, deckBWavesurfer: wavesurfer });
  }
};
/**
 * Audio loading error types for better error handling
 */
enum AudioLoadError {
  NETWORK_ERROR = "NETWORK_ERROR",
  DECODE_ERROR = "DECODE_ERROR",
  FORMAT_NOT_SUPPORTED = "FORMAT_NOT_SUPPORTED",
  ABORTED = "ABORTED",
  UNKNOWN = "UNKNOWN"
}

/**
 * Maps HTML5 audio error codes to our custom error types
 */
const mapAudioError = (errorCode: number): AudioLoadError => {
  switch (errorCode) {
    case 1:
      return AudioLoadError.ABORTED;
    case 2:
      return AudioLoadError.NETWORK_ERROR;
    case 3:
      return AudioLoadError.DECODE_ERROR;
    case 4:
      return AudioLoadError.FORMAT_NOT_SUPPORTED;
    default:
      return AudioLoadError.UNKNOWN;
  }
};

/**
 * Promisified audio loading with proper error handling
 */
const loadAudioElement = async (
  audioElement: HTMLAudioElement,
  src: string
): Promise<void> => {
  return new Promise((resolve, reject) => {
    // Cleanup function to remove event listeners
    const cleanup = () => {
      audioElement.removeEventListener("canplaythrough", handleSuccess);
      audioElement.removeEventListener("error", handleError);
      audioElement.removeEventListener("abort", handleAbort);
    };

    const handleSuccess = () => {
      cleanup();
      resolve();
    };

    const handleError = () => {
      cleanup();
      const errorType = audioElement.error
        ? mapAudioError(audioElement.error.code)
        : AudioLoadError.UNKNOWN;
      const errorMessage =
        audioElement.error?.message || "Unknown audio loading error";

      reject(new Error(`Audio loading failed [${errorType}]: ${errorMessage}`));
    };

    const handleAbort = () => {
      cleanup();
      reject(new Error(`Audio loading was aborted for: ${src}`));
    };

    // Set up event listeners
    audioElement.addEventListener("canplaythrough", handleSuccess, {
      once: true
    });
    audioElement.addEventListener("error", handleError, { once: true });
    audioElement.addEventListener("abort", handleAbort, { once: true });

    // Configure audio element
    audioElement.src = src;
    audioElement.preload = "auto";
    audioElement.crossOrigin = "anonymous";
    audioElement.defaultPlaybackRate = 1.0;

    // Start loading
    audioElement.load();
  });
};

/**
 * Creates a new deck state after successful audio loading
 */
const createLoadedDeckState = (track: Track): DeckState => ({
  track,
  isLoading: false,
  isLoaded: true,
  cuePoint: 0,
  isAnimating: true
});

/**
 * Main track loading function with improved error handling and separation of concerns
 */
const loadTrack = async (
  track: Track,
  audioElement: HTMLAudioElement
): Promise<DeckState> => {
  try {
    // Validate inputs
    if (!track?.id) {
      throw new Error("Invalid track: missing track ID");
    }

    if (!audioElement) {
      throw new Error("Invalid audio element provided");
    }

    // Stop and clear any existing audio
    audioElement.pause();
    audioElement.src = "";

    // Get the audio URL from the backend
    const fullUrl = await analysisApi.getTrackAudioUrl(track.id);

    console.log(
      `Loading track "${track.title}" by ${track.artist} from: ${fullUrl}`
    );

    // Load the audio element
    await loadAudioElement(audioElement, fullUrl.url);

    console.log(
      `Successfully loaded "${
        track.title
      }" (Duration: ${audioElement.duration?.toFixed(2)}s)`
    );

    // Return the new deck state
    return createLoadedDeckState(track);
  } catch (error) {
    // Enhanced error logging
    console.error(
      `Failed to load track "${track?.title || "Unknown"}" (ID: ${
        track?.id || "Unknown"
      }):`,
      {
        error: error instanceof Error ? error.message : "Unknown error",
        trackId: track?.id,
        trackTitle: track?.title,
        audioSrc: audioElement?.src,
        audioNetworkState: audioElement?.networkState,
        audioReadyState: audioElement?.readyState
      }
    );

    // Re-throw with additional context
    throw new Error(
      `Track loading failed: ${
        error instanceof Error ? error.message : "Unknown error"
      }`
    );
  }
};

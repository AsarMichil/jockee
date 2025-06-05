import { atom } from "jotai";
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
  isPlaying?: boolean;
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

// === JOTAI ATOMS ===

// Basic state atoms
export const masterVolumeAtom = atom<number>(1.0);
export const audioContextManagerAtom = atom<AudioContextManager | null>(null);
export const audioContextAtom = atom<AudioContext | null>(null);
export const tracksAtom = atom<Track[]>([]);
export const autoplayAtom = atom<boolean>(true);

// 0.5 = center, 0 = deckA, 1 = deckB
export const crossfaderAtom = atom<number>(0.5);
export const deckAVolumeAtom = atom<number>(1.0);
export const deckBVolumeAtom = atom<number>(1.0);

// Deck state atoms
export const deckAAtom = atom<DeckState | null>(null);
export const deckBAtom = atom<DeckState | null>(null);

// Audio elements atoms (these will be initialized once)
export const deckAAudioElementAtom = atom<HTMLAudioElement>(new Audio());
export const deckBAudioElementAtom = atom<HTMLAudioElement>(new Audio());

// Wavesurfer atoms
export const deckAWavesurferAtom = atom<WaveSurfer | null>(null);
export const deckBWavesurferAtom = atom<WaveSurfer | null>(null);

// Queue state atom
export const queueAtom = atom<QueueState>({
  queue: [],
  currentIndex: 0,
  playbackMode: "sequential",
  playHistory: []
});

// === DERIVED ATOMS ===

// Master volume setter with side effect
export const setMasterVolumeAtom = atom(null, (get, set, volume: number) => {
  set(masterVolumeAtom, volume);
  // Also update the actual audio context master volume
  const audioContextManager = get(audioContextManagerAtom);
  if (audioContextManager) {
    audioContextManager.setMasterVolume(volume);
  }
});

// Queue actions
export const setQueuedTracksAtom = atom(null, (get, set, tracks: Track[]) => {
  const currentQueue = get(queueAtom);
  set(queueAtom, { ...currentQueue, queue: tracks });
});

export const advanceQueueAtom = atom(null, (get, set) => {
  const currentQueue = get(queueAtom);
  set(queueAtom, {
    ...currentQueue,
    currentIndex: Math.min(
      currentQueue.currentIndex + 1,
      currentQueue.queue.length - 1
    )
  });
});

// Load track action
export const loadTrackAtom = atom(
  null,
  async (
    get,
    set,
    { track, deck }: { track: Track; deck: "deckA" | "deckB" }
  ) => {
    try {
      const deckStateAtom = deck === "deckA" ? deckAAtom : deckBAtom;
      const audioElementAtom =
        deck === "deckA" ? deckAAudioElementAtom : deckBAudioElementAtom;

      const deckState = get(deckStateAtom);
      const audioElement = get(audioElementAtom);

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
      const loadingState: DeckState = {
        track: deckState?.track || null,
        isLoading: true,
        isLoaded: false,
        cuePoint: deckState?.cuePoint || 0,
        isAnimating: deckState?.isAnimating || false,
        audioUrl: deckState?.audioUrl,
        isPlaying: deckState?.isPlaying || false
      };
      set(deckStateAtom, loadingState);

      const newDeckState = await loadTrack(track, audioElement);
      set(deckStateAtom, newDeckState);
      console.log(`Track "${track.title}" loaded onto ${deck}`);
    } catch (error) {
      console.error(`Failed to load track onto ${deck}:`, error);
      // Set error state on deck
      const deckStateAtom = deck === "deckA" ? deckAAtom : deckBAtom;
      const deckState = get(deckStateAtom);
      const errorState: DeckState = {
        track,
        isLoaded: false,
        isLoading: false,
        cuePoint: deckState?.cuePoint || 0,
        isAnimating: deckState?.isAnimating || false,
        audioUrl: deckState?.audioUrl,
        isPlaying: false
      };
      set(deckStateAtom, errorState);
      throw error;
    }
  }
);

// Scrub deck action
export const scrubDeckAtom = atom(
  null,
  (
    get,
    set,
    { deck, position }: { deck: "deckA" | "deckB"; position: number }
  ) => {
    const audioElementAtom =
      deck === "deckA" ? deckAAudioElementAtom : deckBAudioElementAtom;
    const audioElement = get(audioElementAtom);
    console.log("scrubDeck", deck, position);

    // Set the audio element's current time directly
    audioElement.currentTime = position;
  }
);

// Autoplay next track action
export const autoplayNextTrackAtom = atom(
  null,
  async (get, set, deck: "deckA" | "deckB") => {
    console.log("autoplayNextTrack", deck);

    const deckStateAtom = deck === "deckA" ? deckAAtom : deckBAtom;
    const audioElementAtom =
      deck === "deckA" ? deckAAudioElementAtom : deckBAudioElementAtom;

    const deckState = get(deckStateAtom);
    const audioElement = get(audioElementAtom);
    const queue = get(queueAtom);

    console.log("queue is currently", queue);

    if (!deckState) {
      console.log(`Deck ${deck} not found`);
      return;
    }

    const queuePositionBefore = queue.currentIndex;
    set(advanceQueueAtom);
    const queuePositionAfter = get(queueAtom).currentIndex;

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
      set(deckStateAtom, newDeckState);
      set(autoplayAtom, false);
      return;
    }

    const nextTrack = get(queueAtom).queue[queuePositionAfter];
    await set(loadTrackAtom, { track: nextTrack, deck });
    set(playDeckAtom, { deck, trackId: nextTrack.id });
    console.log("autoplayed next track", deck);
  }
);

// Play deck action
export const playDeckAtom = atom(
  null,
  (
    get,
    set,
    {
      deck,
      offset
    }: { deck: "deckA" | "deckB"; trackId?: string; offset?: number }
  ) => {
    const deckStateAtom = deck === "deckA" ? deckAAtom : deckBAtom;
    const audioElementAtom =
      deck === "deckA" ? deckAAudioElementAtom : deckBAudioElementAtom;

    const deckState = get(deckStateAtom);
    const audioElement = get(audioElementAtom);

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
      if (get(autoplayAtom)) {
        set(autoplayNextTrackAtom, deck);
      } else {
        // Clear the track and reset the deck state
        const newDeckState: DeckState = {
          track: null,
          isLoading: false,
          isLoaded: false,
          cuePoint: 0,
          isAnimating: false,
          isPlaying: false
        };
        set(deckStateAtom, newDeckState);
      }
    };

    const handlePlaying = () => {
      console.log(`Track started on ${deck}`);
      const currentDeckState = get(deckStateAtom);
      if (currentDeckState) {
        set(deckStateAtom, { ...currentDeckState, isPlaying: true });
      }
    };

    const handlePaused = () => {
      console.log(`Track paused on ${deck}`);
      const currentDeckState = get(deckStateAtom);
      if (currentDeckState) {
        set(deckStateAtom, { ...currentDeckState, isPlaying: false });
      }
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
  }
);

// Pause deck action
export const pauseDeckAtom = atom(null, (get, set, deck: "deckA" | "deckB") => {
  const audioElementAtom =
    deck === "deckA" ? deckAAudioElementAtom : deckBAudioElementAtom;
  const audioElement = get(audioElementAtom);
  // Pause the audio element
  audioElement.pause();
  console.log(`paused deck ${deck} at: ${audioElement.currentTime}`);
});

export const playPauseDeckAtom = atom(
  null,
  (get, set, deck: "deckA" | "deckB") => {
    const audioElementAtom =
      deck === "deckA" ? deckAAudioElementAtom : deckBAudioElementAtom;
    const audioElement = get(audioElementAtom);
    if (audioElement.paused) {
      set(playDeckAtom, { deck });
    } else {
      set(pauseDeckAtom, deck);
    }
  }
);

export const setCrossfaderAtom = atom(null, (get, set, crossfader: number) => {
  set(crossfaderAtom, crossfader);
  const deckAVolume = get(deckAVolumeAtom);
  const deckBVolume = get(deckBVolumeAtom);
  const deckAElement = get(deckAAudioElementAtom);
  const deckBElement = get(deckBAudioElementAtom);
  deckAElement.volume = computePlaybackVolume("deckA", deckAVolume, crossfader);
  deckBElement.volume = computePlaybackVolume("deckB", deckBVolume, crossfader);
});

// Set deck volume action
export const setDeckVolumeAtom = atom(
  null,
  (get, set, { deck, volume }: { deck: "deckA" | "deckB"; volume: number }) => {
    console.log("Setting deck volume", deck, volume);
    if (deck === "deckA") {
      set(deckAVolumeAtom, volume);
      const crossfader = get(crossfaderAtom);
      const playbackVolume = computePlaybackVolume(deck, volume, crossfader);
      const deckElement = get(deckAAudioElementAtom);
      deckElement.volume = playbackVolume;
    } else {
      set(deckBVolumeAtom, volume);
      const crossfader = get(crossfaderAtom);
      const playbackVolume = computePlaybackVolume(deck, volume, crossfader);
      const deckElement = get(deckBAudioElementAtom);
      deckElement.volume = playbackVolume;
    }
  }
);

/**
 * Computes the crossfader curve multiplier for a given position
 * Uses an S-curve that ensures both channels are at full volume when crossfader = 0.5
 * @param crossfader - The crossfader position (0 to 1)
 * @param forDeckA - Whether this is for deck A (true) or deck B (false)
 * @returns The volume multiplier (0 to 1)
 */
const computeCrossfaderCurve = (
  crossfader: number,
  forDeckA: boolean
): number => {
  // Clamp crossfader to valid range
  const pos = Math.max(0, Math.min(1, crossfader));

  if (forDeckA) {
    // For deck A: full volume from 0 to 0.5, then fade out
    if (pos <= 0.5) {
      return 1.0; // Full volume from left to center
    } else {
      // Smooth curve from 1.0 to 0.0 as we go from center (0.5) to right (1.0)
      const fadePosition = (pos - 0.5) * 2; // Normalize to 0-1 range
      // Use cosine curve for smooth fade
      return Math.cos((fadePosition * Math.PI) / 2);
    }
  } else {
    // For deck B: fade in until 0.5, then full volume
    if (pos >= 0.5) {
      return 1.0; // Full volume from center to right
    } else {
      // Smooth curve from 0.0 to 1.0 as we go from left (0.0) to center (0.5)
      const fadePosition = pos * 2; // Normalize to 0-1 range
      // Use sine curve for smooth fade in
      return Math.sin((fadePosition * Math.PI) / 2);
    }
  }
};

/**
 * Computes the playback volume for a given deck and crossfader
 * 0.5 = center (both decks at full volume), 0 = deckA only, 1 = deckB only
 * @param deck - The deck to compute the volume for
 * @param deckVolume - The individual deck volume (0 to 1)
 * @param crossfader - The crossfader position (0 to 1)
 * @returns The final playback volume for the given deck and crossfader
 */
const computePlaybackVolume = (
  deck: "deckA" | "deckB",
  deckVolume: number,
  crossfader: number
): number => {
  const crossfaderMultiplier = computeCrossfaderCurve(
    crossfader,
    deck === "deckA"
  );
  return deckVolume * crossfaderMultiplier;
};
// Set deck BPM action
export const setDeckBpmAtom = atom(
  null,
  (get, set, { deck, bpm }: { deck: "deckA" | "deckB"; bpm: number }) => {
    const audioElementAtom =
      deck === "deckA" ? deckAAudioElementAtom : deckBAudioElementAtom;
    const deckStateAtom = deck === "deckA" ? deckAAtom : deckBAtom;

    const audioElement = get(audioElementAtom);
    const deckState = get(deckStateAtom);

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
);

// Wavesurfer setter atoms
export const setDeckAWavesurferAtom = atom(
  null,
  (get, set, wavesurfer: WaveSurfer) => {
    console.log("Setting wavesurfer for deckA");
    set(deckAWavesurferAtom, wavesurfer);
  }
);

export const setDeckBWavesurferAtom = atom(
  null,
  (get, set, wavesurfer: WaveSurfer) => {
    console.log("Setting wavesurfer for deckB");
    set(deckBWavesurferAtom, wavesurfer);
  }
);

// Helper function for setting wavesurfer (maintains compatibility)
export const setDeckWavesurfer = (
  deck: "deckA" | "deckB",
  wavesurfer: WaveSurfer,
  setAtom: (
    atomSetter: typeof setDeckAWavesurferAtom | typeof setDeckBWavesurferAtom,
    value: WaveSurfer
  ) => void
) => {
  console.log("Setting wavesurfer for deck", deck);
  if (deck === "deckA") {
    setAtom(setDeckAWavesurferAtom, wavesurfer);
  } else {
    setAtom(setDeckBWavesurferAtom, wavesurfer);
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

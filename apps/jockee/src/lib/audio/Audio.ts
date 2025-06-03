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
}

interface DeckState {
  track: Track | null;
  isPlaying: boolean;
  volume: number;
  pitch: number; // Pitch adjustment (-8% to +8%)
  cuePoint: number;
  audioSource: AudioBufferSourceNode | null;
  audioBuffer: AudioBuffer | null;
  gainNode: GainNode | null;
  isLoading: boolean;
  isLoaded: boolean;
  currentPosition: number; // not actually current position, but the position of the track when the deck was paused
  startTime: number; // when the deck was started
  isPaused: boolean;
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
      try {
        const audioContextManager = get().audioContextManager;
        if (!audioContextManager) {
          throw new Error("Audio context manager not initialized");
        }
        const deckState = get()[deck];
        if (deckState?.isLoading) {
          console.log(`Track "${track.title}" is already loading`);
          return;
        }
        if (deckState?.track?.id === track.id) {
          console.log(`Track "${track.title}" is already loaded onto ${deck}`);
          return;
        }
        // set loading and clear old state if it exists
        deckState?.audioSource?.stop();
        deckState?.audioSource?.disconnect();
        set(() => ({
          [deck]: {
            ...deckState,
            isLoading: true,
            isLoaded: false,
            audioSource: null,
            startTime: 0,
            currentPosition: 0,
            isPaused: false
          }
        }));
        const newDeckState = await loadTrack(audioContextManager, track);
        set(() => ({ [deck]: newDeckState }));
        console.log("new deck state please", get()[deck]);
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
            audioBuffer: null,
            audioSource: null,
            gainNode: null
          }
        }));
        throw error;
      }
    },

    scrubDeck: (deck: "deckA" | "deckB", position: number) => {
      const deckState = get()[deck];
      console.log("scrubDeck", deck, position);
      if (!deckState) {
        console.log(`Deck ${deck} not found, you are an idiot`);
        return;
      }
      const audioContextManager = get().audioContextManager;
      if (!audioContextManager) {
        throw new Error("Audio context manager not initialized");
      }
      const audioContext = audioContextManager.getContext();
      if (!audioContext) {
        throw new Error("Audio context not available");
      }

      // if playing just play again with the new position as the offset
      if (deckState.isPlaying) {
        if (!deckState.track?.id) {
          throw new Error("Track ID not available");
        }
        // play the deck again with the new position as the offset
        get().playDeck(deck, deckState.track.id, position);
        return;
      } else {
        const newDeckState = {
          ...deckState,
          currentPosition: position,
          isPaused: true
        };
        set(() => ({ [deck]: newDeckState }));
        return;
      }
    },

    autoplayNextTrack: async (deck: "deckA" | "deckB") => {
      console.log("autoplayNextTrack", deck);
      const deckState = get()[deck];
      const queue = get().queue;
      console.log("queue is currently", queue);
      if (!deckState) {
        console.log(`Deck ${deck} not found, you are an idiot`);
        return;
      }
      const queuePositionBefore = queue.currentIndex;
      get().advanceQueue();
      const queuePositionAfter = get().queue.currentIndex;
      if (queuePositionAfter === queuePositionBefore) {
        console.log("queue is empty clearing deck:", deck);
        const newDeckState = {
          ...deckState,
          isPlaying: false,
          audioSource: null,
          isPaused: false,
          currentPosition: 0,
          startTime: 0,
          isLoading: false,
          isLoaded: false,
          track: null
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
      if (!deckState) {
        console.log(`Deck ${deck} not found, you are an idiot`);
        return;
      }

      if (!deckState.isLoaded) {
        console.log(`Deck ${deck} is not loaded, you are an idiot`);
        return;
      }

      if (deckState.isPlaying) {
        console.log(
          `Deck ${deck} is already playing, you are an idiot`,
          deckState.audioSource
        );
        // stop the deck
        deckState.audioSource?.stop();
        deckState.audioSource?.disconnect();
        // remove the onended listener
        if (deckState.audioSource) {
          deckState.audioSource.onended = null;
        }
        deckState.audioSource = null;
        const newDeckState = { ...deckState, isPlaying: false };
        set(() => ({ [deck]: newDeckState }));
      }
      const audioContextManager = get().audioContextManager;
      if (!audioContextManager) {
        throw new Error("Audio context manager not initialized");
      }

      let trackOffset: number;
      if (offset !== undefined) {
        console.log("offset balls", offset);
        trackOffset = offset;
      } else {
        console.log("no offset balls");
        trackOffset = deckState.isPaused ? deckState.currentPosition : 0;
      }
      console.log(
        `${
          deckState.isPaused ? "Resuming" : "Playing"
        } deck ${deck} with offset ${trackOffset}`
      );

      const newDeckState = playDeck(
        audioContextManager,
        deckState,
        trackId,
        trackOffset
      );

      if (newDeckState.audioSource) {
        newDeckState.audioSource.onended = () => {
          const deckState = get()[deck];
          if (!deckState) {
            console.log(`Deck ${deck} not found, you are an idiot`);
            return;
          }
          // if not playing, stop the deck
          if (deckState.isPlaying) {
            console.log("current queue", get().queue);
            if (get().autoplay) {
              get().autoplayNextTrack(deck);
            } else {
              const updatedDeckState = {
                isPlaying: false,
                isAnimating: false,
                audioSource: null,
                isPaused: false,
                currentPosition: 0,
                startTime: 0,
                isLoading: false,
                isLoaded: false,
                track: null
              };
              set(() => ({ [deck]: updatedDeckState }));
            }
          }
        };
      }

      set(() => ({ [deck]: newDeckState }));
    },

    pauseDeck: (deck: "deckA" | "deckB") => {
      const deckState = get()[deck];
      if (!deckState) {
        console.log(`Deck ${deck} not found, you are an idiot`);
        return;
      }
      const audioContextManager = get().audioContextManager;
      if (!audioContextManager) {
        throw new Error("Audio context manager not initialized");
      }
      if (!deckState.isLoaded) {
        console.log(`Deck ${deck} is not loaded, you are an idiot`);
        return;
      }
      if (!deckState.isPlaying) {
        console.log(`Deck ${deck} is not playing, you are an idiot`);
        return;
      }
      const newDeckState = pauseDeck(audioContextManager, deckState);
      set(() => ({ [deck]: newDeckState }));
    },

    setDeckVolume: (deck: "deckA" | "deckB", volume: number) => {
      const deckState = get()[deck];
      if (!deckState) {
        throw new Error(`Deck ${deck} not found`);
      }
      const audioContextManager = get().audioContextManager;
      if (!audioContextManager) {
        throw new Error("Audio context manager not initialized");
      }
      ensureContextIsResumed(audioContextManager);
      const audioContext = audioContextManager.getContext();
      if (!audioContext) {
        throw new Error("Audio context not available");
      }
      if (!deckState.gainNode) {
        throw new Error("Gain node not available");
      }
      deckState.gainNode.gain.value = volume;
      const newDeckState = { ...deckState };
      set(() => ({ [deck]: newDeckState }));
    },
    recalculateDeckPosition: (deck: "deckA" | "deckB") => {
      const deckState = get()[deck];
      if (!deckState) {
        return;
      }
      if (deckState.isPlaying) {
        const audioContextManager = get().audioContextManager;
        if (!audioContextManager) {
          throw new Error("Audio context manager not initialized");
        }
        const audioContext = audioContextManager.getContext();
        if (!audioContext) {
          throw new Error("Audio context not available");
        }
        const currentTime = audioContext.currentTime;
        const deckPosition = currentTime - deckState.startTime;
        set((state) => ({
          ...state,
          [deck]: {
            ...state[deck],
            currentPosition: deckPosition
          }
        }));
      }
    }
  }));

  initState.then((initState) => {
    console.log("Audio store initialized", initState);
    store.setState(initState);
  });

  return store;
};

/**
 * Load audio from URL using fetch with proper streaming support
 */
async function loadAudioFromUrl(
  audioContext: AudioContext,
  url: string
): Promise<AudioBuffer> {
  try {
    const response = await fetch(url, {
      headers: {
        "Accept": "audio/*"
      }
    });

    if (!response.ok) {
      throw new Error(
        `Failed to fetch audio: ${response.status} ${response.statusText}`
      );
    }

    const arrayBuffer = await response.arrayBuffer();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

    console.log(
      `Audio loaded successfully. Duration: ${audioBuffer.duration}s`
    );
    return audioBuffer;
  } catch (error) {
    console.error("Error loading audio from URL:", error);
    throw error;
  }
}

const loadTrack = async (
  audioContextManager: AudioContextManager,
  track: Track
) => {
  ensureContextIsResumed(audioContextManager);

  if (!audioContextManager) {
    throw new Error("Audio context manager not initialized");
  }

  const audioContext = audioContextManager.getContext();
  if (!audioContext) {
    throw new Error("Audio context not available");
  }

  // Get audio URL and load the audio buffer
  const audioUrl = await analysisApi.getTrackAudioUrl(track.id);
  const audioBuffer = await loadAudioFromUrl(audioContext, audioUrl.url);

  // Create gain node for this deck
  const gainNode = audioContext.createGain();
  gainNode.connect(
    audioContextManager.getMasterGain() || audioContext.destination
  );

  // Create new deck state
  const newDeckState: DeckState = {
    track,
    isPlaying: false,
    volume: 0.8,
    pitch: 0,
    cuePoint: 0,
    audioSource: null, // Will be created when playing
    audioBuffer,
    gainNode,
    isLoading: false,
    isLoaded: true,
    currentPosition: 0,
    startTime: 0,
    isPaused: false,
    isAnimating: true
  };
  return newDeckState;
};

const ensureContextIsResumed = (audioContextManager: AudioContextManager) => {
  audioContextManager.resume();
};

const playDeck = (
  audioContextManager: AudioContextManager,
  deck: DeckState,
  trackId: string,
  offset: number
) => {
  ensureContextIsResumed(audioContextManager);

  const audioContext = audioContextManager.getContext();
  if (!audioContext) {
    throw new Error("Audio context not available");
  }

  const audioBuffer = deck.audioBuffer;
  if (!audioBuffer) {
    throw new Error("Audio buffer not available");
  }

  const audioSource = audioContext.createBufferSource();
  audioSource.buffer = audioBuffer;
  if (!deck.gainNode) {
    deck.gainNode = audioContextManager.setupGainNode();
  }
  audioSource.connect(deck.gainNode);
  audioSource.start(0, offset);

  const newDeckState: DeckState = {
    ...deck,
    audioSource,
    isPlaying: true,
    isPaused: false,
    startTime: audioContext.currentTime - offset
  };
  return newDeckState;
};

const pauseDeck = (
  audioContextManager: AudioContextManager,
  deck: DeckState
) => {
  ensureContextIsResumed(audioContextManager);

  const audioContext = audioContextManager.getContext();
  if (!audioContext) {
    throw new Error("Audio context not available");
  }
  if (deck.isPaused) {
    console.log(`Deck ${deck} is already paused, you are an idiot`);
    return;
  }
  if (!deck.audioSource) {
    throw new Error("Audio source not available");
  }
  deck.audioSource.stop();
  deck.audioSource.disconnect();
  deck.audioSource = null;

  const pausedTime = audioContext.currentTime - deck.startTime;
  console.log(`Paused deck ${deck} at ${pausedTime}`);
  const newDeckState: DeckState = {
    ...deck,
    isPlaying: false,
    isPaused: true,
    currentPosition: pausedTime
  };
  return newDeckState;
};

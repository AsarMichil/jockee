import { ReactNode } from "react";
import { Provider, useSetAtom } from "jotai";
import { useAtom } from "jotai";
import {
  masterVolumeAtom,
  audioContextManagerAtom,
  audioContextAtom,
  tracksAtom,
  autoplayAtom,
  deckAAtom,
  deckBAtom,
  deckAAudioElementAtom,
  deckBAudioElementAtom,
  deckAWavesurferAtom,
  deckBWavesurferAtom,
  queueAtom,
  setMasterVolumeAtom,
  setQueuedTracksAtom,
  advanceQueueAtom,
  loadTrackAtom,
  scrubDeckAtom,
  autoplayNextTrackAtom,
  playDeckAtom,
  pauseDeckAtom,
  setDeckVolumeAtom,
  setDeckBpmAtom,
  setDeckAWavesurferAtom,
  setDeckBWavesurferAtom,
  deckAEQAtom,
  deckBEQAtom,
  setEQBandAtom,
  resetEQAtom,
  initializeEQFiltersAtom
} from "./Audio";

export interface AudioStoreProviderProps {
  children: ReactNode;
}

export const AudioStoreProvider = ({ children }: AudioStoreProviderProps) => {
  return (
    <Provider>
      {children}
    </Provider>
  );
};

// Custom hooks for audio store state and actions
export const useAudioState = () => {
  const [masterVolume] = useAtom(masterVolumeAtom);
  const [audioContextManager] = useAtom(audioContextManagerAtom);
  const [audioContext] = useAtom(audioContextAtom);
  const [tracks] = useAtom(tracksAtom);
  const [autoplay] = useAtom(autoplayAtom);
  const [deckA] = useAtom(deckAAtom);
  const [deckB] = useAtom(deckBAtom);
  const [deckAAudioElement] = useAtom(deckAAudioElementAtom);
  const [deckBAudioElement] = useAtom(deckBAudioElementAtom);
  const [deckAWavesurfer] = useAtom(deckAWavesurferAtom);
  const [deckBWavesurfer] = useAtom(deckBWavesurferAtom);
  const [queue] = useAtom(queueAtom);
  const [deckAEQ] = useAtom(deckAEQAtom);
  const [deckBEQ] = useAtom(deckBEQAtom);

  return {
    masterVolume,
    audioContextManager,
    audioContext,
    tracks,
    autoplay,
    deckA,
    deckB,
    deckAAudioElement,
    deckBAudioElement,
    deckAWavesurfer,
    deckBWavesurfer,
    queue,
    deckAEQ,
    deckBEQ
  };
};

export const useAudioActions = () => {
  const setMasterVolume = useSetAtom(setMasterVolumeAtom);
  const setQueuedTracks = useSetAtom(setQueuedTracksAtom);
  const advanceQueue = useSetAtom(advanceQueueAtom);
  const loadTrack = useSetAtom(loadTrackAtom);
  const scrubDeck = useSetAtom(scrubDeckAtom);
  const autoplayNextTrack = useSetAtom(autoplayNextTrackAtom);
  const playDeck = useSetAtom(playDeckAtom);
  const pauseDeck = useSetAtom(pauseDeckAtom);
  const setDeckVolume = useSetAtom(setDeckVolumeAtom);
  const setDeckBpm = useSetAtom(setDeckBpmAtom);
  const setDeckAWavesurfer = useSetAtom(setDeckAWavesurferAtom);
  const setDeckBWavesurfer = useSetAtom(setDeckBWavesurferAtom);
  const setEQBand = useSetAtom(setEQBandAtom);
  const resetEQ = useSetAtom(resetEQAtom);
  const initializeEQFilters = useSetAtom(initializeEQFiltersAtom);

  return {
    setMasterVolume,
    setQueuedTracks,
    advanceQueue,
    loadTrack,
    scrubDeck,
    autoplayNextTrack,
    playDeck,
    pauseDeck,
    setDeckVolume,
    setDeckBpm,
    setDeckAWavesurfer,
    setDeckBWavesurfer,
    setEQBand,
    resetEQ,
    initializeEQFilters
  };
};

// Convenience hook that combines state and actions
export const useAudioStore = () => {
  const state = useAudioState();
  const actions = useAudioActions();
  
  return { ...state, ...actions };
};

// Individual hooks for specific atoms (for more granular usage)
export const useMasterVolume = () => useAtom(masterVolumeAtom);
export const useAutoplay = () => useAtom(autoplayAtom);
export const useDeckA = () => useAtom(deckAAtom);
export const useDeckB = () => useAtom(deckBAtom);
export const useQueue = () => useAtom(queueAtom);
export const useTracks = () => useAtom(tracksAtom);
export const useAudioContextManager = () => useAtom(audioContextManagerAtom);
export const useDeckAWavesurfer = () => useAtom(deckAWavesurferAtom);
export const useDeckBWavesurfer = () => useAtom(deckBWavesurferAtom);
export const useDeckAAudioElement = () => useAtom(deckAAudioElementAtom);
export const useDeckBAudioElement = () => useAtom(deckBAudioElementAtom);

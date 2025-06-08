/**
 * Simplified DJ Agent for Frontend
 * 
 * This is a frontend-only implementation that uses existing Jotai atoms from Audio.ts
 * instead of reinventing audio management. It provides:
 * 
 * - Mix loading from JobResultResponse
 * - Auto DJ functionality that schedules transitions automatically
 * - Uses existing deck management, crossfading, and playback atoms
 * - Simple transition techniques (crossfade, quick cut)
 * 
 * Usage:
 * - loadMixAtom: Load mix instructions 
 * - startAutoDJAtom: Start automated mixing
 * - stopAutoDJAtom: Stop automated mixing
 * - djStateAtom: Get current DJ state
 */

import { atom, Getter, Setter } from "jotai";
import {
  JobResultResponse,
  MixInstructions,
  Transition,
  DJState
} from "./types";
import {
  playDeckAtom,
  loadTrackAtom,
  setCrossfaderAtom,
  autoplayAtom,
  deckAAtom,
  deckBAtom
} from "./audio/Audio";

/**
 * DJ Agent state atom
 */
export interface DJAgentState {
  isActive: boolean;
  currentMix: MixInstructions | null;
  currentPosition: number;
  startTime: number;
  scheduledTransitions: NodeJS.Timeout[];
}

export const djAgentAtom = atom<DJAgentState>({
  isActive: false,
  currentMix: null,
  currentPosition: 0,
  startTime: 0,
  scheduledTransitions: []
});

/**
 * Load mix instructions
 */
export const loadMixAtom = atom(
  null,
  async (get, set, jobResult: JobResultResponse) => {
    const currentState = get(djAgentAtom);
    
    if (!jobResult.mix_instructions) {
      console.error("No mix instructions found");
      return false;
    }

    // Clear existing transitions
    currentState.scheduledTransitions.forEach(timeout => clearTimeout(timeout));

    set(djAgentAtom, {
      ...currentState,
      currentMix: jobResult.mix_instructions,
      currentPosition: 0,
      scheduledTransitions: []
    });

    console.log(`Loaded mix with ${jobResult.mix_instructions.transitions.length} transitions`);
    return true;
  }
);

/**
 * Start auto DJ
 */
export const startAutoDJAtom = atom(
  null,
  async (get, set) => {
    const djState = get(djAgentAtom);
    
    if (!djState.currentMix) {
      console.error("No mix loaded");
      return false;
    }

    if (djState.isActive) {
      console.warn("Auto DJ already active");
      return false;
    }

    // Enable autoplay
    set(autoplayAtom, true);

    // Load first tracks
    const firstTransition = djState.currentMix.transitions[0];
    if (firstTransition) {
      // Convert the track to the Audio.ts Track format
      const trackA = {
        ...firstTransition.track_a,
        bpm: firstTransition.track_a.bpm || 120,
        key: firstTransition.track_a.key || "C",
        energy: firstTransition.track_a.energy || 0.5
      };
      
      await set(loadTrackAtom, { track: trackA, deck: "deckA" });
      
      if (djState.currentMix.transitions.length > 1) {
        const trackB = {
          ...firstTransition.track_b,
          bpm: firstTransition.track_b.bpm || 120,
          key: firstTransition.track_b.key || "C", 
          energy: firstTransition.track_b.energy || 0.5
        };
        await set(loadTrackAtom, { track: trackB, deck: "deckB" });
      }
    }

    // Start playing
    set(playDeckAtom, { deck: "deckA" });

    // Schedule transitions
    const scheduledTransitions = djState.currentMix.transitions.map((transition, index) => {
      const transitionTime = transition.transition_start * 1000;
      console.log(`Transition ${index} scheduled for ${transitionTime}ms`);
      return setTimeout(() => {
        applyTransition(get, set, transition, index);
      }, transitionTime);
    });

    set(djAgentAtom, {
      ...djState,
      isActive: true,
      startTime: Date.now(),
      scheduledTransitions
    });

    console.log("Auto DJ started");
    return true;
  }
);

/**
 * Stop auto DJ
 */
export const stopAutoDJAtom = atom(
  null,
  (get, set) => {
    const djState = get(djAgentAtom);
    
    djState.scheduledTransitions.forEach(timeout => clearTimeout(timeout));
    set(autoplayAtom, false);
    
    set(djAgentAtom, {
      ...djState,
      isActive: false,
      scheduledTransitions: []
    });

    console.log("Auto DJ stopped");
  }
);

/**
 * Apply transition
 */
const applyTransition = async (
  get: Getter,
  set: Setter,
  transition: Transition,
  index: number
) => {
  try {
    console.log(`Applying ${transition.technique}: ${transition.track_a.title} -> ${transition.track_b.title}`);
    
    const deckA = get(deckAAtom);
    
    // Determine which deck to use for new track
    const targetDeck = deckA?.track?.id === transition.track_a.id ? "deckB" : "deckA";
    
    // Convert track to Audio.ts format
    const trackB = {
      ...transition.track_b,
      bpm: transition.track_b.bpm || 120,
      key: transition.track_b.key || "C",
      energy: transition.track_b.energy || 0.5
    };
    
    // Load new track
    await set(loadTrackAtom, { track: trackB, deck: targetDeck });
    
    // Apply transition based on technique
    switch (transition.technique) {
      case "crossfade":
        await applyCrossfade(set, targetDeck, transition.transition_duration);
        break;
      case "quick_cut":
        set(setCrossfaderAtom, targetDeck === "deckA" ? 0.0 : 1.0);
        set(playDeckAtom, { deck: targetDeck });
        break;
      default:
        await applyCrossfade(set, targetDeck, transition.transition_duration);
    }

    // Update position
    const djState = get(djAgentAtom);
    set(djAgentAtom, { ...djState, currentPosition: index + 1 });
    
  } catch (error) {
    console.error(`Transition ${index} failed:`, error);
  }
};

/**
 * Apply crossfade transition
 */
const applyCrossfade = async (
  set: Setter,
  targetDeck: "deckA" | "deckB",
  duration: number
) => {
  // Start playing new track
  set(playDeckAtom, { deck: targetDeck });
  
  // Animate crossfader
  const startPos = targetDeck === "deckA" ? 1.0 : 0.0;
  const endPos = targetDeck === "deckA" ? 0.0 : 1.0;
  
  animateCrossfader(set, startPos, endPos, duration * 1000);
};

/**
 * Animate crossfader
 */
const animateCrossfader = (
  set: Setter,
  start: number,
  end: number,
  durationMs: number
) => {
  const startTime = Date.now();
  
  const animate = () => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(elapsed / durationMs, 1.0);
    const eased = 0.5 * (1 - Math.cos(progress * Math.PI));
    const position = start + (end - start) * eased;
    
    set(setCrossfaderAtom, position);
    
    if (progress < 1.0) {
      requestAnimationFrame(animate);
    }
  };
  
  requestAnimationFrame(animate);
};

/**
 * DJ state derived atom
 */
export const djStateAtom = atom((get) => {
  const djAgent = get(djAgentAtom);
  const deckA = get(deckAAtom);
  const deckB = get(deckBAtom);
  
  if (!djAgent.currentMix) {
    return { status: "no_mix_loaded" as const };
  }
  
  const elapsedTime = djAgent.isActive ? (Date.now() - djAgent.startTime) / 1000 : 0;
  const progress = djAgent.currentMix.total_duration > 0 
    ? Math.min(elapsedTime / djAgent.currentMix.total_duration, 1.0) 
    : 0;
  
  let currentTrack = null;
  if (deckA?.isPlaying) {
    currentTrack = deckA.track;
  } else if (deckB?.isPlaying) {
    currentTrack = deckB.track;
  }
  
  const state: DJState = {
    status: djAgent.isActive ? "playing" : "paused",
    current_position: djAgent.currentPosition,
    total_transitions: djAgent.currentMix.transitions.length,
    elapsed_time: elapsedTime,
    total_duration: djAgent.currentMix.total_duration,
    progress,
    current_track: currentTrack || undefined
  };
  
  return state;
});

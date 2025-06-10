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
  DJState,
  Transition,
  TransitionTechnique,
  Track
} from "./types";
import {
  playDeckAtom,
  deckAAtom,
  deckBAtom,
  pauseDeckAtom,
  queueAtom,
  loadTrackAtom,
  deckAAudioElementAtom,
  deckBAudioElementAtom,
  setCrossfaderAtom
} from "./audio/Audio";

/**
 * DJ Agent state atom
 */
export interface DJAgentState {
  isActive: boolean;
  currentMix: MixInstructions | null;
  currentIndex: number;
  startTime: number;
}

export const djAgentAtom = atom<DJAgentState>({
  isActive: false,
  currentMix: null,
  currentIndex: 0,
  startTime: 0
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
    set(djAgentAtom, {
      ...currentState,
      currentMix: jobResult.mix_instructions,
      currentIndex: 0
    });

    console.log(
      `Loaded mix with ${jobResult.mix_instructions.transitions.length} transitions`
    );
    return true;
  }
);

/**
 * Start auto DJ
 */
export const startAutoDJAtom = atom(null, async (get, set) => {
  const djState = get(djAgentAtom);
  console.log("Starting DJ, current state:", djState);
  if (!djState.currentMix) {
    console.error("No mix loaded");
    return false;
  }

  if (djState.isActive) {
    console.warn("Auto DJ already active");
    return false;
  }

  set(pauseDeckAtom, "deckA");
  set(pauseDeckAtom, "deckB");

  // load whatever tracks current autoplay dj position is
  const currentQueue = get(queueAtom).queue;
  const leadingDeckName = djState.currentIndex % 2 === 0 ? "deckA" : "deckB";

  const fromTrack = currentQueue[djState.currentIndex];
  const toTrack =
    currentQueue[
      djState.currentIndex + 1 < currentQueue.length
        ? djState.currentIndex + 1
        : djState.currentIndex
    ];

  set(loadTrackAtom, {
    track: currentQueue[djState.currentIndex],
    deck: leadingDeckName
  });

  if (djState.currentIndex < currentQueue.length - 1) {
    set(loadTrackAtom, {
      track: currentQueue[djState.currentIndex + 1],
      deck: leadingDeckName === "deckA" ? "deckB" : "deckA"
    });
  }

  console.log("loading new tracks");
  // Start playing
  set(playDeckAtom, { deck: leadingDeckName });

  set(djAgentAtom, {
    ...djState,
    isActive: true,
    startTime: Date.now()
  });

  const currentTransition =
    djState.currentMix.transitions[djState.currentIndex];
  console.log("current transition is:", currentTransition);
  let fromDeckElement: HTMLAudioElement;
  let toDeckElement: HTMLAudioElement;
  if (leadingDeckName === "deckA") {
    fromDeckElement = get(deckAAudioElementAtom);
    toDeckElement = get(deckBAudioElementAtom);
  } else {
    fromDeckElement = get(deckBAudioElementAtom);
    toDeckElement = get(deckAAudioElementAtom);
  }
  const strat = new CrossfadeStrategy(
    get,
    set,
    "crossfade",
    currentTransition,
    fromTrack,
    toTrack,
    fromTrack.id,
    toTrack.id,
    fromDeckElement,
    toDeckElement,
    leadingDeckName,
    {
      adjustedPlaybackRateFrom: fromDeckElement.playbackRate, // keep normal
      adjustedPlaybackRateTo: fromTrack.bpm / toTrack.bpm
    }
  );

  toggleDjStateFrame(get, set, strat);

  console.log("Auto DJ started");
  return true;
});

/**
 * Stop auto DJ
 */
export const stopAutoDJAtom = atom(null, (get, set) => {
  const djState = get(djAgentAtom);

  set(pauseDeckAtom, "deckA");
  set(pauseDeckAtom, "deckB");

  set(djAgentAtom, {
    ...djState,
    isActive: false
  });

  console.log("Auto DJ stopped");
});

const toggleDjStateFrame = (
  get: Getter,
  set: Setter,
  strat: TransitionStrategy
) => {
  let currentFrame = -1;
  const animate = () => {
    console.log("Animate", currentFrame);
    const djAgent = get(djAgentAtom);
    if (!djAgent.isActive) {
      cancelAnimationFrame(currentFrame);
      return;
    }

    // check if current track (which can be a or b) is at a transition point

    // inside a transition point calculate what the state should be and set it to that state ie crossfade %, loudness, bpm etc
    strat.tick();
    currentFrame = requestAnimationFrame(animate);
  };
  const agent = get(djAgentAtom);
  if (agent.isActive) {
    // turning off animate
    currentFrame = requestAnimationFrame(animate);
  } else {
    // turning it on
  }

  // scroll(timestamp, distanceToScroll, secondsToScroll)
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

  let currentTrack = null;
  if (deckA?.isPlaying) {
    currentTrack = deckA.track;
  } else if (deckB?.isPlaying) {
    currentTrack = deckB.track;
  }

  const state: DJState = {
    status: djAgent.isActive ? "playing" : "paused",
    current_position: djAgent.currentIndex,
    current_track: currentTrack || undefined
  };

  return state;
});

// technique: 'crossfade' | 'smooth_blend' | 'quick_cut' | 'beatmatch' | 'creative';

interface TransitionStrategy {
  get: Getter;
  set: Setter;
  technique: TransitionTechnique;
  transition: Transition;
  fromDeckTrack: Track;
  toDeckTrack: Track;
  fromDeckTrackId: string;
  toDeckTrackId: string;
  fromDeckElement: HTMLAudioElement;
  toDeckElement: HTMLAudioElement;
  fromDeckName: "deckA" | "deckB";

  apply(): void;
  tick(): void;
  matchBPM:
    | {
        adjustedPlaybackRateFrom: number;
        adjustedPlaybackRateTo: number;
      }
    | undefined;
}
class CrossfadeStrategy implements TransitionStrategy {
  get: Getter;
  set: Setter;
  technique: "crossfade";
  transition: Transition;
  fromDeckTrack: Track;
  toDeckTrack: Track;
  fromDeckTrackId: string;
  toDeckTrackId: string;
  fromDeckElement: HTMLAudioElement;
  toDeckElement: HTMLAudioElement;
  fromDeckName: "deckA" | "deckB";
  matchBPM:
    | {
        adjustedPlaybackRateFrom: number;
        adjustedPlaybackRateTo: number;
      }
    | undefined;

  constructor(
    get: Getter,
    set: Setter,
    technique: "crossfade",
    transition: Transition,
    fromDeckTrack: Track,
    toDeckTrack: Track,
    fromDeckTrackId: string,
    toDeckTrackId: string,
    fromDeckElement: HTMLAudioElement,
    toDeckElement: HTMLAudioElement,
    fromDeckName: "deckA" | "deckB",
    matchBPM?: {
      adjustedPlaybackRateFrom: number;
      adjustedPlaybackRateTo: number;
    }
  ) {
    this.get = get;
    this.set = set;
    this.technique = technique;
    this.transition = transition;
    this.fromDeckElement = fromDeckElement;
    this.toDeckElement = toDeckElement;
    this.fromDeckTrackId = fromDeckTrackId;
    this.toDeckTrackId = toDeckTrackId;
    this.fromDeckTrack = fromDeckTrack;
    this.toDeckTrack = toDeckTrack;
    this.matchBPM = matchBPM;
    this.fromDeckName = fromDeckName;
  }
  apply(): void {}

  tick() {
    console.log("Tick!");

    // 3 cases before transiton start
    if (this.fromDeckElement.currentTime < this.transition.transition_start) {
      console.log("do nothing");
      // do nothing or maybe make sure b element is silent
      if (!this.toDeckElement.paused) {
        this.toDeckElement.pause();
        if (this.toDeckElement.currentTime !== 0) {
          this.toDeckElement.currentTime = 0;
        }
      }
    }
    // Past transtion duration
    else if (
      this.fromDeckElement.currentTime >
      this.transition.transition_start + this.transition.transition_duration
    ) {
      if (!this.fromDeckElement.paused) {
        this.fromDeckElement.pause();
        if (
          this.fromDeckElement.currentTime !== this.fromDeckElement.duration
        ) {
          this.fromDeckElement.currentTime = this.fromDeckElement.duration;
        }
      }
      console.log("FROM TRACK SHOULD BE DONE");
    }
    // During
    else if (
      this.fromDeckElement.currentTime > this.transition.transition_start &&
      this.fromDeckElement.currentTime <
        this.transition.transition_start + this.transition.transition_duration
    ) {
      // match bpm
      if (
        this.matchBPM &&
        this.matchBPM.adjustedPlaybackRateFrom !==
          this.fromDeckElement.playbackRate &&
        this.matchBPM.adjustedPlaybackRateTo !==
          this.fromDeckElement.playbackRate
      ) {
        this.fromDeckElement.playbackRate =
          this.matchBPM.adjustedPlaybackRateFrom;
        this.toDeckElement.playbackRate = this.matchBPM.adjustedPlaybackRateTo;
      }

      const transtionPosition =
        this.fromDeckElement.currentTime - this.transition.transition_start;

      // This is potentially a little brittle and maybe timing won't sound right..
      if (this.toDeckElement.paused) {
        console.log("WAS PAUSED NOW STARTING LOL", this.fromDeckName);
        const mixInPoint = this.toDeckTrack.mix_in_point ?? 0;
        const offset = mixInPoint + transtionPosition;
        this.set(playDeckAtom, {
          deck: this.fromDeckName === "deckA" ? "deckB" : "deckA",
          offset
        });
      }

      // percent of transition completed
      const crossfadeAmount =
        transtionPosition / this.transition.transition_duration;
      this.set(setCrossfaderAtom, crossfadeAmount);
      console.log("WITHIN TRANSITION", transtionPosition, crossfadeAmount);
    } else {
      console.log("hmm i think this shouldn't happen");
    }
  }
}

export type CurrentSupportedTransitons = CrossfadeStrategy;

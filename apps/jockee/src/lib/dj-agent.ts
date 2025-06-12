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
  setCrossfaderAtom,
  setDeckBpmAtom
} from "./audio/Audio";

const MAGIC_BPM_DELTA_UNIT = 0.005;

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

  // Create initial transition strategy using helper function
  const initialStrategy = createTransitionStrategy(
    get,
    set,
    currentTransition,
    fromTrack,
    toTrack,
    leadingDeckName
  );

  toggleDjStateFrame(get, set, initialStrategy);

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

/**
 * Helper function to create a transition strategy
 */
const createTransitionStrategy = (
  get: Getter,
  set: Setter,
  transition: Transition,
  fromTrack: Track,
  toTrack: Track,
  fromDeckName: "deckA" | "deckB"
): TransitionStrategy => {
  const fromDeckElement =
    fromDeckName === "deckA"
      ? get(deckAAudioElementAtom)
      : get(deckBAudioElementAtom);
  const toDeckElement =
    fromDeckName === "deckA"
      ? get(deckBAudioElementAtom)
      : get(deckAAudioElementAtom);

  // For now, we only support crossfade, but this can be extended
  const technique = transition.technique || "crossfade";

  if (technique === "crossfade") {
    return new CrossfadeStrategy(
      get,
      set,
      "crossfade",
      transition,
      fromTrack,
      toTrack,
      fromTrack.id,
      toTrack.id,
      fromDeckElement,
      toDeckElement,
      fromDeckName,
      {
        adjustedPlaybackRateFrom: fromDeckElement.playbackRate,
        adjustedPlaybackRateTo: fromTrack.bpm / toTrack.bpm
      }
    );
  } else if (technique === "quick_cut") {
    return new QuickCutStrategy(
      get,
      set,
      "quick_cut",
      transition,
      fromTrack,
      toTrack,
      fromTrack.id,
      toTrack.id,
      fromDeckElement,
      toDeckElement,
      fromDeckName,
      {
        adjustedPlaybackRateFrom: fromDeckElement.playbackRate,
        adjustedPlaybackRateTo: fromTrack.bpm / toTrack.bpm
      }
    );
  }

  // Default to crossfade for unsupported techniques
  return new CrossfadeStrategy(
    get,
    set,
    "crossfade",
    transition,
    fromTrack,
    toTrack,
    fromTrack.id,
    toTrack.id,
    fromDeckElement,
    toDeckElement,
    fromDeckName,
    {
      adjustedPlaybackRateFrom: fromDeckElement.playbackRate,
      adjustedPlaybackRateTo: fromTrack.bpm / toTrack.bpm
    }
  );
};

/**
 * Setup the next transition
 */
const setupNextTransition = (
  get: Getter,
  set: Setter,
  currentIndex: number
): TransitionStrategy | null => {
  const djState = get(djAgentAtom);
  const currentQueue = get(queueAtom).queue;

  // Check if we have more transitions to process
  if (
    !djState.currentMix ||
    currentIndex + 1 >= djState.currentMix.transitions.length
  ) {
    console.log("No more transitions to setup");
    return null;
  }

  // Check if we have enough tracks for the next transition
  if (currentIndex + 2 >= currentQueue.length) {
    console.log("No more tracks in queue for next transition");
    return null;
  }

  const nextTransition = djState.currentMix.transitions[currentIndex + 1];
  const fromTrack = currentQueue[currentIndex + 1]; // The "to" track becomes the "from" track
  const toTrack = currentQueue[currentIndex + 2]; // Next track in sequence

  // Determine which deck is currently the "to" deck (it becomes the "from" deck for next transition)
  const currentLeadingDeck = currentIndex % 2 === 0 ? "deckA" : "deckB";
  const nextFromDeck = currentLeadingDeck === "deckA" ? "deckB" : "deckA"; // The current "to" deck

  // Load the track after next on the deck that just finished
  if (currentIndex + 2 < currentQueue.length) {
    set(loadTrackAtom, {
      track: currentQueue[currentIndex + 2],
      deck: currentLeadingDeck // Load track after next on the deck that just finished playing
    });
  }

  // Update DJ state to the next transition
  set(djAgentAtom, {
    ...djState,
    currentIndex: currentIndex + 1
  });

  console.log(
    `Setting up transition ${currentIndex + 2}: ${fromTrack.title} -> ${
      toTrack.title
    }`
  );

  return createTransitionStrategy(
    get,
    set,
    nextTransition,
    fromTrack,
    toTrack,
    nextFromDeck
  );
};

const toggleDjStateFrame = (
  get: Getter,
  set: Setter,
  initialStrategy: TransitionStrategy
) => {
  let currentFrame = -1;
  let currentStrategy: TransitionStrategy | null = initialStrategy;

  const animate = () => {
    console.log("Animate", currentFrame);
    const djAgent = get(djAgentAtom);

    if (!djAgent.isActive) {
      cancelAnimationFrame(currentFrame);
      return;
    }

    if (!currentStrategy) {
      console.log("No current strategy, stopping DJ");
      set(stopAutoDJAtom);
      return;
    }

    // Run the current transition strategy
    currentStrategy.tick();

    // Check if current transition is complete
    if (currentStrategy.isComplete) {
      console.log("Current transition complete, setting up next transition");

      // Setup next transition
      const nextStrategy = setupNextTransition(get, set, djAgent.currentIndex);

      if (nextStrategy) {
        currentStrategy = nextStrategy;
        console.log("Next transition ready");
      } else {
        console.log("All transitions complete, stopping Auto DJ");
        set(stopAutoDJAtom);
        return;
      }
    }

    currentFrame = requestAnimationFrame(animate);
  };

  const agent = get(djAgentAtom);
  if (agent.isActive) {
    currentFrame = requestAnimationFrame(animate);
  }
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
  isComplete: boolean;

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
  isComplete: boolean;
  matchedBpm: boolean;

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
    this.isComplete = false;
    this.matchedBpm = false;
  }
  apply(): void {}

  tick() {
    if (this.isComplete) {
      // do nothing
      return;
    }

    // 3 cases before transiton start
    if (this.fromDeckElement.currentTime < this.transition.transition_start) {
      // do nothing or maybe make sure b element is silent
      if (!this.toDeckElement.paused) {
        this.toDeckElement.pause();
      }
      if (this.toDeckElement.currentTime !== 0) {
        this.toDeckElement.currentTime = 0;
      }

      // secretly boost or lower bpm back to original song level

      if (this.fromDeckElement.playbackRate < 1.0) {
        const nextBpm = Math.min(
          (this.fromDeckElement.playbackRate + MAGIC_BPM_DELTA_UNIT) *
            this.fromDeckTrack.bpm,
          this.fromDeckTrack.bpm
        );
        this.set(setDeckBpmAtom, {
          deck: this.fromDeckName,
          bpm: nextBpm
        });
      } else if (this.fromDeckElement.playbackRate > 1.0) {
        const nextBpm = Math.max(
          (this.fromDeckElement.playbackRate - MAGIC_BPM_DELTA_UNIT) *
            this.fromDeckTrack.bpm,
          this.fromDeckTrack.bpm
        );
        this.set(setDeckBpmAtom, {
          deck: this.fromDeckName,
          bpm: nextBpm
        });
      }
    }
    // Past transtion duration
    else if (
      this.fromDeckElement.currentTime >=
      this.transition.transition_start + this.transition.transition_duration
    ) {
      if (!this.isComplete) {
        this.isComplete = true;
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
      // if (
      //   this.matchBPM &&
      //   this.matchBPM.adjustedPlaybackRateFrom !==
      //     this.fromDeckElement.playbackRate &&
      //   this.matchBPM.adjustedPlaybackRateTo !==
      //     this.fromDeckElement.playbackRate
      // ) {
      //   this.fromDeckElement.playbackRate =
      //     this.matchBPM.adjustedPlaybackRateFrom;
      //   this.toDeckElement.playbackRate = this.matchBPM.adjustedPlaybackRateTo;
      // }
      if (!this.matchedBpm) {
        console.log("SETTING BPM");
        this.set(setDeckBpmAtom, {
          deck: this.fromDeckName === "deckA" ? "deckB" : "deckA",
          bpm: this.fromDeckTrack.bpm
        });
        this.matchedBpm = true;
      }

      let transitionPosition =
        this.fromDeckElement.currentTime - this.transition.transition_start;

      // if a transition actually goes PAST the end time of the from deck's track...
      if (this.fromDeckElement.paused) {
        const leftoverAmount =
          this.transition.transition_start +
          this.transition.transition_duration -
          this.fromDeckElement.duration;
        transitionPosition = Math.min(
          this.toDeckElement.currentTime -
            (this.toDeckTrack.mix_in_point ?? 0) -
            leftoverAmount,
          this.transition.transition_duration
        );
      }

      // This is potentially a little brittle and maybe timing won't sound right..
      if (this.toDeckElement.paused) {
        console.log("WAS PAUSED NOW STARTING LOL", this.fromDeckName);
        const mixInPoint = this.toDeckTrack.mix_in_point ?? 0;
        const offset = mixInPoint + transitionPosition;
        this.set(playDeckAtom, {
          deck: this.fromDeckName === "deckA" ? "deckB" : "deckA",
          offset
        });
      }

      // percent of transition completed
      const crossfadeAmount =
        transitionPosition / this.transition.transition_duration;

      if (this.fromDeckName === "deckA") {
        this.set(setCrossfaderAtom, crossfadeAmount);
      } else {
        this.set(setCrossfaderAtom, 1 - crossfadeAmount);
      }
      if (transitionPosition >= this.transition.transition_duration) {
        this.isComplete = true;
      }
      // this is horrible maybe but if a transition will go PAST the end of a song...

      console.log("WITHIN TRANSITION", transitionPosition, crossfadeAmount);
    } else {
      console.log("hmm i think this shouldn't happen");
    }
  }
}

export type CurrentSupportedTransitons = CrossfadeStrategy | QuickCutStrategy;

class QuickCutStrategy implements TransitionStrategy {
  get: Getter;
  set: Setter;
  technique: "quick_cut";
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
  isComplete: boolean;
  hasCut: boolean;

  constructor(
    get: Getter,
    set: Setter,
    technique: "quick_cut",
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
    this.isComplete = false;
    this.hasCut = false;
  }

  apply(): void {}

  tick() {
    if (this.isComplete) {
      return;
    }

    // Before transition start - keep preparing
    if (this.fromDeckElement.currentTime < this.transition.transition_start) {
      // Ensure the to-deck is paused and ready
      if (!this.toDeckElement.paused) {
        this.toDeckElement.pause();
      }
      if (this.toDeckElement.currentTime !== 0) {
        this.toDeckElement.currentTime = 0;
      }

      // For quick cuts, we don't need to adjust BPM beforehand
      // Just let the from track play at its current rate
      return;
    }

    // At or after transition start - execute the quick cut
    if (
      !this.hasCut &&
      this.fromDeckElement.currentTime >= this.transition.transition_start
    ) {
      console.log("EXECUTING QUICK CUT");

      // Quick cut: immediately start the next track from the beginning (radio DJ style)
      // No mix points - just cut to the start of the song
      this.set(playDeckAtom, {
        deck: this.fromDeckName === "deckA" ? "deckB" : "deckA",
        offset: 0
      });

      // Set crossfader to fully switch to the new track
      // For quick cut, we want an immediate switch
      if (this.fromDeckName === "deckA") {
        this.set(setCrossfaderAtom, 1.0); // Full to deck B
      } else {
        this.set(setCrossfaderAtom, 0.0); // Full to deck A
      }

      // Pause the from deck after a very brief moment to avoid audio glitch
      setTimeout(() => {
        this.set(pauseDeckAtom, this.fromDeckName);
      }, 50); // 50ms delay to avoid immediate audio cutting

      this.hasCut = true;

      // For quick cuts, mark as complete almost immediately
      // Use a short duration to allow for any audio settling
      setTimeout(() => {
        this.isComplete = true;
        console.log("QUICK CUT COMPLETE");
      }, Math.min(this.transition.transition_duration * 1000, 500)); // Max 500ms

      return;
    }

    // After cut is executed, just wait for completion
    if (this.hasCut && !this.isComplete) {
      // Quick cut should be complete very quickly
      // This is handled by the setTimeout above
      return;
    }
  }
}

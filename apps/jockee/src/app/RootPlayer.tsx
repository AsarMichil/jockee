"use client";

import { useAudioStore } from "@/lib/audio/AudioStoreProvider";

export default function RootPlayer() {
  const { audioContext } = useAudioStore((state) => state);
  // console.log(
  //   "root player context",
  //   audioContextManager,
  //   audioContext,
  //   deckA,
  //   deckB
  // );

  return (
    <div>
      <div>RootPlayer</div>
      {audioContext && <div>AudioContext {audioContext.sampleRate}</div>}
    </div>
  );
}

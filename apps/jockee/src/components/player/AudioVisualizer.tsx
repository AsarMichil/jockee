import {
  useAudioActions,
  useDeckAAudioElement,
  useDeckBAudioElement,
  useAutoplay
} from "@/lib/audio/AudioStoreProvider";
import WavesurferPlayer from "@wavesurfer/react";
import { useEffect, useMemo, useState } from "react";
import type WaveSurfer from "wavesurfer.js";
import { deckAAtom } from "@/lib/audio/Audio";
import { deckBAtom } from "@/lib/audio/Audio";
import { useAtomValue } from "jotai";
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions.esm.js";

export default function WaveformVisualizer({
  deck,
  loaded
}: {
  deck: "A" | "B";
  trackTitle: string;
  loaded: boolean;
}) {
  const [wavesurfer, setWavesurfer] = useState<WaveSurfer | null>(null);
  const deckState = useAtomValue(deck === "A" ? deckAAtom : deckBAtom);
  const beatTimestamps = deckState?.track?.beat_timestamps;
  console.log("beatTimestamps", beatTimestamps);
  const regionsPlugin = useMemo(() => RegionsPlugin.create(), []);
  const plugins = useMemo(() => [regionsPlugin], [regionsPlugin]);

  useEffect(() => {
    console.log("useEffect", beatTimestamps, wavesurfer);
    if (beatTimestamps && beatTimestamps.length > 0 && wavesurfer) {
      for (let i = 0; i < beatTimestamps.length; i++) {
        regionsPlugin.addRegion({
          start: beatTimestamps[i],
          drag: false,
          color: "#c6d2ff"
          
        });
      }
    }
  });

  // Use Jotai hooks
  const { setDeckAWavesurfer, setDeckBWavesurfer, autoplayNextTrack } =
    useAudioActions();
  const [deckAAudioElement] = useDeckAAudioElement();
  const [deckBAudioElement] = useDeckBAudioElement();
  const [autoplay] = useAutoplay();
  // const beatTimestamps = useAtomValue(deckstat)

  const audioElement = deck === "A" ? deckAAudioElement : deckBAudioElement;

  const onReady = (ws: WaveSurfer) => {
    console.log("onReady", ws);
    setWavesurfer(ws);

    // Use the appropriate setter based on deck
    if (deck === "A") {
      setDeckAWavesurfer(ws);
    } else {
      setDeckBWavesurfer(ws);
    }
  };

  const handleEnded = () => {
    console.log("onFinish");
    if (autoplay) {
      autoplayNextTrack(deck === "A" ? "deckA" : "deckB");
    }
  };

  if (!loaded) {
    return <div>Loading...</div>;
  }

  return (
    <WavesurferPlayer
      onFinish={handleEnded}
      onReady={onReady}
      height={100}
      waveColor="#372aac"
      media={audioElement}
      dragToSeek={true}
      plugins={plugins}
      minPxPerSec={300}
    />
  );
}

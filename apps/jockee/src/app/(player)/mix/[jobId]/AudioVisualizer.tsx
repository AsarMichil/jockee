// "use client";

// import { useAudioStore } from "@/lib/audio/AudioStoreProvider";
// import { useMemo, useCallback, useRef } from "react";
// import { useWavesurfer } from "@wavesurfer/react";
// import Timeline from "wavesurfer.js/dist/plugins/timeline.esm.js";

// const formatTime = (seconds: number) =>
//   [seconds / 60, seconds % 60]
//     .map((v) => `0${Math.floor(v)}`.slice(-2))
//     .join(":");

// export default function WaveformVisualizer({
//   deck
// }: {
//   deck: "deckA" | "deckB";
// }) {
//   console.log("outer rendrein");
//   const audioElement = useAudioStore((state) => state[deck]?.audioElement);

//   if (!audioElement) return null;
//   return <WaveformVisualizerInternal audioElement={audioElement} />;
// }

// // A React component that will render wavesurfer
// function WaveformVisualizerInternal({
//   audioElement
// }: {
//   audioElement: HTMLMediaElement;
// }) {
//   console.log("rerrerendering");
//   const containerRef = useRef(null);
// //   const { wavesurfer, isPlaying, currentTime } = useWavesurfer({
// //     container: containerRef,
// //     height: 100,
// //     waveColor: "rgb(200, 0, 200)",
// //     progressColor: "rgb(100, 0, 100)",
// //     media: audioElement,
// //     plugins: useMemo(() => [Timeline.create()], [])
// //   });

//   const onPlayPause = useCallback(() => {
//     wavesurfer?.playPause();
//   }, [wavesurfer]);

//   return (
//     <>
//       <div ref={containerRef} />

//       <p>Current audio: {audioElement?.src}</p>

//       <p>Current time: {formatTime(currentTime)}</p>

//       <div style={{ margin: "1em 0", display: "flex", gap: "1em" }}>
//         <button onClick={onPlayPause} style={{ minWidth: "5em" }}>
//           {isPlaying ? "Pause" : "Play"}
//         </button>
//       </div>
//     </>
//   );
// }

import { useAudioStore } from "@/lib/audio/AudioStoreProvider";
import WavesurferPlayer from "@wavesurfer/react";
import { useState } from "react";

export default function WaveformVisualizer({
  deck
}: {
  deck: "deckA" | "deckB";
}) {
  const audioElement = useAudioStore((state) => state[deck]?.audioElement);
  console.log("audioElement BLAH", audioElement);
  if (!audioElement) return null;
  return <AudioVisualizerInner audioElement={audioElement} />;
}

function AudioVisualizerInner({
  audioElement
}: {
  audioElement: HTMLMediaElement;
}) {
  console.log("innner render");
  const [wavesurfer, setWavesurfer] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const onReady = (ws) => {
    setWavesurfer(ws);
    setIsPlaying(false);
  };

  const onPlayPause = () => {
    wavesurfer?.playPause();
  };

  return (
    <>
      <WavesurferPlayer
        height={100}
        waveColor="violet"
        media={audioElement}
        onReady={onReady}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
      />

      <button onClick={onPlayPause}>{isPlaying ? "Pause" : "Play"}</button>
    </>
  );
}

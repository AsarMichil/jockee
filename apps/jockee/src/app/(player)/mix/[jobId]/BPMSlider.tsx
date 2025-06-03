import { Slider } from "@/components/ui/slider";
import { useAudioStore } from "@/lib/audio/AudioStoreProvider";
import { RotateCcw } from "lucide-react";
import { useState } from "react";

export default function BPMSlider({ deckName }: { deckName: string }) {
  const derivedDeckName = deckName === "A" ? "deckA" : "deckB";
  const deck = useAudioStore((state) => state[derivedDeckName]);
  const setDeckBpm = useAudioStore((state) => state.setDeckBpm);
  const [bpm, setBpmInner] = useState([deck?.track?.bpm || 0]);

  const setBpm = (value: number[]) => {
    const toNearestDecimal = Math.round(value[0] * 10) / 10;
    setDeckBpm(derivedDeckName, toNearestDecimal);
    setBpmInner([toNearestDecimal]);
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm text-gray-600">
        <span>BPM</span>
        <span className="flex items-center gap-2">
          {bpm[0]}
          {/* Reset to original bpm */}
          <button onClick={() => setBpm([deck?.track?.bpm || 0])}>
            <RotateCcw className="w-4 h-4" />
          </button>
        </span>
      </div>
      <Slider
        min={1}
        max={400}
        value={bpm}
        onValueChange={setBpm}
        step={0.1}
        className="w-full"
        disabled={!deck?.track}
      />
    </div>
  );
}

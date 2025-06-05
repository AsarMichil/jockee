import { Slider } from "@/components/ui/slider";
import { deckAAtom, deckBAtom, setDeckBpmAtom } from "@/lib/audio/Audio";
import { useAtomValue, useSetAtom } from "jotai";
import { RotateCcw } from "lucide-react";
import { useEffect, useState } from "react";

export default function BPMSlider({ deckName }: { deckName: string }) {
  const derivedDeckName = deckName === "A" ? "deckA" : "deckB";

  // Use individual deck hooks instead of selector
  const deckA = useAtomValue(deckAAtom);
  const deckB = useAtomValue(deckBAtom);
  const deck = deckName === "A" ? deckA : deckB;
  const setDeckBpm = useSetAtom(setDeckBpmAtom);
  const deckBpm = deck?.track?.bpm ?? 0;
  console.log("BPM SLIDER", deckA, deckB, deck, deckName, deckBpm);

  const [bpm, setBpmInner] = useState([deckBpm]);
  // Sync local state with atom value when it changes
  useEffect(() => {
    setBpmInner([deckBpm]);
  }, [deckBpm]);

  const setBpm = (value: number[]) => {
    const toNearestDecimal = Math.round(value[0] * 10) / 10;
    setDeckBpm({ deck: derivedDeckName, bpm: toNearestDecimal });
    setBpmInner([toNearestDecimal]);
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm text-gray-600">
        <span>BPM</span>
        <span className="flex items-center gap-2">
          {bpm[0]}
          {/* Reset to original bpm */}
          <button onClick={() => setBpm([deckBpm ?? 0])}>
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

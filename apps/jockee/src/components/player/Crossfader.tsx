import { Slider } from "@/components/ui/slider";
import { crossfaderAtom, setCrossfaderAtom } from "@/lib/audio/Audio";
import { useAtomValue, useSetAtom } from "jotai";

export default function Crossfader() {
  const crossfaderPosition = useAtomValue(crossfaderAtom);
  const setCrossfaderAction = useSetAtom(setCrossfaderAtom);

  const setCrossfader = (value: number[]) => {
    setCrossfaderAction(value[0]);
  };

  return (
    <div className="space-y-4">
      <div className="text-center">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Crossfader</h3>
        <div className="flex justify-between text-xs text-gray-500 mb-2">
          <span>A</span>
          <span>CENTER</span>
          <span>B</span>
        </div>
        <Slider
          value={[crossfaderPosition]}
          onValueChange={setCrossfader}
          min={0}
          max={1}
          step={0.001}
          className="w-full"
        />
        <div className="text-xs text-gray-500 mt-1">
          {crossfaderPosition === 0 && "Deck A"}
          {crossfaderPosition === 1 && "Deck B"}
          {crossfaderPosition > 0 && crossfaderPosition < 1 && "Mixed"}
        </div>
      </div>
    </div>
  );
}

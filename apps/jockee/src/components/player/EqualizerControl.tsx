import { useAtomValue, useSetAtom } from "jotai";
import { 
  deckAEQAtom, 
  deckBEQAtom, 
  setEQBandAtom, 
  resetEQAtom 
} from "@/lib/audio/Audio";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { RotateCcw } from "lucide-react";

interface EqualizerControlProps {
  deck: "deckA" | "deckB";
  title: string;
}

export default function EqualizerControl({ deck, title }: EqualizerControlProps) {
  const eq = useAtomValue(deck === "deckA" ? deckAEQAtom : deckBEQAtom);
  const setEQBand = useSetAtom(setEQBandAtom);
  const resetEQ = useSetAtom(resetEQAtom);

  const handleBandChange = (band: "low" | "mid" | "high", value: number[]) => {
    setEQBand({ deck, band, value: value[0] });
  };

  const handleReset = () => {
    resetEQ(deck);
  };

  return (
    <div className="space-y-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleReset}
          className="h-6 w-6 p-0 text-gray-500 hover:text-gray-700"
        >
          <RotateCcw className="h-3 w-3" />
        </Button>
      </div>
      
      <div className="flex justify-center space-x-8">
        {/* High */}
        <div className="flex flex-col items-center space-y-2">
          <div className="h-32 flex items-center justify-center">
            <Slider
              value={[eq.high]}
              onValueChange={(value) => handleBandChange("high", value)}
              max={40}
              min={-40}
              step={0.5}
              orientation="vertical"
              className="h-28"
            />
          </div>
          <div className="text-center min-w-20">
            <div className="text-xs font-medium text-gray-600">HIGH</div>
            <div className="text-xs text-gray-500">3.2kHz</div>
            <div className="text-xs font-mono text-gray-700 bg-white px-1 rounded">
              {eq.high > 0 ? '+' : ''}{eq.high.toFixed(1)}dB
            </div>
          </div>
        </div>

        {/* Mid */}
        <div className="flex flex-col items-center space-y-2">
          <div className="h-32 flex items-center justify-center">
            <Slider
              value={[eq.mid]}
              onValueChange={(value) => handleBandChange("mid", value)}
              max={40}
              min={-40}
              step={0.5}
              orientation="vertical"
              className="h-28"
            />
          </div>
          <div className="text-center min-w-20">
            <div className="text-xs font-medium text-gray-600">MID</div>
            <div className="text-xs text-gray-500">1kHz</div>
            <div className="text-xs font-mono text-gray-700 bg-white px-1 rounded">
              {eq.mid > 0 ? '+' : ''}{eq.mid.toFixed(1)}dB
            </div>
          </div>
        </div>

        {/* Low */}
        <div className="flex flex-col items-center space-y-2">
          <div className="h-32 flex items-center justify-center">
            <Slider
              value={[eq.low]}
              onValueChange={(value) => handleBandChange("low", value)}
              max={40}
              min={-40}
              step={0.5}
              orientation="vertical"
              className="h-28"
            />
          </div>
          <div className="text-center min-w-20">
            <div className="text-xs font-medium text-gray-600">LOW</div>
            <div className="text-xs text-gray-500">320Hz</div>
            <div className="text-xs font-mono text-gray-700 bg-white px-1 rounded">
              {eq.low > 0 ? '+' : ''}{eq.low.toFixed(1)}dB
            </div>
          </div>
        </div>
      </div>
      
      {/* EQ Curve Visualization (decorative) */}
      <div className="h-8 bg-gray-100 rounded border relative overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-xs text-gray-400 font-mono">EQ CURVE</div>
        </div>
        <svg 
          className="absolute inset-0 w-full h-full" 
          viewBox="0 0 100 32" 
          preserveAspectRatio="none"
        >
          <path
            d={`M 0,16 Q 25,${16 - eq.low * 0.3} 33,${16 - eq.low * 0.3} Q 50,${16 - eq.mid * 0.3} 66,${16 - eq.high * 0.3} Q 75,${16 - eq.high * 0.3} 100,16`}
            stroke="rgb(99, 102, 241)"
            strokeWidth="2"
            fill="none"
            opacity="0.6"
          />
        </svg>
      </div>
    </div>
  );
} 
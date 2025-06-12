import DJNotPlaying from "../DJGuy/DJ-Not-Playing";
import DJPlaying from "../DJGuy/DJ-Playing";

export default function AutoDJGuy({ isPlaying }: { isPlaying: boolean }) {
  return (
    // either dj guy playing or dj guy not playing
    <div className="flex flex-col items-center justify-center">
      {isPlaying ? (
        <DJPlaying />
      ) : (
        <DJNotPlaying />
      )}
    </div>
  );
}

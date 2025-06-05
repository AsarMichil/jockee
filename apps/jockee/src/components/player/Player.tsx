import { useAudioActions } from "@/lib/audio/AudioStoreProvider";
import { AnalysisJob, Track } from "@/lib/types";
import { use, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TrackProgress } from "@/components/TrackProgress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from "@/components/ui/dialog";
import {
  Play,
  SkipForward,
  SkipBack,
  Music,
  Clock,
  Zap,
  Headphones
} from "lucide-react";
import { PlaybackSlider } from "./PlaybackSlider";
import BPMSlider from "./BPMSlider";
import WaveformVisualizer from "./AudioVisualizer";
import VolumeSlider from "./VolumeSlider";
import Crossfader from "./Crossfader";
import {
  deckAAtom,
  deckBAtom,
  queueAtom,
  scrubDeckAtom
} from "@/lib/audio/Audio";
import { useAtomValue, useSetAtom } from "jotai";
import { APlayButton } from "./BigAssPlayButton";
import { BPlayButton } from "./BigAssPlayButton";
import { AutoplayButton } from "./AutoplayButton";

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

const formatBPM = (bpm: number) => {
  return `${Math.round(bpm)} BPM`;
};

export default function Player({ data }: { data: Promise<AnalysisJob> }) {
  const job = use(data);

  // Use Jotai hooks instead of Zustand selectors
  const { setQueuedTracks, loadTrack, advanceQueue } = useAudioActions();

  const deckA = useAtomValue(deckAAtom);
  const deckB = useAtomValue(deckBAtom);
  console.log("deckA", deckA);
  console.log("deckB", deckB);

  // Dialog state
  const [showLoadDialog, setShowLoadDialog] = useState(true);
  const [isAudioInitialized, setIsAudioInitialized] = useState(false);

  useEffect(() => {
    if (job.tracks) {
      setQueuedTracks(job.tracks);
      // Don't auto-load tracks - wait for user interaction
    }
  }, [job.tracks, setQueuedTracks]);

  const initializeAudioAndLoadTrack = async (track: Track, deck: "A" | "B") => {
    try {
      // Load the track to the specified deck
      await loadTrack({ track, deck: deck === "A" ? "deckA" : "deckB" });

      setIsAudioInitialized(true);
      console.log(`Track "${track.title}" loaded to Deck ${deck}`);
    } catch (error) {
      console.error(`Failed to load track to Deck ${deck}:`, error);
    }
  };

  const handleInitialLoad = async () => {
    if (!job.tracks || job.tracks.length === 0) return;
    try {
      // Load first track to Deck A
      await initializeAudioAndLoadTrack(job.tracks[0], "A");
      // no need to advance queue here, starts at 0
      // Load second track to Deck B if available
      if (job.tracks.length >= 2) {
        await initializeAudioAndLoadTrack(job.tracks[1], "B");
        advanceQueue();
      }

      setShowLoadDialog(false);
    } catch (error) {
      console.error("Failed to initialize audio and load tracks:", error);
    }
  };

  const handleLoadToDeck = async (track: Track, deck: "A" | "B") => {
    try {
      await initializeAudioAndLoadTrack(track, deck);
    } catch (error) {
      console.error(`Failed to load track to Deck ${deck}:`, error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white">
      {/* Load Tracks Dialog */}
      <Dialog open={showLoadDialog} onOpenChange={setShowLoadDialog}>
        <DialogContent className="sm:max-w-md" showCloseButton={false}>
          <DialogHeader>
            <DialogTitle>Initialize Audio Player</DialogTitle>
          </DialogHeader>

          <div className="flex items-center justify-center mb-4">
            <div className="p-3 bg-blue-100 rounded-full">
              <Headphones className="h-8 w-8 text-blue-600" />
            </div>
          </div>
          <DialogDescription className="text-center">
            Your mix is ready! Click below to initialize the audio system and
            load your tracks to the decks.
          </DialogDescription>

          {job.tracks && job.tracks.length >= 2 && (
            <div className="mt-4 space-y-2">
              <div className="text-sm font-medium text-gray-900">
                Ready to load:
              </div>
              <div className="space-y-1">
                <div className="p-2 bg-blue-50 rounded text-sm">
                  <div className="font-medium">
                    Deck A: {job.tracks[0]?.title}
                  </div>
                  <div className="text-gray-600">
                    by {job.tracks[0]?.artist}
                  </div>
                </div>
                {job.tracks[1] && (
                  <div className="p-2 bg-green-50 rounded text-sm">
                    <div className="font-medium">
                      Deck B: {job.tracks[1]?.title}
                    </div>
                    <div className="text-gray-600">
                      by {job.tracks[1]?.artist}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
          <DialogFooter>
            <Button
              onClick={handleInitialLoad}
              className="w-full"
              disabled={!job.tracks || job.tracks.length === 0}
            >
              <Play className="h-4 w-4 mr-2" />
              Load Tracks & Start DJ Session
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Header */}
      <div className="bg-black/50 backdrop-blur-sm border-b border-gray-700 p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{job.playlist_name}</h1>
            <p className="text-gray-400">
              {job.tracks?.length || 0} tracks loaded
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-400">Mix Analysis</p>
            <p className="text-lg font-semibold">{job.status}</p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Audio Not Initialized Overlay */}
        {!isAudioInitialized && !showLoadDialog && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-40 flex items-center justify-center">
            <Card className="w-full max-w-md mx-4">
              <CardHeader>
                <CardTitle className="text-center flex items-center justify-center">
                  <Headphones className="h-6 w-6 mr-2" />
                  Audio Not Ready
                </CardTitle>
              </CardHeader>
              <CardContent className="text-center space-y-4">
                <p className="text-gray-600">
                  Please load tracks to initialize the audio system.
                </p>
                <Button
                  onClick={() => setShowLoadDialog(true)}
                  className="w-full"
                >
                  Load Tracks
                </Button>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Main Player Interface */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Top track player card */}
          <div className="col-span-3">
            <TrackTimelineCard />
          </div>
          {/* Deck A */}
          <DeckCard
            deck="A"
            track={deckA?.track || null}
            onLoad={(track) => handleLoadToDeck(track, "A")}
            job={job}
          />

          {/* Center Mixer */}
          <Card className="w-full">
            <CardHeader>
              <CardTitle className="text-center">Mixer</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Crossfader */}
              <Crossfader />

              {/* Master Volume
              <VolumeSlider
                volume={masterVolume}
                onVolumeChange={setMasterVolume}
                label="Master"
              /> */}
              <AutoplayButton />
              {/* Sync Controls */}
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-700">Sync</h3>
                <div className="grid grid-cols-2 gap-2">
                  <Button variant="outline" size="sm" className="w-full">
                    Beat Sync A→B
                  </Button>
                  <Button variant="outline" size="sm" className="w-full">
                    Beat Sync B→A
                  </Button>
                </div>
              </div>

              {/* Mix Progress */}
              {job.mix_instructions && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-gray-700">
                    Mix Progress
                  </h3>
                  <TrackProgress
                    mixInstructions={job.mix_instructions}
                    currentTime={0} // This would be connected to actual playback time
                    className="bg-gray-800 text-white"
                  />
                </div>
              )}
            </CardContent>
          </Card>

          {/* Deck B */}
          <DeckCard
            deck="B"
            track={deckB?.track || null}
            onLoad={(track) => handleLoadToDeck(track, "B")}
            job={job}
          />
        </div>

        {/* Queue and Mix Information */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Track Queue */}
          <Card>
            <CardHeader>
              <CardTitle>Track Queue</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {job.tracks?.map((track) => (
                  <div
                    key={track.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">
                        {track.title}
                      </p>
                      <p className="text-sm text-gray-600 truncate">
                        {track.artist}
                      </p>
                      <div className="flex items-center space-x-4 text-xs text-gray-500 mt-1">
                        <span>{formatTime(track.duration)}</span>
                        <span>{formatBPM(track.bpm)}</span>
                        <span>{track.key}</span>
                        <span>{Math.round(track.energy * 100)}% Energy</span>
                      </div>
                    </div>
                    <div className="flex space-x-1 ml-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleLoadToDeck(track, "A")}
                        disabled={!isAudioInitialized}
                      >
                        A
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleLoadToDeck(track, "B")}
                        disabled={!isAudioInitialized}
                      >
                        B
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Mix Information */}
          {job.mix_instructions && (
            <Card>
              <CardHeader>
                <CardTitle>Mix Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <div className="text-lg font-bold text-blue-600">
                      {job.mix_instructions.metadata.track_count}
                    </div>
                    <div className="text-sm text-gray-600">Tracks</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <div className="text-lg font-bold text-green-600">
                      {formatTime(job.mix_instructions.total_duration)}
                    </div>
                    <div className="text-sm text-gray-600">Duration</div>
                  </div>
                  <div className="text-center p-3 bg-purple-50 rounded-lg">
                    <div className="text-lg font-bold text-purple-600">
                      {Math.round(job.mix_instructions.metadata.avg_bpm)}
                    </div>
                    <div className="text-sm text-gray-600">Avg BPM</div>
                  </div>
                  <div className="text-center p-3 bg-yellow-50 rounded-lg">
                    <div className="text-lg font-bold text-yellow-600">
                      {Math.round(
                        job.mix_instructions.metadata.avg_compatibility * 100
                      )}
                      %
                    </div>
                    <div className="text-sm text-gray-600">Compatibility</div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-2">
                    Key Distribution
                  </h4>
                  <div className="flex flex-wrap gap-1">
                    {job.mix_instructions.metadata.keys_used.map((key) => (
                      <span
                        key={key}
                        className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
                      >
                        {key}
                      </span>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

const TrackTimelineCard = () => {
  const deckA = useAtomValue(deckAAtom);
  const deckB = useAtomValue(deckBAtom);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-bold text-gray-900">
          Playback
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-1 bg-gray-50 rounded-lg">
          <TrackTimeline
            track={deckA?.track || null}
            deck="A"
            isLoaded={deckA?.isLoaded || false}
          />
          <TrackTimeline
            track={deckB?.track || null}
            deck="B"
            isLoaded={deckB?.isLoaded || false}
          />
        </div>
      </CardContent>
    </Card>
  );
};

const TrackTimeline = ({
  track,
  deck,
  isLoaded
}: {
  track: Track | null;
  deck: "A" | "B";
  isLoaded: boolean;
}) => {
  return (
    <div className="bg-black rounded-lg p-4">
      <WaveformVisualizer
        deck={deck}
        trackTitle={track?.title || ""}
        loaded={isLoaded}
      />
    </div>
  );
};

const DeckCard = ({
  deck,
  track,
  onLoad,
  job
}: {
  deck: "A" | "B";
  track: Track | null;
  onLoad: (track: Track) => void;
  job: AnalysisJob;
}) => {
  const queue = useAtomValue(queueAtom);
  const scrubDeck = useSetAtom(scrubDeckAtom);

  return (
    <Card className="w-full">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold text-gray-900">
            Deck {deck}
          </CardTitle>
          <div className="flex items-center space-x-2">
            <Music className="h-4 w-4 text-gray-500" />
            <span className="text-sm text-gray-500">
              {track ? formatBPM(track.bpm) : "No Track"}
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Track Info */}
        <div className="bg-gray-50 rounded-lg p-4">
          {track ? (
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-900 truncate">
                {track.title}
              </h3>
              <p className="text-sm text-gray-600 truncate">{track.artist}</p>
              <div className="flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center space-x-1">
                  <Clock className="h-3 w-3" />
                  <span>{formatTime(track.duration)}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Zap className="h-3 w-3" />
                  <span>{Math.round(track.energy * 100)}% Energy</span>
                </div>
                <span className="font-mono">{track.key}</span>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400">
              <Music className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No track loaded</p>
            </div>
          )}
        </div>

        <PlaybackSlider track={track} deckName={deck} />

        {/* Transport Controls */}
        <div className="flex justify-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            disabled={!track}
            onClick={() =>
              scrubDeck({
                deck: deck === "A" ? "deckA" : "deckB",
                position: 0
              })
            }
          >
            <SkipBack className="h-4 w-4" />
          </Button>
          {deck === "A" ? <APlayButton /> : <BPlayButton />}
          <Button
            variant="outline"
            size="sm"
            disabled={!track}
            onClick={() => console.log("skip forward")}
          >
            <SkipForward className="h-4 w-4" />
          </Button>
        </div>

        {/* Volume Control */}
        <VolumeSlider deckName={deck} />

        {/* BPM Control */}
        <BPMSlider deckName={deck} />

        {/* Quick Load from Queue */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Quick Load</h4>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {queue.queue.slice(0, 5).map((queueTrack) => {
              // Find the original track with full info from job.tracks
              const fullTrack = job.tracks?.find((t) => t.id === queueTrack.id);
              if (!fullTrack) return null;

              return (
                <button
                  key={queueTrack.id}
                  onClick={() => onLoad(fullTrack)}
                  className="w-full text-left p-2 text-xs bg-gray-50 hover:bg-gray-100 rounded border transition-colors"
                >
                  <div className="truncate">{queueTrack.title}</div>
                  <div className="text-gray-500 truncate">
                    {queueTrack.artist}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

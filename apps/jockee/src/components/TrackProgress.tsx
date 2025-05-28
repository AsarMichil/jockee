import { MixInstructions } from '../lib/types';
import { formatDuration } from '../lib/utils';

interface TrackProgressProps {
  mixInstructions: MixInstructions;
  currentTime: number;
  className?: string;
}

export const TrackProgress: React.FC<TrackProgressProps> = ({
  mixInstructions,
  currentTime,
  className = ''
}) => {
  // Find current track and transition based on time
  let accumulatedTime = 0;
  let currentTransitionIndex = 0;
  let currentTrackProgress = 0;

  for (let i = 0; i < mixInstructions.transitions.length; i++) {
    const transition = mixInstructions.transitions[i];
    const trackDuration = transition.track_a.duration;
    
    if (accumulatedTime + trackDuration > currentTime) {
      currentTransitionIndex = i;
      currentTrackProgress = ((currentTime - accumulatedTime) / trackDuration) * 100;
      break;
    }
    
    accumulatedTime += trackDuration;
  }

  const currentTransition = mixInstructions.transitions[currentTransitionIndex];
  const isInTransition = currentTime >= (accumulatedTime + currentTransition.transition_start) &&
                        currentTime <= (accumulatedTime + currentTransition.transition_start + currentTransition.transition_duration);

  return (
    <div className={`bg-white rounded-lg p-4 ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-medium text-gray-900">Now Playing</h3>
        <span className="text-sm text-gray-500">
          Track {currentTransitionIndex + 1} of {mixInstructions.transitions.length}
        </span>
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center space-x-3">
          <div className="flex-1">
            <p className="font-medium text-gray-900 truncate">
              {currentTransition.track_a.title}
            </p>
            <p className="text-sm text-gray-500 truncate">
              {currentTransition.track_a.artist}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium text-gray-900">
              {Math.round(currentTransition.track_a.bpm)} BPM
            </p>
            <p className="text-xs text-gray-500">
              {currentTransition.track_a.key}
            </p>
          </div>
        </div>

        {/* Track Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${Math.max(0, Math.min(100, currentTrackProgress))}%` }}
          />
        </div>

        {/* Transition Indicator */}
        {isInTransition && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-2">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
              <span className="text-sm font-medium text-yellow-800">
                Transitioning to: {currentTransition.track_b.title}
              </span>
            </div>
            <p className="text-xs text-yellow-600 mt-1">
              Using {currentTransition.technique} • {currentTransition.transition_duration.toFixed(1)}s
            </p>
          </div>
        )}

        {/* Next Track Preview */}
        {!isInTransition && currentTransitionIndex < mixInstructions.transitions.length - 1 && (
          <div className="bg-gray-50 rounded-lg p-2">
            <p className="text-xs text-gray-500 mb-1">Next:</p>
            <p className="text-sm font-medium text-gray-700 truncate">
              {currentTransition.track_b.title}
            </p>
            <p className="text-xs text-gray-500 truncate">
              {currentTransition.track_b.artist}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}; 
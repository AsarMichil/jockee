import { useEffect } from 'react';

interface UseKeyboardShortcutsProps {
  onPlayPause: () => void;
  onSeek: (time: number) => void;
  currentTime: number;
  duration: number;
  isLoading?: boolean;
}

export const useKeyboardShortcuts = ({
  onPlayPause,
  onSeek,
  currentTime,
  duration,
  isLoading = false
}: UseKeyboardShortcutsProps) => {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't trigger shortcuts if user is typing in an input
      if (event.target instanceof HTMLInputElement || 
          event.target instanceof HTMLTextAreaElement ||
          isLoading) {
        return;
      }

      switch (event.code) {
        case 'Space':
          event.preventDefault();
          onPlayPause();
          break;
        
        case 'ArrowLeft':
          event.preventDefault();
          // Seek backward 10 seconds
          onSeek(Math.max(0, currentTime - 10));
          break;
        
        case 'ArrowRight':
          event.preventDefault();
          // Seek forward 10 seconds
          onSeek(Math.min(duration, currentTime + 10));
          break;
        
        case 'ArrowUp':
          event.preventDefault();
          // Seek forward 30 seconds
          onSeek(Math.min(duration, currentTime + 30));
          break;
        
        case 'ArrowDown':
          event.preventDefault();
          // Seek backward 30 seconds
          onSeek(Math.max(0, currentTime - 30));
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onPlayPause, onSeek, currentTime, duration, isLoading]);
}; 
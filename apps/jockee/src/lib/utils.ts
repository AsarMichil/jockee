import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

export function formatTime(date: string): string {
  return new Date(date).toLocaleTimeString()
}

export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString()
}

export function getEnergyColor(energy: number): string {
  if (energy < 0.3) return "text-blue-500"
  if (energy < 0.6) return "text-green-500"
  if (energy < 0.8) return "text-yellow-500"
  return "text-red-500"
}

export function getBpmColor(bpm: number): string {
  if (bpm < 100) return "text-blue-500"
  if (bpm < 120) return "text-green-500"
  if (bpm < 140) return "text-yellow-500"
  return "text-red-500"
}

export function getCompatibilityColor(score: number): string {
  if (score < 0.5) return "text-red-500"
  if (score < 0.7) return "text-yellow-500"
  return "text-green-500"
}
 
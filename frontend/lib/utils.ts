import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const SEVERITY_CONFIG: Record<string, { label: string; color: string; bg: string; border: string }> = {
  critical: { label: 'CRITICAL', color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' },
  high:     { label: 'HIGH',     color: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200' },
  medium:   { label: 'MEDIUM',   color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200' },
  low:      { label: 'LOW',      color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200' },
  info:     { label: 'INFO',     color: 'text-gray-600', bg: 'bg-gray-50', border: 'border-gray-200' },
  PASS:     { label: 'PASS',     color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' },
}

export const CATEGORY_CONFIG: Record<string, { label: string; icon: string }> = {
  security:        { label: 'Security',        icon: '🔒' },
  logic:           { label: 'Logic',           icon: '🧠' },
  performance:     { label: 'Performance',     icon: '⚡' },
  style:           { label: 'Style',           icon: '🎨' },
  maintainability: { label: 'Maintainability', icon: '🔧' },
  accessibility:   { label: 'Accessibility',   icon: '♿' },
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

export function severityOrder(s: string): number {
  return { critical: 0, high: 1, medium: 2, low: 3, info: 4 }[s] ?? 5
}

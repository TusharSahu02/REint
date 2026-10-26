import { useSyncExternalStore } from 'react'

export const TIMEZONES = [
  { id: 'Europe/London', label: 'Europe/London' },
  { id: 'Asia/Kolkata', label: 'India (IST)' },
  { id: 'UTC', label: 'UTC' },
]

const KEY = 'wfm.timezone'
const listeners = new Set<() => void>()

let current: string = localStorage.getItem(KEY) ?? 'Europe/London'
if (!TIMEZONES.some((t) => t.id === current)) current = 'Europe/London'

function subscribe(cb: () => void): () => void {
  listeners.add(cb)
  return () => {
    listeners.delete(cb)
  }
}

const getSnapshot = (): string => current

export function setTimezone(tz: string): void {
  current = tz
  localStorage.setItem(KEY, tz)
  listeners.forEach((l) => l())
}

export function useTimezone(): string {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot)
}

export function tzLabel(tz: string): string {
  return TIMEZONES.find((t) => t.id === tz)?.label ?? tz
}

export function fmtTime(iso: string, tz: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: tz,
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))
}

export function fmtDateTime(iso: string, tz: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: tz,
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))
}

export function fmtDay(iso: string, tz: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: tz,
    day: '2-digit',
    month: 'short',
  }).format(new Date(iso))
}

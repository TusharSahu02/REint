import type { AppConfig, DecisionForecastResponse } from './types'

const BASE: string = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    let detail: string = res.statusText
    try {
      detail = ((await res.json()) as { detail?: string }).detail ?? detail
    } catch {
      // body was not JSON; keep statusText
    }
    throw new Error(`API error ${res.status}: ${detail}`)
  }
  return (await res.json()) as T
}

export const fetchConfig = (): Promise<AppConfig> => getJson<AppConfig>('/api/config')

export const fetchDecision = (
  date: string,
  cutoff: string | null,
): Promise<DecisionForecastResponse> => {
  const params = new URLSearchParams({ date })
  if (cutoff) params.set('cutoff', cutoff)
  return getJson<DecisionForecastResponse>(`/api/decision-forecast?${params}`)
}

export const apiBase = BASE

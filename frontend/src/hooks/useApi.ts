import { useQuery } from '@tanstack/react-query'
import { fetchAccuracy, fetchConfig, fetchDecision } from '../api/client'
import type { Basis } from '../api/types'

export function useAppConfig() {
  return useQuery({ queryKey: ['config'], queryFn: fetchConfig, staleTime: Infinity })
}

export function useDecisionForecast(date: string, cutoff: string | null, enabled: boolean) {
  return useQuery({
    queryKey: ['decision', date, cutoff],
    queryFn: () => fetchDecision(date, cutoff),
    enabled,
  })
}

export function useAccuracy(
  start: string,
  end: string,
  basis: Basis,
  cutoff: string | null,
  enabled: boolean,
) {
  return useQuery({
    queryKey: ['accuracy', start, end, basis, cutoff],
    queryFn: () => fetchAccuracy(start, end, basis, cutoff),
    enabled,
  })
}

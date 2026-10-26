import { useQuery } from '@tanstack/react-query'
import { fetchConfig, fetchDecision } from '../api/client'

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

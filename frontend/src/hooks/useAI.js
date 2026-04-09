import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import client from '../api/client'

// AI Recommendations
export function useAIRecommendations(query, options = {}) {
  return useMutation({
    mutationFn: async (data) => {
      const response = await client.post('/api/ai/recommend', data)
      return response.data
    },
    ...options,
  })
}

// Evening Plan
export function useEveningPlan() {
  return useMutation({
    mutationFn: async (data) => {
      const response = await client.post('/api/ai/plan-evening', data)
      return response.data
    },
  })
}

// AI Sessions
export function useAISessions() {
  return useQuery({
    queryKey: ['ai', 'sessions'],
    queryFn: async () => {
      const response = await client.get('/api/ai/sessions')
      return response.data
    },
  })
}

// AI Chat History
export function useAIChatHistory(sessionId) {
  return useQuery({
    queryKey: ['ai', 'chat', sessionId],
    queryFn: async () => {
      const response = await client.get(`/api/ai/chat/${sessionId}`)
      return response.data
    },
    enabled: !!sessionId,
  })
}

// AI Feedback
export function useAIFeedback() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data) => {
      const response = await client.post('/api/ai/feedback', data)
      return response.data
    },
    onSuccess: () => {
      // Invalidate sessions and insights
      queryClient.invalidateQueries({ queryKey: ['ai', 'sessions'] })
      queryClient.invalidateQueries({ queryKey: ['ai', 'insights'] })
    },
  })
}

// AI Preferences
export function useAIPreferences() {
  return useQuery({
    queryKey: ['ai', 'preferences'],
    queryFn: async () => {
      const response = await client.get('/api/ai/preferences')
      return response.data
    },
  })
}

export function useUpdateAIPreferences() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data) => {
      const response = await client.put('/api/ai/preferences', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai', 'preferences'] })
    },
  })
}

// AI Onboarding
export function useAIOnboardingStatus() {
  return useQuery({
    queryKey: ['ai', 'onboarding'],
    queryFn: async () => {
      const response = await client.get('/api/ai/onboarding/status')
      return response.data
    },
  })
}

export function useCompleteAIOnboarding() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data) => {
      const response = await client.put('/api/ai/onboarding/complete', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai', 'onboarding'] })
      queryClient.invalidateQueries({ queryKey: ['ai', 'preferences'] })
    },
  })
}

// AI Insights
export function useAIInsights() {
  return useQuery({
    queryKey: ['ai', 'insights'],
    queryFn: async () => {
      const response = await client.get('/api/ai/insights')
      return response.data
    },
  })
}

// Assistant Summary
export function useAssistantSummary() {
  return useQuery({
    queryKey: ['assistant', 'summary'],
    queryFn: async () => {
      const response = await client.get('/api/assistant/summary')
      return response.data
    },
  })
}

// Daily Picks
export function useDailyPicks() {
  return useQuery({
    queryKey: ['assistant', 'daily-picks'],
    queryFn: async () => {
      const response = await client.get('/api/assistant/daily-picks')
      return response.data
    },
  })
}

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'

export const useSessionsStore = defineStore('sessions', () => {
  const sessions = ref([])
  const currentSession = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Use relative path when served from same origin (Docker), or absolute for dev
  const API_BASE = import.meta.env.VITE_API_BASE || ''
  const authStore = useAuthStore()

  async function fetchSessions() {
    loading.value = true
    error.value = null
    
    try {
      const response = await fetch(`${API_BASE}/api/sessions`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`,
        },
      })

      if (!response.ok) {
        if (response.status === 401) {
          authStore.logout()
          throw new Error('Authentication required')
        }
        throw new Error('Failed to fetch sessions')
      }

      const data = await response.json()
      sessions.value = data
      return { success: true }
    } catch (err) {
      error.value = err.message
      console.error('Error fetching sessions:', err)
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  async function fetchSession(sessionId) {
    loading.value = true
    error.value = null
    
    try {
      const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`,
        },
      })

      if (!response.ok) {
        if (response.status === 401) {
          authStore.logout()
          throw new Error('Authentication required')
        }
        if (response.status === 404) {
          throw new Error('Session not found')
        }
        throw new Error('Failed to fetch session')
      }

      const data = await response.json()
      currentSession.value = data
      return { success: true }
    } catch (err) {
      error.value = err.message
      console.error('Error fetching session:', err)
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  function clearCurrentSession() {
    currentSession.value = null
  }

  return {
    sessions,
    currentSession,
    loading,
    error,
    fetchSessions,
    fetchSession,
    clearCurrentSession,
  }
})


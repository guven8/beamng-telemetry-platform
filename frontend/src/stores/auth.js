import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('jwt_token') || null)
  const username = ref(null)

  // Use relative path when served from same origin (Docker), or absolute for dev
  const API_BASE = import.meta.env.VITE_API_BASE || ''

  async function login(usernameInput, password) {
    try {
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: usernameInput,
          password: password,
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Login failed')
      }

      const data = await response.json()
      token.value = data.access_token
      username.value = usernameInput
      localStorage.setItem('jwt_token', data.access_token)
      
      return { success: true }
    } catch (error) {
      console.error('Login error:', error)
      return { success: false, error: error.message }
    }
  }

  function logout() {
    token.value = null
    username.value = null
    localStorage.removeItem('jwt_token')
  }

  const isAuthenticated = () => {
    return token.value !== null
  }

  return {
    token,
    username,
    login,
    logout,
    isAuthenticated,
  }
})



import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTelemetryStore = defineStore('telemetry', () => {
  const currentSample = ref(null)
  const speedHistory = ref([])
  const maxHistoryLength = 100 // Keep last 100 samples for chart
  const websocket = ref(null)
  const isConnected = ref(false)

  const API_BASE = import.meta.env.VITE_WS_BASE || 'ws://localhost:8000'

  function connectWebSocket(token) {
    // Close existing connection if any
    if (websocket.value) {
      if (websocket.value.readyState === WebSocket.OPEN) {
        console.log('WebSocket already connected')
        return
      }
      websocket.value.close()
    }

    if (!token) {
      console.error('No token provided for WebSocket connection')
      return
    }

    const wsUrl = `${API_BASE}/ws/telemetry?token=${token}`
    console.log('Connecting to WebSocket:', wsUrl.replace(token, 'token=***'))
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket connected successfully')
      isConnected.value = true
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        currentSample.value = data

        // Add to speed history for chart
        if (data.speed !== null && data.speed !== undefined) {
          speedHistory.value.push({
            time: new Date(data.timestamp),
            speed: data.speed,
          })

          // Keep only last N samples
          if (speedHistory.value.length > maxHistoryLength) {
            speedHistory.value.shift()
          }
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      console.error('WebSocket readyState:', ws.readyState)
      isConnected.value = false
    }

    ws.onclose = (event) => {
      console.log('WebSocket disconnected', event.code, event.reason)
      isConnected.value = false
      // Optionally attempt to reconnect after a delay
      if (event.code !== 1000) { // Not a normal closure
        console.log('Unexpected closure, may attempt reconnect...')
      }
    }

    websocket.value = ws
  }

  function disconnectWebSocket() {
    if (websocket.value) {
      websocket.value.close()
      websocket.value = null
      isConnected.value = false
    }
  }

  function clearHistory() {
    speedHistory.value = []
  }

  return {
    currentSample,
    speedHistory,
    isConnected,
    connectWebSocket,
    disconnectWebSocket,
    clearHistory,
  }
})



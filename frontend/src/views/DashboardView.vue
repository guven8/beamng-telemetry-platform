<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <h1>BeamNG Telemetry Dashboard</h1>
      <div class="header-actions">
        <span class="connection-status" :class="{ connected: isConnected }">
          {{ isConnected ? '● Connected' : '○ Disconnected' }}
        </span>
        <button @click="handleLogout" class="logout-button">Logout</button>
      </div>
    </header>

    <div class="dashboard-content">
      <div class="telemetry-grid">
        <!-- Speed Card -->
        <div class="metric-card">
          <div class="metric-label">Speed</div>
          <div class="metric-value">
            {{ formatSpeed(currentSample?.speed) }}
          </div>
          <div class="metric-unit">km/h</div>
        </div>

        <!-- RPM Card -->
        <div class="metric-card">
          <div class="metric-label">RPM</div>
          <div class="metric-value">
            {{ formatRPM(currentSample?.rpm) }}
          </div>
          <div class="metric-unit">rpm</div>
        </div>

        <!-- Gear Card -->
        <div class="metric-card">
          <div class="metric-label">Gear</div>
          <div class="metric-value">
            {{ formatGear(currentSample?.gear) }}
          </div>
        </div>

        <!-- G-Force X Card -->
        <div class="metric-card">
          <div class="metric-label">G-Force X</div>
          <div class="metric-value">
            {{ formatGForce(currentSample?.g_force_x) }}
          </div>
        </div>

        <!-- G-Force Y Card -->
        <div class="metric-card">
          <div class="metric-label">G-Force Y</div>
          <div class="metric-value">
            {{ formatGForce(currentSample?.g_force_y) }}
          </div>
        </div>
      </div>

      <!-- Speed Chart -->
      <div class="chart-container">
        <h2>Speed Over Time</h2>
        <SpeedChart :data="speedHistory" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useTelemetryStore } from '../stores/telemetry'
import SpeedChart from '../components/SpeedChart.vue'

const router = useRouter()
const authStore = useAuthStore()
const telemetryStore = useTelemetryStore()

const currentSample = computed(() => telemetryStore.currentSample)
const speedHistory = computed(() => telemetryStore.speedHistory)
const isConnected = computed(() => telemetryStore.isConnected)

onMounted(() => {
  if (!authStore.isAuthenticated()) {
    router.push('/login')
    return
  }

  // Connect WebSocket with a small delay to ensure store is ready
  const token = authStore.token
  if (token) {
    console.log('Dashboard mounted, connecting WebSocket...')
    telemetryStore.connectWebSocket(token)
  } else {
    console.error('No token available for WebSocket connection')
  }
})

onUnmounted(() => {
  telemetryStore.disconnectWebSocket()
})

function handleLogout() {
  telemetryStore.disconnectWebSocket()
  authStore.logout()
  router.push('/login')
}

function formatSpeed(speed) {
  if (speed === null || speed === undefined) return '--'
  // Convert m/s to km/h
  return (speed * 3.6).toFixed(1)
}

function formatRPM(rpm) {
  if (rpm === null || rpm === undefined) return '--'
  return rpm.toLocaleString()
}

function formatGear(gear) {
  if (gear === null || gear === undefined) return '--'
  if (gear === -1) return 'R'
  if (gear === 0) return 'N'
  return gear.toString()
}

function formatGForce(gForce) {
  if (gForce === null || gForce === undefined) return '--'
  return gForce.toFixed(2)
}
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: #f5f5f5;
}

.dashboard-header {
  background: white;
  padding: 20px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.dashboard-header h1 {
  font-size: 24px;
  color: #333;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}

.connection-status {
  font-size: 14px;
  color: #999;
}

.connection-status.connected {
  color: #4caf50;
}

.logout-button {
  padding: 8px 16px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.logout-button:hover {
  background: #d32f2f;
}

.dashboard-content {
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
}

.telemetry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.metric-card {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.metric-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-value {
  font-size: 36px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.metric-unit {
  font-size: 12px;
  color: #999;
}

.chart-container {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chart-container h2 {
  font-size: 18px;
  margin-bottom: 20px;
  color: #333;
}
</style>



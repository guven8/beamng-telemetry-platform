<template>
  <div class="session-detail-page">
    <header class="page-header">
      <div class="header-left">
        <button @click="goBack" class="back-button">← Back</button>
        <h1>Session {{ sessionId }}</h1>
      </div>
      <div class="header-actions">
        <button @click="handleLogout" class="logout-button">Logout</button>
      </div>
    </header>

    <div class="page-content">
      <div v-if="loading" class="loading">Loading session...</div>
      <div v-else-if="error" class="error-message">{{ error }}</div>
      <div v-else-if="session" class="session-detail">
        <!-- Summary Stats -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">Duration</div>
            <div class="stat-value">{{ formatDuration(session.duration_seconds) }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Top Speed</div>
            <div class="stat-value">{{ formatSpeed(session.top_speed) }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Average Speed</div>
            <div class="stat-value">{{ formatSpeed(session.avg_speed) }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Max RPM</div>
            <div class="stat-value">{{ formatRPM(session.max_rpm) }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Frames</div>
            <div class="stat-value">{{ session.frame_count || 0 }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Start Time</div>
            <div class="stat-value-small">{{ formatDateTime(session.start_time) }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">End Time</div>
            <div class="stat-value-small">{{ formatDateTime(session.end_time) }}</div>
          </div>
        </div>

        <!-- Speed Chart -->
        <div class="chart-container">
          <h2>Speed Over Time</h2>
          <SessionSpeedChart :frames="session.frames || []" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useSessionsStore } from '../stores/sessions'
import SessionSpeedChart from '../components/SessionSpeedChart.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const sessionsStore = useSessionsStore()

const sessionId = computed(() => parseInt(route.params.id))
const session = computed(() => sessionsStore.currentSession)
const loading = computed(() => sessionsStore.loading)
const error = computed(() => sessionsStore.error)

onMounted(async () => {
  if (!authStore.isAuthenticated()) {
    router.push('/login')
    return
  }
  await sessionsStore.fetchSession(sessionId.value)
})

function goBack() {
  router.push('/sessions')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function formatDateTime(dateTime) {
  if (!dateTime) return '--'
  return new Date(dateTime).toLocaleString()
}

function formatDuration(seconds) {
  if (seconds === null || seconds === undefined) return '--'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}m ${secs}s`
}

function formatSpeed(speed) {
  if (speed === null || speed === undefined) return '--'
  // Convert m/s to km/h
  return (speed * 3.6).toFixed(1) + ' km/h'
}

function formatRPM(rpm) {
  if (rpm === null || rpm === undefined) return '--'
  return rpm.toLocaleString()
}
</script>

<style scoped>
.session-detail-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.page-header {
  background: white;
  padding: 20px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.back-button {
  padding: 8px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.back-button:hover {
  background: #5568d3;
}

.page-header h1 {
  font-size: 24px;
  color: #333;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 20px;
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

.page-content {
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
}

.loading,
.error-message {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error-message {
  color: #d32f2f;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #333;
}

.stat-value-small {
  font-size: 14px;
  font-weight: 500;
  color: #333;
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


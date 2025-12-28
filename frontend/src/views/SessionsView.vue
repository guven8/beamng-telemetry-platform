<template>
  <div class="sessions-page">
    <header class="page-header">
      <div class="header-left">
        <router-link to="/dashboard" class="back-button">← Dashboard</router-link>
        <h1>Sessions</h1>
      </div>
      <div class="header-actions">
        <button @click="handleLogout" class="logout-button">Logout</button>
      </div>
    </header>

    <div class="page-content">
      <div v-if="loading" class="loading">Loading sessions...</div>
      <div v-else-if="error" class="error-message">{{ error }}</div>
      <div v-else-if="sessions.length === 0" class="empty-state">
        No sessions found. Start driving in BeamNG.drive to create sessions.
      </div>
      <table v-else class="sessions-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Start Time</th>
            <th>Duration</th>
            <th>Top Speed</th>
            <th>Avg Speed</th>
            <th>Max RPM</th>
            <th>Frames</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="session in sessions"
            :key="session.id"
            @click="navigateToSession(session.id)"
            class="session-row"
          >
            <td>{{ session.id }}</td>
            <td>{{ formatDateTime(session.start_time) }}</td>
            <td>{{ formatDuration(session.duration_seconds) }}</td>
            <td>{{ formatSpeed(session.top_speed) }}</td>
            <td>{{ formatSpeed(session.avg_speed) }}</td>
            <td>{{ formatRPM(session.max_rpm) }}</td>
            <td>{{ session.frame_count || 0 }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useSessionsStore } from '../stores/sessions'

const router = useRouter()
const authStore = useAuthStore()
const sessionsStore = useSessionsStore()

// Use computed to ensure reactivity
const sessions = computed(() => sessionsStore.sessions)
const loading = computed(() => sessionsStore.loading)
const error = computed(() => sessionsStore.error)

onMounted(async () => {
  if (!authStore.isAuthenticated()) {
    router.push('/login')
    return
  }
  // Always fetch sessions on mount, even if store has data
  await sessionsStore.fetchSessions()
})

function navigateToSession(sessionId) {
  router.push(`/sessions/${sessionId}`)
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
.sessions-page {
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
  text-decoration: none;
  border-radius: 4px;
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
.error-message,
.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error-message {
  color: #d32f2f;
}

.sessions-table {
  width: 100%;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.sessions-table thead {
  background: #f5f5f5;
}

.sessions-table th {
  padding: 16px;
  text-align: left;
  font-weight: 600;
  font-size: 14px;
  color: #333;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sessions-table td {
  padding: 16px;
  border-top: 1px solid #eee;
  font-size: 14px;
  color: #666;
}

.session-row {
  cursor: pointer;
  transition: background 0.2s;
}

.session-row:hover {
  background: #f9f9f9;
}
</style>


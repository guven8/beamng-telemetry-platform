<template>
  <div class="login-container">
    <div class="login-card">
      <h1>BeamNG Telemetry Platform</h1>
      <p class="subtitle">Login to access the dashboard</p>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            required
            placeholder="local"
            autocomplete="username"
          />
        </div>
        
        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            placeholder="local"
            autocomplete="current-password"
          />
        </div>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <button type="submit" :disabled="loading" class="login-button">
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('local')
const password = ref('local')
const loading = ref(false)
const error = ref(null)

async function handleLogin() {
  error.value = null
  loading.value = true

  const result = await authStore.login(username.value, password.value)

  if (result.success) {
    router.push('/dashboard')
  } else {
    error.value = result.error || 'Login failed. Please check your credentials.'
  }

  loading.value = false
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  background: white;
  border-radius: 8px;
  padding: 40px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

h1 {
  font-size: 24px;
  margin-bottom: 8px;
  color: #333;
  text-align: center;
}

.subtitle {
  color: #666;
  text-align: center;
  margin-bottom: 32px;
  font-size: 14px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

input {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
}

input:focus {
  outline: none;
  border-color: #667eea;
}

.login-button {
  padding: 12px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.login-button:hover:not(:disabled) {
  background: #5568d3;
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  padding: 12px;
  background: #fee;
  color: #c33;
  border-radius: 4px;
  font-size: 14px;
  text-align: center;
}
</style>



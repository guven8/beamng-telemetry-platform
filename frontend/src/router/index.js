import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import SessionsView from '../views/SessionsView.vue'
import SessionDetailView from '../views/SessionDetailView.vue'

const routes = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView,
    meta: { requiresAuth: true },
  },
  {
    path: '/sessions',
    name: 'sessions',
    component: SessionsView,
    meta: { requiresAuth: true },
  },
  {
    path: '/sessions/:id',
    name: 'session-detail',
    component: SessionDetailView,
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard to protect authenticated routes
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated()) {
    next({ name: 'login' })
  } else {
    next()
  }
})

export default router



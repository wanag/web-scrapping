import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref(localStorage.getItem('auth_token') || null)
  const expiresAt = ref(localStorage.getItem('auth_expires') || null)

  // Getters
  const isAuthenticated = computed(() => {
    if (!token.value) return false

    // Check if token is expired
    if (expiresAt.value && new Date() > new Date(expiresAt.value)) {
      logout()
      return false
    }

    return true
  })

  // Actions
  function setToken(newToken, expiresIn) {
    token.value = newToken

    // Calculate expiration time
    const expires = new Date()
    expires.setSeconds(expires.getSeconds() + expiresIn)
    expiresAt.value = expires.toISOString()

    // Save to localStorage
    localStorage.setItem('auth_token', newToken)
    localStorage.setItem('auth_expires', expiresAt.value)
  }

  function logout() {
    token.value = null
    expiresAt.value = null

    // Clear localStorage
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_expires')

    // Redirect to login
    router.push({ name: 'login' })
  }

  function clearAuth() {
    token.value = null
    expiresAt.value = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_expires')
  }

  return {
    token,
    expiresAt,
    isAuthenticated,
    setToken,
    logout,
    clearAuth
  }
})

<template>
  <v-app>
    <router-view />
  </v-app>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  // Check authentication on app load
  if (!authStore.isAuthenticated) {
    authStore.clearAuth()
  }
})
</script>

<style>
/* Global styles */
* {
  box-sizing: border-box;
}

#app {
  font-family: 'Roboto', sans-serif;
}
</style>

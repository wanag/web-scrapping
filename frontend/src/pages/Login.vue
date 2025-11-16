<template>
  <v-container fluid class="fill-height login-container">
    <!-- Theme toggle button (floating) -->
    <v-btn
      :icon="isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'"
      @click="toggleTheme"
      class="theme-toggle-btn"
      color="white"
      variant="text"
    ></v-btn>

    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <v-card-title class="text-h4 text-center py-6 bg-primary">
            <v-icon icon="mdi-book-open-page-variant" size="48" class="mr-2"></v-icon>
            <span class="text-white">Book Reader</span>
          </v-card-title>

          <v-card-text class="pa-8">
            <div class="text-center mb-6">
              <h2 class="text-h5 mb-2">Welcome Back</h2>
              <p class="text-grey">Enter your 4-digit PIN to continue</p>
            </div>

            <v-form @submit.prevent="handleLogin">
              <div class="pin-input-container mb-6">
                <v-text-field
                  v-for="(digit, index) in pinDigits"
                  :key="index"
                  :ref="el => pinInputs[index] = el"
                  v-model="pinDigits[index]"
                  class="pin-digit"
                  variant="outlined"
                  density="comfortable"
                  type="tel"
                  maxlength="1"
                  hide-details
                  :error="error !== null"
                  @input="onPinInput(index)"
                  @keydown="onPinKeydown(index, $event)"
                  autocomplete="off"
                />
              </div>

              <v-alert
                v-if="error"
                type="error"
                variant="tonal"
                class="mb-4"
                closable
                @click:close="error = null"
              >
                {{ error }}
              </v-alert>

              <v-btn
                type="submit"
                color="primary"
                size="large"
                block
                :loading="loading"
                :disabled="pin.length !== 4"
              >
                Login
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTheme } from '@/composables/useTheme'
import api from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()
const { isDark, toggleTheme } = useTheme()

const pinDigits = ref(['', '', '', ''])
const pinInputs = ref([])
const loading = ref(false)
const error = ref(null)

const pin = computed(() => pinDigits.value.join(''))

onMounted(() => {
  // Focus first input
  if (pinInputs.value[0]) {
    pinInputs.value[0].$el.querySelector('input').focus()
  }
})

function onPinInput(index) {
  // Remove non-numeric characters
  pinDigits.value[index] = pinDigits.value[index].replace(/[^0-9]/g, '')

  // Move to next input if digit entered
  if (pinDigits.value[index] && index < 3) {
    const nextInput = pinInputs.value[index + 1]
    if (nextInput) {
      nextInput.$el.querySelector('input').focus()
    }
  }

  // Auto-submit when all 4 digits entered
  if (index === 3 && pinDigits.value.every(d => d !== '')) {
    handleLogin()
  }
}

function onPinKeydown(index, event) {
  // Handle backspace
  if (event.key === 'Backspace' && !pinDigits.value[index] && index > 0) {
    const prevInput = pinInputs.value[index - 1]
    if (prevInput) {
      prevInput.$el.querySelector('input').focus()
      pinDigits.value[index - 1] = ''
    }
  }

  // Handle arrow keys
  if (event.key === 'ArrowLeft' && index > 0) {
    pinInputs.value[index - 1].$el.querySelector('input').focus()
  }
  if (event.key === 'ArrowRight' && index < 3) {
    pinInputs.value[index + 1].$el.querySelector('input').focus()
  }
}

async function handleLogin() {
  if (pin.value.length !== 4) return

  loading.value = true
  error.value = null

  try {
    const response = await api.auth.login(pin.value)

    if (response.data.success) {
      authStore.setToken(response.data.token, response.data.expires_in)
      router.push({ name: 'welcome' })
    } else {
      error.value = 'Invalid PIN'
      resetPin()
    }
  } catch (err) {
    if (err.response && err.response.status === 401) {
      error.value = 'Invalid PIN. Please try again.'
    } else {
      error.value = 'Connection error. Please check if the server is running.'
    }
    resetPin()
  } finally {
    loading.value = false
  }
}

function resetPin() {
  pinDigits.value = ['', '', '', '']
  if (pinInputs.value[0]) {
    pinInputs.value[0].$el.querySelector('input').focus()
  }
}
</script>

<style scoped>
.login-container {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  position: relative;
}

.theme-toggle-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 10;
}

.pin-input-container {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.pin-digit {
  width: 64px;
}

.pin-digit :deep(input) {
  text-align: center;
  font-size: 24px;
  font-weight: bold;
}
</style>

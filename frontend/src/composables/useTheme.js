import { ref, watch } from 'vue'
import { useTheme as useVuetifyTheme } from 'vuetify'

const isDark = ref(localStorage.getItem('theme') === 'dark')

export function useTheme() {
  const vuetifyTheme = useVuetifyTheme()

  // Apply saved theme on load
  if (isDark.value) {
    vuetifyTheme.global.name.value = 'dark'
  }

  // Watch for changes and persist
  watch(isDark, (newValue) => {
    vuetifyTheme.global.name.value = newValue ? 'dark' : 'light'
    localStorage.setItem('theme', newValue ? 'dark' : 'light')
  })

  function toggleTheme() {
    isDark.value = !isDark.value
  }

  return {
    isDark,
    toggleTheme
  }
}

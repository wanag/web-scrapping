<template>
  <v-app>
    <v-app-bar color="primary" density="compact">
      <v-app-bar-nav-icon @click="goBack"></v-app-bar-nav-icon>
      <v-app-bar-title>{{ book?.metadata.title || 'Reader' }}</v-app-bar-title>

      <template v-slot:append>
        <v-btn
          :icon="isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'"
          @click="toggleTheme"
        ></v-btn>
        <v-btn icon @click="settingsDialog = true">
          <v-icon>mdi-cog</v-icon>
        </v-btn>
      </template>
    </v-app-bar>

    <v-main>
      <!-- Loading -->
      <v-container v-if="loading" class="text-center py-12">
        <v-progress-circular
          indeterminate
          color="primary"
          size="64"
        ></v-progress-circular>
        <p class="mt-4 text-grey">Loading book...</p>
      </v-container>

      <!-- Error -->
      <v-container v-else-if="error" class="text-center py-12">
        <v-icon icon="mdi-alert-circle-outline" size="64" color="error"></v-icon>
        <h2 class="text-h5 mt-4">{{ error }}</h2>
        <v-btn color="primary" class="mt-4" @click="goBack">Go Back</v-btn>
      </v-container>

      <!-- Reader -->
      <div v-else-if="chapter" class="reader-container">
        <!-- Chapter navigation header -->
        <v-container class="chapter-nav-top">
          <v-row align="center">
            <v-col>
              <h2 class="text-h6">{{ chapter.title }}</h2>
              <p class="text-caption text-grey">
                Chapter {{ currentChapterId + 1 }} of {{ book?.chapters.length }}
              </p>
            </v-col>
            <v-col cols="auto">
              <v-btn-group variant="outlined">
                <v-btn
                  :disabled="chapter.previous_chapter === null"
                  @click="goToChapter(chapter.previous_chapter)"
                  icon="mdi-chevron-left"
                ></v-btn>
                <v-btn
                  :disabled="chapter.next_chapter === null"
                  @click="goToChapter(chapter.next_chapter)"
                  icon="mdi-chevron-right"
                ></v-btn>
              </v-btn-group>
            </v-col>
          </v-row>
        </v-container>

        <!-- Chapter content -->
        <v-container class="chapter-content" :class="`theme-${theme}`" :style="contentStyle">
          <div v-html="formattedContent"></div>
        </v-container>

        <!-- Chapter navigation footer -->
        <v-container class="chapter-nav-bottom py-8">
          <v-row>
            <v-col>
              <v-btn
                v-if="chapter.previous_chapter !== null"
                variant="tonal"
                @click="goToChapter(chapter.previous_chapter)"
              >
                <v-icon icon="mdi-chevron-left" class="mr-2"></v-icon>
                Previous Chapter
              </v-btn>
            </v-col>
            <v-col class="text-right">
              <v-btn
                v-if="chapter.next_chapter !== null"
                color="primary"
                @click="goToChapter(chapter.next_chapter)"
              >
                Next Chapter
                <v-icon icon="mdi-chevron-right" class="ml-2"></v-icon>
              </v-btn>
            </v-col>
          </v-row>
        </v-container>
      </div>
    </v-main>

    <!-- Settings dialog -->
    <v-dialog v-model="settingsDialog" max-width="500">
      <v-card>
        <v-card-title>Reading Settings</v-card-title>
        <v-card-text>
          <div class="mb-4">
            <label class="text-subtitle-2 mb-2 d-block">Font Size</label>
            <v-slider
              v-model="fontSize"
              min="12"
              max="24"
              step="1"
              thumb-label
              :label="`${fontSize}px`"
            ></v-slider>
          </div>

          <div class="mb-4">
            <label class="text-subtitle-2 mb-2 d-block">Line Height</label>
            <v-slider
              v-model="lineHeight"
              min="1.2"
              max="2.4"
              step="0.1"
              thumb-label
            ></v-slider>
          </div>

          <div class="mb-4">
            <label class="text-subtitle-2 mb-2 d-block">Max Width</label>
            <v-slider
              v-model="maxWidth"
              min="600"
              max="1200"
              step="50"
              thumb-label
              :label="`${maxWidth}px`"
            ></v-slider>
          </div>

          <div>
            <label class="text-subtitle-2 mb-2 d-block">Theme</label>
            <v-btn-toggle v-model="theme" mandatory>
              <v-btn value="light">Light</v-btn>
              <v-btn value="dark">Dark</v-btn>
              <v-btn value="sepia">Sepia</v-btn>
            </v-btn-toggle>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="resetSettings">Reset</v-btn>
          <v-btn color="primary" @click="settingsDialog = false">Done</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Resume notification -->
    <v-snackbar
      v-model="resumeSnackbar"
      :timeout="3000"
      color="info"
      location="top"
    >
      <v-icon icon="mdi-bookmark-check" class="mr-2"></v-icon>
      {{ resumeMessage }}
    </v-snackbar>
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useBooksStore } from '@/stores/books'
import { useTheme } from '@/composables/useTheme'
import { useReadingProgress } from '@/composables/useReadingProgress'
import api from '@/services/api'

const router = useRouter()
const route = useRoute()
const booksStore = useBooksStore()
const { isDark, toggleTheme } = useTheme()
const { getProgress, saveProgress } = useReadingProgress()

const bookId = computed(() => route.params.bookId)
const book = ref(null)
const chapter = ref(null)
const currentChapterId = ref(0)
const loading = ref(false)
const error = ref(null)

// Reading settings
const settingsDialog = ref(false)
const fontSize = ref(16)
const lineHeight = ref(1.6)
const maxWidth = ref(800)
const theme = ref('light')

// Progress notification
const resumeSnackbar = ref(false)
const resumeMessage = ref('')

onMounted(async () => {
  loadSettings()
  await loadBook()
})

// Sync reader theme with global theme
watch(isDark, (newValue) => {
  // Only auto-sync if user hasn't manually set sepia theme
  if (theme.value !== 'sepia') {
    theme.value = newValue ? 'dark' : 'light'
  }
})

async function loadBook() {
  loading.value = true
  error.value = null

  try {
    // Load book metadata
    const bookResponse = await api.books.get(bookId.value)
    book.value = bookResponse.data

    // Check for saved reading progress
    const savedProgress = getProgress(bookId.value)
    let chapterToLoad = 0

    if (savedProgress && savedProgress.chapterId !== null) {
      // Validate saved chapter exists
      if (savedProgress.chapterId < book.value.chapters.length) {
        chapterToLoad = savedProgress.chapterId

        // Show notification that we're resuming
        resumeMessage.value = `Resuming from Chapter ${chapterToLoad + 1}`
        resumeSnackbar.value = true
      }
    }

    // Load the appropriate chapter
    await loadChapter(chapterToLoad)
  } catch (err) {
    console.error('Failed to load book:', err)
    error.value = 'Failed to load book'
  } finally {
    loading.value = false
  }
}

async function loadChapter(chapterId) {
  try {
    const response = await api.books.getChapter(bookId.value, chapterId)
    chapter.value = response.data
    currentChapterId.value = chapterId

    // Save reading progress
    saveProgress(bookId.value, chapterId)

    // Scroll to top
    window.scrollTo(0, 0)
  } catch (err) {
    console.error('Failed to load chapter:', err)
    error.value = 'Failed to load chapter'
  }
}

function goToChapter(chapterId) {
  if (chapterId !== null) {
    loadChapter(chapterId)
  }
}

function goBack() {
  router.push({ name: 'welcome' })
}

const formattedContent = computed(() => {
  if (!chapter.value) return ''

  // Convert markdown to HTML
  return markdownToHtml(chapter.value.content)
})

function markdownToHtml(markdown) {
  let html = markdown

  // Code blocks (must be before inline code)
  html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')

  // Headings
  html = html.replace(/^######\s+(.+)$/gm, '<h6>$1</h6>')
  html = html.replace(/^#####\s+(.+)$/gm, '<h5>$1</h5>')
  html = html.replace(/^####\s+(.+)$/gm, '<h4>$1</h4>')
  html = html.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^##\s+(.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^#\s+(.+)$/gm, '<h1>$1</h1>')

  // Horizontal rules
  html = html.replace(/^---+$/gm, '<hr>')

  // Blockquotes
  html = html.replace(/^>\s+(.+)$/gm, '<blockquote>$1</blockquote>')

  // Lists - unordered
  html = html.replace(/^-\s+(.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')

  // Lists - ordered
  html = html.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')

  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')

  // Italic
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')

  // Paragraphs - split by double newlines and wrap in <p> tags
  const lines = html.split('\n')
  let result = []
  let paragraph = []

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()

    // Check if line is already wrapped in a block element
    const isBlockElement = /^<(h[1-6]|hr|ul|ol|blockquote|pre|div)/.test(line)
    const closesBlockElement = /<\/(ul|ol|blockquote|pre)>$/.test(line)

    if (line === '') {
      // Empty line - end current paragraph
      if (paragraph.length > 0) {
        const paraText = paragraph.join(' ')
        if (!isBlockElement) {
          result.push('<p>' + paraText + '</p>')
        } else {
          result.push(paraText)
        }
        paragraph = []
      }
    } else if (isBlockElement || closesBlockElement) {
      // Block element - add directly
      if (paragraph.length > 0) {
        result.push('<p>' + paragraph.join(' ') + '</p>')
        paragraph = []
      }
      result.push(line)
    } else {
      // Regular text - add to current paragraph
      paragraph.push(line)
    }
  }

  // Add remaining paragraph
  if (paragraph.length > 0) {
    const paraText = paragraph.join(' ')
    if (!/^<(h[1-6]|hr|ul|ol|blockquote|pre)/.test(paraText)) {
      result.push('<p>' + paraText + '</p>')
    } else {
      result.push(paraText)
    }
  }

  return result.join('\n')
}

const contentStyle = computed(() => {
  const themes = {
    light: {
      background: '#ffffff',
      color: '#000000'
    },
    dark: {
      background: '#1e1e1e',
      color: '#e0e0e0'
    },
    sepia: {
      background: '#f4ecd8',
      color: '#5c4f3d'
    }
  }

  const selectedTheme = themes[theme.value] || themes.light

  return {
    fontSize: `${fontSize.value}px`,
    lineHeight: lineHeight.value,
    maxWidth: `${maxWidth.value}px`,
    backgroundColor: selectedTheme.background,
    color: selectedTheme.color
  }
})

function loadSettings() {
  const saved = localStorage.getItem('reader_settings')
  if (saved) {
    try {
      const settings = JSON.parse(saved)
      fontSize.value = settings.fontSize || 16
      lineHeight.value = settings.lineHeight || 1.6
      maxWidth.value = settings.maxWidth || 800
      // Sync theme with global theme unless user set sepia
      if (settings.theme === 'sepia') {
        theme.value = 'sepia'
      } else {
        theme.value = isDark.value ? 'dark' : 'light'
      }
    } catch (e) {
      console.error('Failed to load settings:', e)
    }
  } else {
    // No saved settings, use global theme
    theme.value = isDark.value ? 'dark' : 'light'
  }
}

function saveSettings() {
  const settings = {
    fontSize: fontSize.value,
    lineHeight: lineHeight.value,
    maxWidth: maxWidth.value,
    theme: theme.value
  }
  localStorage.setItem('reader_settings', JSON.stringify(settings))
}

function resetSettings() {
  fontSize.value = 16
  lineHeight.value = 1.6
  maxWidth.value = 800
  theme.value = 'light'
  saveSettings()
}

// Watch for setting changes and save
watch([fontSize, lineHeight, maxWidth, theme], () => {
  saveSettings()
})
</script>

<style scoped>
.reader-container {
  min-height: calc(100vh - 56px);
}

.chapter-content {
  margin: 0 auto;
  padding: 2rem;
  min-height: 60vh;
  transition: all 0.3s ease;
}

/* Paragraphs */
.chapter-content :deep(p) {
  margin-bottom: 1em;
  text-align: justify;
  line-height: inherit;
}

/* Headings */
.chapter-content :deep(h1) {
  font-size: 2em;
  font-weight: 700;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  line-height: 1.2;
}

.chapter-content :deep(h2) {
  font-size: 1.75em;
  font-weight: 600;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  line-height: 1.3;
}

.chapter-content :deep(h3) {
  font-size: 1.5em;
  font-weight: 600;
  margin-top: 1.3em;
  margin-bottom: 0.5em;
  line-height: 1.4;
}

.chapter-content :deep(h4) {
  font-size: 1.25em;
  font-weight: 600;
  margin-top: 1.2em;
  margin-bottom: 0.5em;
}

.chapter-content :deep(h5) {
  font-size: 1.1em;
  font-weight: 600;
  margin-top: 1.1em;
  margin-bottom: 0.5em;
}

.chapter-content :deep(h6) {
  font-size: 1em;
  font-weight: 600;
  margin-top: 1em;
  margin-bottom: 0.5em;
}

/* Lists */
.chapter-content :deep(ul),
.chapter-content :deep(ol) {
  margin: 1em 0;
  padding-left: 2em;
}

.chapter-content :deep(li) {
  margin-bottom: 0.5em;
  line-height: 1.6;
}

.chapter-content :deep(ul) {
  list-style-type: disc;
}

.chapter-content :deep(ol) {
  list-style-type: decimal;
}

/* Code */
.chapter-content :deep(code) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9em;
}

.chapter-content :deep(pre) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 1em;
  border-radius: 5px;
  overflow-x: auto;
  margin: 1em 0;
}

.chapter-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
  font-size: 0.9em;
  line-height: 1.5;
}

/* Blockquotes */
.chapter-content :deep(blockquote) {
  border-left: 4px solid #1976D2;
  padding-left: 1em;
  margin: 1em 0;
  font-style: italic;
  color: rgba(0, 0, 0, 0.7);
}

/* Links */
.chapter-content :deep(a) {
  color: #1976D2;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-bottom 0.2s;
}

.chapter-content :deep(a:hover) {
  border-bottom: 1px solid #1976D2;
}

/* Horizontal rules */
.chapter-content :deep(hr) {
  border: none;
  border-top: 2px solid rgba(0, 0, 0, 0.1);
  margin: 2em 0;
}

/* Tables */
.chapter-content :deep(table) {
  border-collapse: collapse;
  margin: 1em 0;
  width: 100%;
}

.chapter-content :deep(td),
.chapter-content :deep(th) {
  border: 1px solid rgba(0, 0, 0, 0.1);
  padding: 0.5em;
}

.chapter-content :deep(th) {
  background-color: rgba(0, 0, 0, 0.05);
  font-weight: 600;
}

/* Dark theme overrides */
.chapter-content.theme-dark :deep(code) {
  background-color: rgba(255, 255, 255, 0.1);
  color: #e0e0e0;
}

.chapter-content.theme-dark :deep(pre) {
  background-color: rgba(255, 255, 255, 0.05);
}

.chapter-content.theme-dark :deep(blockquote) {
  border-left-color: #2196F3;
  color: rgba(255, 255, 255, 0.7);
}

.chapter-content.theme-dark :deep(a) {
  color: #64B5F6;
}

.chapter-content.theme-dark :deep(a:hover) {
  border-bottom-color: #64B5F6;
}

.chapter-content.theme-dark :deep(hr) {
  border-top-color: rgba(255, 255, 255, 0.12);
}

.chapter-content.theme-dark :deep(td),
.chapter-content.theme-dark :deep(th) {
  border-color: rgba(255, 255, 255, 0.12);
}

.chapter-content.theme-dark :deep(th) {
  background-color: rgba(255, 255, 255, 0.05);
}

/* Sepia theme overrides */
.chapter-content.theme-sepia :deep(code) {
  background-color: rgba(92, 79, 61, 0.1);
  color: #5c4f3d;
}

.chapter-content.theme-sepia :deep(pre) {
  background-color: rgba(92, 79, 61, 0.05);
}

.chapter-content.theme-sepia :deep(blockquote) {
  border-left-color: #8B7355;
  color: rgba(92, 79, 61, 0.8);
}

.chapter-content.theme-sepia :deep(a) {
  color: #8B7355;
}

.chapter-content.theme-sepia :deep(a:hover) {
  border-bottom-color: #8B7355;
}

.chapter-content.theme-sepia :deep(hr) {
  border-top-color: rgba(92, 79, 61, 0.2);
}

.chapter-content.theme-sepia :deep(td),
.chapter-content.theme-sepia :deep(th) {
  border-color: rgba(92, 79, 61, 0.2);
}

.chapter-content.theme-sepia :deep(th) {
  background-color: rgba(92, 79, 61, 0.08);
}

/* Strong and emphasis */
.chapter-content :deep(strong) {
  font-weight: 600;
}

.chapter-content :deep(em) {
  font-style: italic;
}

/* Navigation */
.chapter-nav-top,
.chapter-nav-bottom {
  max-width: 900px;
  margin: 0 auto;
}

.chapter-nav-top {
  padding-top: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.chapter-nav-bottom {
  border-top: 1px solid rgba(0, 0, 0, 0.12);
}

/* Dark mode navigation borders - these need to be on .reader-container to work with v-main */
.v-theme--dark .chapter-nav-top {
  border-bottom-color: rgba(255, 255, 255, 0.12);
}

.v-theme--dark .chapter-nav-bottom {
  border-top-color: rgba(255, 255, 255, 0.12);
}
</style>

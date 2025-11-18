<template>
  <v-app>
    <v-app-bar color="primary" prominent>
      <v-app-bar-title>
        <v-icon icon="mdi-book-open-page-variant" class="mr-2"></v-icon>
        Book Scraper & Reader
      </v-app-bar-title>

      <template v-slot:append>
        <v-btn
          :icon="isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'"
          @click="toggleTheme"
        ></v-btn>
        <v-btn icon="mdi-logout" @click="handleLogout"></v-btn>
      </template>
    </v-app-bar>

    <v-main>
      <v-container fluid class="pa-6">
        <!-- Header -->
        <v-row class="mb-4">
          <v-col>
            <h1 class="text-h4 mb-2">My Library</h1>
            <p class="text-grey">{{ booksStore.books.length }} book(s) in your library</p>
          </v-col>
          <v-col cols="auto">
            <v-btn
              color="secondary"
              size="large"
              prepend-icon="mdi-upload"
              @click="goToImport"
              class="mr-2"
            >
              Import Book
            </v-btn>
            <v-btn
              color="primary"
              size="large"
              prepend-icon="mdi-plus"
              @click="goToScraper"
            >
              Add New Book
            </v-btn>
          </v-col>
        </v-row>

        <!-- Loading -->
        <v-row v-if="loading" class="mt-8">
          <v-col class="text-center">
            <v-progress-circular
              indeterminate
              color="primary"
              size="64"
            ></v-progress-circular>
            <p class="mt-4 text-grey">Loading books...</p>
          </v-col>
        </v-row>

        <!-- Empty state -->
        <v-row v-else-if="booksStore.books.length === 0" class="mt-8">
          <v-col class="text-center">
            <v-icon icon="mdi-book-off-outline" size="120" color="grey-lighten-1"></v-icon>
            <h2 class="text-h5 mt-4 mb-2">No Books Yet</h2>
            <p class="text-grey mb-6">Start by scraping a book from any webpage</p>
            <v-btn
              color="primary"
              size="large"
              prepend-icon="mdi-plus"
              @click="goToScraper"
            >
              Add Your First Book
            </v-btn>
          </v-col>
        </v-row>

        <!-- Books grid -->
        <v-row v-else>
          <v-col
            v-for="book in booksStore.sortedBooks"
            :key="book.id"
            cols="12"
            sm="6"
            md="4"
            lg="3"
          >
            <v-card
              class="book-card"
              hover
              @click="openBook(book.id)"
            >
              <v-card-title class="text-h6">
                {{ book.title }}
              </v-card-title>

              <v-card-subtitle v-if="book.author">
                by {{ book.author }}
              </v-card-subtitle>

              <v-card-text>
                <div class="d-flex align-center mb-2">
                  <v-icon icon="mdi-book-outline" size="small" class="mr-2"></v-icon>
                  <span class="text-body-2">{{ book.chapters_count }} chapter(s)</span>
                </div>

                <div class="d-flex align-center mb-2">
                  <v-icon icon="mdi-translate" size="small" class="mr-2"></v-icon>
                  <span class="text-body-2">{{ book.language.toUpperCase() }}</span>
                </div>

                <div class="d-flex align-center mb-2">
                  <v-icon icon="mdi-calendar" size="small" class="mr-2"></v-icon>
                  <span class="text-body-2">{{ formatDate(book.created_at) }}</span>
                </div>

                <!-- Reading Progress -->
                <template v-if="getProgress(book.id)">
                  <v-divider class="my-3"></v-divider>
                  <div class="mb-2">
                    <div class="d-flex align-center justify-space-between mb-1">
                      <span class="text-caption">
                        <v-icon icon="mdi-bookmark-check" size="x-small" class="mr-1"></v-icon>
                        Chapter {{ getProgress(book.id).chapterId + 1 }} of {{ book.chapters_count }}
                      </span>
                      <span class="text-caption font-weight-bold">
                        {{ getProgressPercentage(book.id, book.chapters_count) }}%
                      </span>
                    </div>
                    <v-progress-linear
                      :model-value="getProgressPercentage(book.id, book.chapters_count)"
                      color="primary"
                      height="6"
                      rounded
                    ></v-progress-linear>
                  </div>
                </template>

                <v-chip-group v-if="book.tags && book.tags.length" class="mt-2">
                  <v-chip
                    v-for="tag in book.tags"
                    :key="tag"
                    size="x-small"
                    label
                  >
                    {{ tag }}
                  </v-chip>
                </v-chip-group>
              </v-card-text>

              <v-card-actions>
                <v-btn
                  color="primary"
                  variant="tonal"
                  @click.stop="openBook(book.id)"
                >
                  Read
                </v-btn>

                <v-spacer></v-spacer>

                <v-btn
                  icon="mdi-delete"
                  variant="text"
                  color="error"
                  size="small"
                  @click.stop="confirmDelete(book)"
                ></v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>

    <!-- Delete confirmation dialog -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>Delete Book?</v-card-title>
        <v-card-text>
          Are you sure you want to delete "{{ bookToDelete?.title }}"? This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="error" :loading="deleting" @click="deleteBook">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Error snackbar -->
    <v-snackbar v-model="errorSnackbar" color="error" timeout="5000">
      {{ errorMessage }}
      <template v-slot:actions>
        <v-btn variant="text" @click="errorSnackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useBooksStore } from '@/stores/books'
import { useTheme } from '@/composables/useTheme'
import { useReadingProgress } from '@/composables/useReadingProgress'
import api from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()
const booksStore = useBooksStore()
const { isDark, toggleTheme } = useTheme()
const { getProgress, getProgressPercentage, clearProgress } = useReadingProgress()

const loading = ref(false)
const deleteDialog = ref(false)
const bookToDelete = ref(null)
const deleting = ref(false)
const errorSnackbar = ref(false)
const errorMessage = ref('')

onMounted(async () => {
  await loadBooks()
})

async function loadBooks() {
  loading.value = true
  try {
    const response = await api.books.list()
    booksStore.setBooks(response.data.books)
  } catch (error) {
    console.error('Failed to load books:', error)
    showError('Failed to load books')
  } finally {
    loading.value = false
  }
}

function goToScraper() {
  router.push({ name: 'scraper' })
}

function goToImport() {
  router.push({ name: 'import' })
}

function openBook(bookId) {
  router.push({ name: 'reader', params: { bookId } })
}

function handleLogout() {
  authStore.logout()
}

function confirmDelete(book) {
  bookToDelete.value = book
  deleteDialog.value = true
}

async function deleteBook() {
  if (!bookToDelete.value) return

  deleting.value = true
  try {
    await api.books.delete(bookToDelete.value.id)

    // Also clear reading progress for this book
    clearProgress(bookToDelete.value.id)

    booksStore.removeBook(bookToDelete.value.id)
    deleteDialog.value = false
    bookToDelete.value = null
  } catch (error) {
    console.error('Failed to delete book:', error)
    showError('Failed to delete book')
  } finally {
    deleting.value = false
  }
}

function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

function showError(message) {
  errorMessage.value = message
  errorSnackbar.value = true
}
</script>

<style scoped>
.book-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s;
}

.book-card:hover {
  transform: translateY(-4px);
  cursor: pointer;
}
</style>

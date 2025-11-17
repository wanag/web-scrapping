<template>
  <v-app>
    <v-app-bar color="primary">
      <v-app-bar-nav-icon @click="goBack"></v-app-bar-nav-icon>
      <v-app-bar-title>Add New Book</v-app-bar-title>

      <template v-slot:append>
        <v-btn
          :icon="isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'"
          @click="toggleTheme"
        ></v-btn>
      </template>
    </v-app-bar>

    <v-main>
      <v-container class="pa-6">
        <v-row justify="center">
          <v-col cols="12" md="8" lg="6">
            <v-card>
              <v-card-title class="text-h5">
                Scrape a Book
              </v-card-title>

              <v-card-text>
                <p class="text-body-1 mb-6">
                  Enter the URL of a webpage you want to save as a book. You'll be able to preview and edit the metadata before saving.
                </p>

                <v-form @submit.prevent="startPreview">
                  <v-text-field
                    v-model="url"
                    label="Page URL"
                    placeholder="https://example.com/article"
                    variant="outlined"
                    prepend-inner-icon="mdi-link"
                    :disabled="loading"
                    :error-messages="urlError"
                    clearable
                    class="mb-4"
                  ></v-text-field>

                  <v-select
                    v-model="selectedMode"
                    :items="modes"
                    item-title="label"
                    item-value="value"
                    label="Scraping Mode"
                    variant="outlined"
                    prepend-inner-icon="mdi-format-list-bulleted"
                    hint="Choose how to scrape this page"
                    persistent-hint
                    :disabled="loading"
                    class="mb-4"
                  >
                    <template v-slot:item="{ item, props }">
                      <v-list-item v-bind="props">
                        <v-list-item-subtitle class="mt-1">{{ item.raw.description }}</v-list-item-subtitle>
                      </v-list-item>
                    </template>
                  </v-select>

                  <v-switch
                    v-model="chineseMode"
                    label="Chinese Website Mode"
                    color="primary"
                    hint="Use Chinese character detection to identify content containers (>50% Chinese)"
                    persistent-hint
                    :disabled="loading"
                    class="mb-4"
                  >
                    <template v-slot:label>
                      <div class="d-flex align-center">
                        <v-icon icon="mdi-ideogram-cjk" class="mr-2"></v-icon>
                        <span>Chinese Website Mode</span>
                      </div>
                    </template>
                  </v-switch>

                  <v-switch
                    v-model="simplifyMarkdown"
                    label="Simplified Markdown"
                    color="primary"
                    hint="Keep only headings, paragraphs, and lists. Remove bold, italic, code blocks, images, etc."
                    persistent-hint
                    :disabled="loading"
                    class="mb-4"
                  >
                    <template v-slot:label>
                      <div class="d-flex align-center">
                        <v-icon icon="mdi-format-text" class="mr-2"></v-icon>
                        <span>Simplified Markdown</span>
                      </div>
                    </template>
                  </v-switch>

                  <v-alert
                    v-if="error"
                    type="error"
                    variant="tonal"
                    class="mt-4"
                    closable
                    @click:close="error = null"
                  >
                    {{ error }}
                  </v-alert>

                  <div class="mt-6">
                    <v-btn
                      type="submit"
                      color="primary"
                      size="large"
                      block
                      :loading="loading"
                      :disabled="!url || loading"
                    >
                      <v-icon icon="mdi-eye" class="mr-2"></v-icon>
                      {{ selectedMode === 'index_page' || selectedMode === 'hybrid' ? 'Check Content' : 'Preview Content' }}
                    </v-btn>
                  </div>
                </v-form>
              </v-card-text>
            </v-card>

            <!-- Tips card -->
            <v-card class="mt-6">
              <v-card-title>
                <v-icon icon="mdi-lightbulb-on-outline" class="mr-2"></v-icon>
                Tips
              </v-card-title>
              <v-card-text>
                <ul class="pl-4">
                  <li class="mb-2">Works best with article pages, blog posts, and documentation</li>
                  <li class="mb-2">Automatically removes ads and navigation elements</li>
                  <li class="mb-2">Detects language and extracts metadata</li>
                  <li>Try scraping: Wikipedia articles, Medium posts, blog articles</li>
                </ul>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>

    <!-- Loading dialog -->
    <v-dialog v-model="loadingDialog" persistent max-width="400">
      <v-card>
        <v-card-title>Loading Preview</v-card-title>
        <v-card-text class="text-center py-6">
          <v-progress-circular
            indeterminate
            color="primary"
            size="64"
            class="mb-4"
          ></v-progress-circular>
          <p class="text-body-1">Fetching content from the webpage...</p>
          <p class="text-body-2 text-grey mt-2">This may take a moment</p>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Preview dialog -->
    <v-dialog v-model="previewDialog" max-width="800" scrollable persistent>
      <v-card v-if="previewData">
        <v-card-title class="d-flex align-center">
          <v-icon icon="mdi-eye-outline" class="mr-2"></v-icon>
          Preview & Edit Metadata
        </v-card-title>

        <v-divider></v-divider>

        <v-card-text class="pt-6">
          <!-- Metadata form -->
          <v-form ref="metadataForm">
            <v-text-field
              v-model="editableMetadata.title"
              label="Title"
              variant="outlined"
              prepend-inner-icon="mdi-format-title"
              :rules="[v => !!v || 'Title is required']"
              class="mb-4"
            ></v-text-field>

            <v-text-field
              v-model="editableMetadata.author"
              label="Author (optional)"
              variant="outlined"
              prepend-inner-icon="mdi-account"
              class="mb-4"
            ></v-text-field>

            <v-text-field
              v-model="editableMetadata.language"
              label="Language Code"
              variant="outlined"
              prepend-inner-icon="mdi-translate"
              hint="e.g., en, es, fr, zh, ja"
              class="mb-4"
            ></v-text-field>

            <v-textarea
              v-model="editableMetadata.description"
              label="Description (optional)"
              variant="outlined"
              prepend-inner-icon="mdi-text"
              rows="3"
              class="mb-4"
            ></v-textarea>

            <v-text-field
              v-model="tagsInput"
              label="Tags (comma-separated, optional)"
              variant="outlined"
              prepend-inner-icon="mdi-tag-multiple"
              hint="e.g., fiction, adventure, science"
              class="mb-4"
            ></v-text-field>
          </v-form>

          <v-divider class="my-4"></v-divider>

          <!-- Content size information -->
          <v-expansion-panels class="mb-4">
            <v-expansion-panel>
              <v-expansion-panel-title>
                <div class="d-flex align-center">
                  <v-icon icon="mdi-information-outline" class="mr-2"></v-icon>
                  <span>Content Size Information</span>
                  <v-chip size="x-small" class="ml-3" color="primary" variant="flat">
                    {{ previewData.size_info?.formatted_size || formatSize(previewData.full_length) }}
                  </v-chip>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-list density="compact">
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon icon="mdi-text" size="small"></v-icon>
                    </template>
                    <v-list-item-title>Character Count</v-list-item-title>
                    <v-list-item-subtitle>
                      {{ (previewData.size_info?.character_count || previewData.full_length).toLocaleString() }}
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon icon="mdi-file-document-outline" size="small"></v-icon>
                    </template>
                    <v-list-item-title>Estimated File Size</v-list-item-title>
                    <v-list-item-subtitle>
                      {{ previewData.size_info?.formatted_size || formatSize(previewData.full_length) }}
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item v-if="previewData.size_info?.compression_estimate">
                    <template v-slot:prepend>
                      <v-icon icon="mdi-zip-box" size="small"></v-icon>
                    </template>
                    <v-list-item-title>Compressed Size</v-list-item-title>
                    <v-list-item-subtitle>
                      {{ previewData.size_info.compression_estimate }}
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon icon="mdi-book-outline" size="small"></v-icon>
                    </template>
                    <v-list-item-title>Chapters</v-list-item-title>
                    <v-list-item-subtitle>1 Chapter</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- Container selection panel -->
            <v-expansion-panel v-if="previewData.containers && previewData.containers.length > 0">
              <v-expansion-panel-title>
                <div class="d-flex align-center">
                  <v-icon icon="mdi-code-tags" class="mr-2"></v-icon>
                  <span>HTML Containers</span>
                  <v-chip size="x-small" class="ml-3" color="secondary" variant="flat">
                    {{ selectedContainers.length }} / {{ previewData.containers.length }} selected
                  </v-chip>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="mb-3">
                  <p class="text-caption text-grey mb-2">
                    Select which HTML containers to include in the extracted content. Deselecting containers may reduce unwanted elements.
                  </p>
                  <div class="d-flex gap-2">
                    <v-btn
                      size="x-small"
                      variant="outlined"
                      @click="selectAllContainers"
                    >
                      Select All
                    </v-btn>
                    <v-btn
                      size="x-small"
                      variant="outlined"
                      @click="deselectAllContainers"
                    >
                      Deselect All
                    </v-btn>
                  </div>
                </div>

                <v-list density="compact">
                  <v-list-item
                    v-for="(container, index) in previewData.containers"
                    :key="index"
                    class="container-item"
                  >
                    <template v-slot:prepend>
                      <v-checkbox
                        v-model="selectedContainers"
                        :value="index"
                        hide-details
                        density="compact"
                      ></v-checkbox>
                    </template>

                    <v-list-item-title>
                      <code class="text-caption">
                        &lt;{{ container.type }}
                        <span v-if="container.id" class="text-primary"> id="{{ container.id }}"</span>
                        <span v-if="container.classes" class="text-success"> class="{{ container.classes }}"</span>
                        &gt;
                      </code>
                    </v-list-item-title>

                    <v-list-item-subtitle class="mt-1">
                      <div class="text-caption text-grey">
                        {{ container.content_length.toLocaleString() }} characters
                      </div>
                      <div class="text-caption mt-1 preview-text">
                        {{ container.content_preview }}
                      </div>
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- Index page content preview (for HYBRID mode) -->
            <v-expansion-panel v-if="previewData.mode === 'hybrid' && previewData.index_preview?.index_content">
              <v-expansion-panel-title>
                <div class="d-flex align-center">
                  <v-icon icon="mdi-text-box-outline" class="mr-2"></v-icon>
                  <span>Index Page Content</span>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-card variant="outlined" class="pa-3">
                  <p class="text-caption text-grey mb-2">
                    {{ previewData.index_preview.index_content_length }} characters
                  </p>
                  <p class="text-body-2">{{ previewData.index_preview.index_content }}</p>
                </v-card>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>

          <v-divider class="my-4"></v-divider>

          <!-- Content editing section (only show for ONE_PAGE mode) -->
          <div v-if="previewData.mode === 'one_page'" class="mb-4">
            <div class="d-flex align-center justify-space-between mb-3">
              <h3 class="text-subtitle-1">Content Preview</h3>
              <v-btn
                @click="goToEditor"
                color="secondary"
                variant="outlined"
                size="small"
                :loading="loading"
              >
                <v-icon icon="mdi-pencil" class="mr-2"></v-icon>
                Edit Content
              </v-btn>
            </div>

            <!-- Edited content indicator -->
            <v-alert
              v-if="hasEditedContent"
              type="success"
              variant="tonal"
              density="compact"
              class="mb-3"
            >
              <template v-slot:prepend>
                <v-icon icon="mdi-check-circle"></v-icon>
              </template>
              <small>Content has been edited. The edited version will be used when you save.</small>
            </v-alert>

            <v-card variant="outlined" class="pa-4 preview-content">
              <p class="text-body-2">{{ previewData.content_preview }}</p>
            </v-card>
          </div>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions class="pa-4">
          <v-btn @click="closePreview">Cancel</v-btn>
          <v-spacer></v-spacer>
          <!-- For INDEX_PAGE and HYBRID modes: Show Links in Table -->
          <v-btn
            v-if="selectedMode === 'index_page' || selectedMode === 'hybrid'"
            color="primary"
            @click="openScrapChapter"
          >
            <v-icon icon="mdi-table-large" class="mr-2"></v-icon>
            Show Links in Table
          </v-btn>
          <!-- For ONE_PAGE mode: Scrape & Save Book -->
          <v-btn
            v-else
            color="primary"
            :loading="scraping"
            @click="executeScrape"
          >
            <v-icon icon="mdi-download" class="mr-2"></v-icon>
            Scrape & Save Book
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Scraping progress dialog -->
    <v-dialog v-model="scrapingDialog" persistent max-width="400">
      <v-card>
        <v-card-title>Scraping in Progress</v-card-title>
        <v-card-text class="text-center py-6">
          <v-progress-circular
            indeterminate
            color="primary"
            size="64"
            class="mb-4"
          ></v-progress-circular>
          <p class="text-body-1">Saving book to library...</p>
          <p class="text-body-2 text-grey mt-2">This may take a moment</p>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Success dialog -->
    <v-dialog v-model="successDialog" max-width="400">
      <v-card>
        <v-card-title class="text-success">
          <v-icon icon="mdi-check-circle" class="mr-2"></v-icon>
          Book Added Successfully!
        </v-card-title>
        <v-card-text>
          <p class="mb-2"><strong>Title:</strong> {{ scrapedBook?.title }}</p>
          <p class="mb-2"><strong>Size:</strong> {{ scrapedBook?.size }}</p>
          <p class="mb-2"><strong>Chapters:</strong> {{ scrapedBook?.chapters }}</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="closeSuccessDialog">Add Another</v-btn>
          <v-btn color="primary" @click="openScrapedBook">Read Now</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useBooksStore } from '@/stores/books'
import { useEditorStore } from '@/stores/editor'
import { useTheme } from '@/composables/useTheme'
import api from '@/services/api'

const router = useRouter()
const route = useRoute()
const booksStore = useBooksStore()
const editorStore = useEditorStore()
const { isDark, toggleTheme } = useTheme()

const url = ref('')
const selectedMode = ref('one_page')
const chineseMode = ref(localStorage.getItem('chineseMode') === 'true')
const simplifyMarkdown = ref(localStorage.getItem('simplifyMarkdown') === 'true')
const modes = [
  {
    value: 'one_page',
    label: 'Single Page',
    description: 'Scrape content from a single page'
  },
  {
    value: 'index_page',
    label: 'Index Page',
    description: 'Parse chapter links and scrape each chapter'
  },
  {
    value: 'hybrid',
    label: 'Hybrid',
    description: 'Scrape index page content + linked chapters'
  }
]
const loading = ref(false)
const loadingDialog = ref(false)
const previewDialog = ref(false)
const scrapingDialog = ref(false)
const successDialog = ref(false)
const scraping = ref(false)
const error = ref(null)
const urlError = ref(null)

const previewData = ref(null)
const editableMetadata = ref({
  title: '',
  author: '',
  language: 'en',
  description: '',
  tags: []
})
const tagsInput = ref('')
const scrapedBook = ref(null)
const metadataForm = ref(null)

// Container selection tracking
const selectedContainers = ref([])

// Chapter selection tracking (for INDEX_PAGE and HYBRID modes)
const selectedChapters = ref([])

// Track if content was edited in editor
const hasEditedContent = computed(() => {
  return editorStore.hasActiveSession && editorStore.isContentEdited
})

function goBack() {
  router.push({ name: 'welcome' })
}

async function startPreview() {
  // Validate URL
  if (!url.value) {
    urlError.value = 'Please enter a URL'
    return
  }

  try {
    new URL(url.value)
    urlError.value = null
  } catch {
    urlError.value = 'Please enter a valid URL'
    return
  }

  loading.value = true
  loadingDialog.value = true
  error.value = null

  try {
    const response = await api.scraper.preview(url.value, selectedMode.value, false, chineseMode.value, simplifyMarkdown.value)

    if (response.data.success) {
      previewData.value = response.data

      // Populate editable metadata
      editableMetadata.value = {
        title: response.data.metadata.title || '',
        author: response.data.metadata.author || '',
        language: response.data.metadata.language || 'en',
        description: response.data.metadata.description || '',
        tags: response.data.metadata.tags || []
      }

      // Convert tags array to comma-separated string
      tagsInput.value = editableMetadata.value.tags.join(', ')

      // Initialize all containers as selected
      if (response.data.containers && response.data.containers.length > 0) {
        selectedContainers.value = response.data.containers.map((_, index) => index)
      } else {
        selectedContainers.value = []
      }

      // Initialize all chapters as selected (for INDEX_PAGE and HYBRID modes)
      if (response.data.index_preview && response.data.index_preview.chapters) {
        selectedChapters.value = response.data.index_preview.chapters
          .filter(ch => ch.selected)
          .map(ch => ch.url)
      } else {
        selectedChapters.value = []
      }

      loadingDialog.value = false
      previewDialog.value = true
    } else {
      loadingDialog.value = false
      error.value = response.data.error || 'Failed to preview page'
    }
  } catch (err) {
    loadingDialog.value = false
    if (err.response && err.response.data) {
      error.value = err.response.data.detail || err.response.data.error || 'Failed to preview page'
    } else {
      error.value = 'Failed to preview page. Please check the URL and try again.'
    }
    console.error('Preview error:', err)
  } finally {
    loading.value = false
  }
}

function closePreview() {
  previewDialog.value = false
  previewData.value = null
  // Don't clear editor store - might be returning from editor
}

async function goToEditor() {
  // Load full content and navigate to editor page
  try {
    loading.value = true
    const response = await api.scraper.preview(url.value, 'one_page', true, chineseMode.value, simplifyMarkdown.value)

    console.log('Full content response:', {
      success: response.data.success,
      hasFullContent: !!response.data.full_content,
      fullContentLength: response.data.full_content?.length,
      previewLength: response.data.content_preview?.length
    })

    if (response.data.success && response.data.full_content) {
      // Set editor session with full content and metadata
      editorStore.setEditorSession({
        sourceUrl: url.value,
        previewData: previewData.value,
        editedContent: response.data.full_content,
        editableMetadata: editableMetadata.value,
        scrapeMode: 'one_page',
        containers: response.data.containers || [],
        selectedContainers: selectedContainers.value
      })

      console.log('Editor store content length:', editorStore.editedContent.length)
      console.log('Containers passed to editor:', response.data.containers?.length || 0)

      // Navigate to editor page
      router.push({ name: 'editor' })
    } else {
      error.value = 'Failed to load full content for editing'
      console.error('Full content not available in response')
    }
  } catch (err) {
    error.value = 'Failed to load full content for editing'
    console.error('Load full content error:', err)
  } finally {
    loading.value = false
  }
}

async function executeScrape() {
  // Validate form
  const { valid } = await metadataForm.value.validate()
  if (!valid) {
    return
  }

  scraping.value = true
  previewDialog.value = false
  scrapingDialog.value = true

  try {
    // Convert tags string to array
    const tags = tagsInput.value
      .split(',')
      .map(tag => tag.trim())
      .filter(tag => tag.length > 0)

    const metadataOverrides = {
      title: editableMetadata.value.title,
      author: editableMetadata.value.author || null,
      language: editableMetadata.value.language,
      description: editableMetadata.value.description || null,
      tags: tags
    }

    // Use edited content from editor store if available (only for ONE_PAGE mode)
    const customContent = hasEditedContent.value && selectedMode.value === 'one_page'
      ? editorStore.editedContent
      : null

    // For INDEX_PAGE and HYBRID modes, pass selected chapters
    const selectedChaptersList = (selectedMode.value === 'index_page' || selectedMode.value === 'hybrid')
      ? selectedChapters.value
      : null

    const response = await api.scraper.execute(
      url.value,
      selectedMode.value,
      metadataOverrides,
      customContent,
      selectedChaptersList,
      chineseMode.value,
      simplifyMarkdown.value
    )

    if (response.data.success) {
      scrapedBook.value = {
        id: response.data.book_id,
        title: editableMetadata.value.title,
        size: response.data.total_size,
        chapters: response.data.chapters_saved
      }

      scrapingDialog.value = false
      successDialog.value = true

      // Reload books list in the background
      setTimeout(async () => {
        try {
          const booksResponse = await api.books.list()
          booksStore.setBooks(booksResponse.data.books)
        } catch (err) {
          console.error('Failed to reload books:', err)
        }
      }, 500)
    } else {
      scrapingDialog.value = false
      error.value = response.data.message || 'Failed to scrape page'
    }
  } catch (err) {
    scrapingDialog.value = false
    if (err.response && err.response.data) {
      error.value = err.response.data.detail || err.response.data.error || 'Failed to scrape page'
    } else {
      error.value = 'Failed to scrape page. Please try again.'
    }
    console.error('Scraping error:', err)
  } finally {
    scraping.value = false
  }
}

function closeSuccessDialog() {
  successDialog.value = false
  url.value = ''
  previewData.value = null
  editableMetadata.value = {
    title: '',
    author: '',
    language: 'en',
    description: '',
    tags: []
  }
  tagsInput.value = ''
  scrapedBook.value = null
}

function openScrapedBook() {
  if (scrapedBook.value && scrapedBook.value.id) {
    router.push({ name: 'reader', params: { bookId: scrapedBook.value.id } })
  }
}

function formatSize(length) {
  const kb = length / 1024
  if (kb < 1024) {
    return `${kb.toFixed(1)} KB (${length.toLocaleString()} chars)`
  }
  const mb = kb / 1024
  return `${mb.toFixed(2)} MB (${length.toLocaleString()} chars)`
}

function selectAllContainers() {
  if (previewData.value?.containers) {
    selectedContainers.value = previewData.value.containers.map((_, index) => index)
  }
}

function deselectAllContainers() {
  selectedContainers.value = []
}

function truncateUrl(url) {
  if (url.length > 60) {
    return url.substring(0, 57) + '...'
  }
  return url
}

function openScrapChapter() {
  // Navigate to scrape chapter page with chapter data and metadata
  if (previewData.value?.index_preview?.chapters) {
    console.log('[Scrape Chapter] Opening scrape chapter page with', previewData.value.index_preview.chapters.length, 'chapters')
    console.log('[Scrape Chapter] Currently selected:', selectedChapters.value.length)

    const data = {
      chapters: previewData.value.index_preview.chapters,
      selectedUrls: selectedChapters.value,
      metadata: editableMetadata.value,
      sourceUrl: url.value,
      mode: selectedMode.value
    }

    // Encode data as URL parameter
    const encodedData = encodeURIComponent(JSON.stringify(data))

    // Close preview dialog
    previewDialog.value = false

    router.push({
      name: 'scrape-chapter',
      params: { data: encodedData }
    })
  }
}

// Watch chineseMode and persist to localStorage
watch(chineseMode, (newValue) => {
  localStorage.setItem('chineseMode', newValue.toString())
})

// Watch simplifyMarkdown and persist to localStorage
watch(simplifyMarkdown, (newValue) => {
  localStorage.setItem('simplifyMarkdown', newValue.toString())
})

// Handle returning from editor
onMounted(() => {
  if (route.query.fromEditor === 'true') {
    // Returning from editor - restore preview dialog with updated data
    if (editorStore.hasActiveSession) {
      // Restore URL and preview data
      url.value = editorStore.sourceUrl
      previewData.value = editorStore.previewData

      // Restore metadata (might have been edited)
      editableMetadata.value = { ...editorStore.editableMetadata }
      tagsInput.value = editorStore.editableMetadata.tags.join(', ')

      // Show preview dialog
      previewDialog.value = true
    }
  }
})
</script>

<style scoped>
ul {
  list-style-type: disc;
}

li {
  line-height: 1.6;
}

.preview-content {
  max-height: 300px;
  overflow-y: auto;
  background-color: rgba(0, 0, 0, 0.05);
}

/* Dark mode preview */
.v-theme--dark .preview-content {
  background-color: rgba(255, 255, 255, 0.05);
  color: #e0e0e0;
}

.preview-content p {
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.6;
}

/* Container selection styling */
.container-item {
  border-left: 3px solid rgba(var(--v-theme-primary), 0.3);
  margin-bottom: 8px;
  padding-left: 8px;
}

.preview-text {
  font-family: monospace;
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.6);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.v-theme--dark .preview-text {
  color: rgba(255, 255, 255, 0.6);
}
</style>

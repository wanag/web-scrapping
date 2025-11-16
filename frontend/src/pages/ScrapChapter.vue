<template>
  <v-container fluid class="pa-6">
    <v-card>
      <!-- Header -->
      <v-card-title class="d-flex align-center justify-space-between bg-primary">
        <div class="d-flex align-center">
          <v-icon icon="mdi-table-large" class="mr-3" size="large"></v-icon>
          <div>
            <h2 class="text-h5">Scrape Chapters</h2>
            <p class="text-caption mt-1 text-grey-lighten-2">
              Select chapters, adjust settings, and start scraping.
            </p>
          </div>
        </div>
        <v-chip color="white" variant="flat" class="font-weight-bold">
          {{ selectedLinks.length }} / {{ displayChapters.length }} selected
        </v-chip>
      </v-card-title>

      <v-card-text class="pa-4">
        <!-- Metadata Editing Section -->
        <v-expansion-panels class="mb-4">
          <v-expansion-panel>
            <v-expansion-panel-title>
              <div class="d-flex align-center">
                <v-icon icon="mdi-pencil" class="mr-2"></v-icon>
                <span>Edit Book Metadata</span>
              </div>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="metadata.title"
                    label="Book Title"
                    outlined
                    dense
                    hide-details="auto"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="metadata.author"
                    label="Author"
                    outlined
                    dense
                    hide-details="auto"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="metadata.language"
                    :items="languages"
                    label="Language"
                    outlined
                    dense
                    hide-details="auto"
                  ></v-select>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="tagsInput"
                    label="Tags (comma-separated)"
                    outlined
                    dense
                    hide-details="auto"
                  ></v-text-field>
                </v-col>
                <v-col cols="12">
                  <v-textarea
                    v-model="metadata.description"
                    label="Description"
                    outlined
                    rows="3"
                    hide-details="auto"
                  ></v-textarea>
                </v-col>
              </v-row>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>

        <!-- Chinese Mode Toggle -->
        <v-card class="mb-4" variant="outlined">
          <v-card-text>
            <v-switch
              v-model="chineseMode"
              color="primary"
              hide-details
            >
              <template v-slot:label>
                <div class="d-flex align-center">
                  <v-icon icon="mdi-ideogram-cjk" class="mr-2" color="primary"></v-icon>
                  <div>
                    <div class="font-weight-bold">Chinese Website Mode</div>
                    <div class="text-caption text-medium-emphasis">
                      Use Chinese character detection to identify content containers (>50% Chinese)
                    </div>
                  </div>
                </div>
              </template>
            </v-switch>
          </v-card-text>
        </v-card>

        <!-- Action Buttons -->
        <div class="d-flex gap-2 mb-4">
          <v-btn
            color="primary"
            variant="outlined"
            prepend-icon="mdi-checkbox-multiple-marked"
            @click="selectAll"
            :disabled="scraping"
          >
            Select All
          </v-btn>
          <v-btn
            color="primary"
            variant="outlined"
            prepend-icon="mdi-checkbox-multiple-blank-outline"
            @click="deselectAll"
            :disabled="scraping"
          >
            Deselect All
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn
            color="success"
            variant="elevated"
            prepend-icon="mdi-download"
            @click="startScraping"
            :disabled="selectedLinks.length === 0 || scraping"
            :loading="scraping"
            size="large"
          >
            Start Scraping
          </v-btn>
        </div>

        <!-- Clustering Controls -->
        <v-card variant="outlined" class="mb-4 pa-4">
          <h3 class="text-subtitle-1 mb-3">
            <v-icon icon="mdi-group" class="mr-2"></v-icon>
            URL Clustering
          </h3>

          <v-row align="center">
            <v-col cols="12" md="6">
              <v-slider
                v-model="clusterThreshold"
                :min="0.5"
                :max="1.0"
                :step="0.05"
                label="Similarity Threshold"
                thumb-label="always"
                :thumb-size="24"
                color="primary"
                :disabled="scraping"
              >
                <template v-slot:append>
                  <v-chip size="small" :color="getThresholdColor(clusterThreshold)">
                    {{ getThresholdLabel(clusterThreshold) }}
                  </v-chip>
                </template>
              </v-slider>
            </v-col>

            <v-col cols="12" md="6">
              <v-btn
                color="secondary"
                variant="elevated"
                prepend-icon="mdi-group"
                @click="applyClusteringFilter"
                :disabled="scraping"
                block
              >
                Apply Clustering
              </v-btn>
              <v-btn
                variant="text"
                size="small"
                @click="resetClustering"
                :disabled="scraping"
                block
                class="mt-2"
              >
                Reset to All Links
              </v-btn>
            </v-col>
          </v-row>

          <v-alert v-if="clusteringApplied" type="info" variant="tonal" density="compact" class="mt-3">
            Showing {{ displayChapters.length }} links from largest cluster (threshold: {{ clusterThreshold }})
          </v-alert>
        </v-card>

        <!-- Scraping Progress Alert -->
        <v-alert v-if="scraping" type="info" variant="tonal" class="mb-4">
          <div class="d-flex align-center">
            <v-progress-circular
              indeterminate
              color="primary"
              size="20"
              width="2"
              class="mr-3"
            ></v-progress-circular>
            <span>Scraping in progress: {{ scrapedCount }} / {{ selectedLinks.length }} chapters completed</span>
          </div>
        </v-alert>

        <!-- Data Table -->
        <v-data-table
          v-model="selectedLinks"
          :headers="headers"
          :items="displayChapters"
          item-value="url"
          show-select
          :items-per-page="-1"
          class="elevation-1"
          density="comfortable"
        >
          <!-- Order Column -->
          <template v-slot:item.order="{ item }">
            <v-chip size="small" color="grey-lighten-2" variant="flat">
              {{ item.order + 1 }}
            </v-chip>
          </template>

          <!-- Name Column -->
          <template v-slot:item.name="{ item }">
            <span class="font-weight-medium">{{ item.name }}</span>
          </template>

          <!-- URL Column -->
          <template v-slot:item.url="{ item }">
            <a
              :href="item.url"
              target="_blank"
              class="text-primary text-decoration-none"
              @click.stop
            >
              {{ truncateUrl(item.url) }}
              <v-icon icon="mdi-open-in-new" size="x-small" class="ml-1"></v-icon>
            </a>
          </template>

          <!-- Status Column -->
          <template v-slot:item.status="{ item }">
            <v-chip
              v-if="item.status"
              :color="getStatusColor(item.status)"
              size="small"
              variant="flat"
            >
              <v-icon
                v-if="item.status === 'scraping'"
                icon="mdi-loading"
                class="mr-1 rotating"
                size="x-small"
              ></v-icon>
              <v-icon
                v-else-if="item.status === 'done'"
                icon="mdi-check"
                class="mr-1"
                size="x-small"
              ></v-icon>
              <v-icon
                v-else-if="item.status === 'error'"
                icon="mdi-alert-circle"
                class="mr-1"
                size="x-small"
              ></v-icon>
              {{ item.status }}
            </v-chip>
            <span v-else class="text-grey">-</span>
          </template>

          <!-- Actions Column -->
          <template v-slot:item.actions="{ item }">
            <v-tooltip text="Preview chapter" location="top">
              <template v-slot:activator="{ props }">
                <v-btn
                  icon="mdi-eye"
                  size="x-small"
                  variant="text"
                  color="primary"
                  v-bind="props"
                  @click="openChapterPreview(item)"
                  :disabled="scraping"
                ></v-btn>
              </template>
            </v-tooltip>
            <v-icon
              v-if="hasEditedContent(item.url)"
              icon="mdi-pencil"
              size="x-small"
              color="success"
              class="ml-1"
            ></v-icon>
          </template>
        </v-data-table>

        <!-- Info Alert -->
        <v-alert
          v-if="displayChapters.length === 0"
          type="warning"
          variant="tonal"
          class="mt-4"
        >
          No chapter links {{ clusteringApplied ? 'in cluster' : 'found' }}. {{ clusteringApplied ? 'Try adjusting the threshold or resetting.' : 'Please go back and try with a different URL or mode.' }}
        </v-alert>
      </v-card-text>
    </v-card>

    <!-- Chapter Preview Dialog -->
    <v-dialog v-model="previewDialog" max-width="900" scrollable>
      <v-card>
        <v-card-title class="bg-primary text-white">
          <v-icon icon="mdi-eye" class="mr-2"></v-icon>
          Preview Chapter: {{ previewingChapter?.name || '' }}
        </v-card-title>

        <v-card-text class="pa-4" style="max-height: 70vh">
          <v-progress-linear v-if="loadingPreview" indeterminate color="primary"></v-progress-linear>

          <div v-else-if="chapterPreviewData">
            <!-- Content Preview Section -->
            <v-expansion-panels class="mb-4">
              <v-expansion-panel>
                <v-expansion-panel-title>
                  <div class="d-flex align-center">
                    <v-icon icon="mdi-text-box" class="mr-2"></v-icon>
                    <span>Content Preview</span>
                    <v-chip size="x-small" class="ml-3" variant="flat" color="grey">
                      {{ chapterPreviewData.full_length?.toLocaleString() || 0 }} characters
                    </v-chip>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <v-alert type="info" variant="tonal" density="compact" class="mb-3">
                    First ~500 characters preview. Click "Edit Full Content" to modify the entire content.
                  </v-alert>
                  <div class="preview-box pa-3 bg-grey-lighten-4 rounded">
                    <pre class="text-body-2">{{ chapterPreviewData.content_preview }}</pre>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <!-- Full Content Editing -->
              <v-expansion-panel>
                <v-expansion-panel-title>
                  <div class="d-flex align-center">
                    <v-icon icon="mdi-pencil" class="mr-2"></v-icon>
                    <span>Edit Full Content</span>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <v-textarea
                    v-model="editedChapterContent"
                    label="Full Chapter Content"
                    rows="15"
                    variant="outlined"
                    auto-grow
                    hide-details
                  ></v-textarea>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <!-- Container Selection (if available) -->
              <v-expansion-panel v-if="chapterPreviewData.containers && chapterPreviewData.containers.length > 0">
                <v-expansion-panel-title>
                  <div class="d-flex align-center">
                    <v-icon icon="mdi-package-variant" class="mr-2"></v-icon>
                    <span>Container Selection</span>
                    <v-chip size="x-small" class="ml-3" variant="flat" color="primary">
                      {{ selectedChapterContainers?.length || chapterPreviewData.containers.length }} / {{ chapterPreviewData.containers.length }} selected
                    </v-chip>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <p class="text-caption text-grey mb-2">
                    Multiple content containers detected. Select which ones to include.
                  </p>
                  <div class="d-flex gap-2 mb-3">
                    <v-btn size="x-small" variant="outlined" @click="selectAllPreviewContainers">
                      Select All
                    </v-btn>
                    <v-btn size="x-small" variant="outlined" @click="deselectAllPreviewContainers">
                      Deselect All
                    </v-btn>
                  </div>

                  <v-list density="compact" max-height="300" class="overflow-y-auto">
                    <v-list-item
                      v-for="(container, index) in chapterPreviewData.containers"
                      :key="index"
                      class="container-item"
                    >
                      <template v-slot:prepend>
                        <v-checkbox
                          v-model="selectedChapterContainers"
                          :value="index"
                          hide-details
                          density="compact"
                        ></v-checkbox>
                      </template>

                      <v-list-item-title>
                        <v-chip size="x-small" class="mr-2">{{ container.type }}</v-chip>
                        <span class="text-caption">{{ container.content_length }} chars</span>
                      </v-list-item-title>

                      <v-list-item-subtitle class="mt-1">
                        <span class="text-caption">{{ container.content_preview.substring(0, 100) }}...</span>
                      </v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions class="pa-4">
          <v-btn @click="closeChapterPreview">Cancel</v-btn>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            variant="elevated"
            @click="saveChapterPreview"
            prepend-icon="mdi-content-save"
          >
            Save Edits
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Success Dialog -->
    <v-dialog v-model="successDialog" max-width="500" persistent>
      <v-card>
        <v-card-title class="bg-success text-white">
          <v-icon icon="mdi-check-circle" class="mr-2"></v-icon>
          Scraping Complete!
        </v-card-title>
        <v-card-text class="pa-6">
          <p class="text-h6 mb-3">Book saved successfully!</p>
          <v-list density="compact">
            <v-list-item>
              <template v-slot:prepend>
                <v-icon icon="mdi-book" class="mr-2"></v-icon>
              </template>
              <v-list-item-title>{{ scrapedCount }} chapters scraped</v-list-item-title>
            </v-list-item>
            <v-list-item v-if="errorCount > 0">
              <template v-slot:prepend>
                <v-icon icon="mdi-alert-circle" color="warning" class="mr-2"></v-icon>
              </template>
              <v-list-item-title>{{ errorCount }} chapters failed</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" variant="elevated" @click="goToWelcome">
            Go to Library
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Error Dialog -->
    <v-dialog v-model="errorDialog" max-width="500">
      <v-card>
        <v-card-title class="bg-error text-white">
          <v-icon icon="mdi-alert-circle" class="mr-2"></v-icon>
          Scraping Failed
        </v-card-title>
        <v-card-text class="pa-6">
          <p>{{ errorMessage }}</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="errorDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()

// Data from route params
const chapters = ref([])
const selectedLinks = ref([])
const metadata = ref({
  title: '',
  author: '',
  language: 'en',
  description: '',
  tags: []
})
const tagsInput = ref('')
const sourceUrl = ref('')
const mode = ref('index_page')
const chineseMode = ref(localStorage.getItem('chineseMode') === 'true')

// Clustering state
const clusterThreshold = ref(0.9)
const clusteringApplied = ref(false)
const filteredChapters = ref([])

// Scraping state
const scraping = ref(false)
const scrapedCount = ref(0)
const errorCount = ref(0)
const successDialog = ref(false)
const errorDialog = ref(false)
const errorMessage = ref('')

// Chapter preview state
const previewDialog = ref(false)
const loadingPreview = ref(false)
const previewingChapter = ref(null)
const chapterPreviewData = ref(null)
const editedChapterContent = ref('')
const selectedChapterContainers = ref([])
const editedChapterData = ref(new Map()) // Map<chapterUrl, {customContent, selectedContainers}>

// Languages list
const languages = [
  { title: 'English', value: 'en' },
  { title: 'Chinese (Simplified)', value: 'zh-CN' },
  { title: 'Chinese (Traditional)', value: 'zh-TW' },
  { title: 'Spanish', value: 'es' },
  { title: 'French', value: 'fr' },
  { title: 'German', value: 'de' },
  { title: 'Japanese', value: 'ja' },
  { title: 'Korean', value: 'ko' }
]

// Computed property for display
const displayChapters = computed(() => {
  return clusteringApplied.value ? filteredChapters.value : chapters.value
})

// Table headers
const headers = [
  { title: 'Order', key: 'order', sortable: true, width: '100px' },
  { title: 'Chapter Name', key: 'name', sortable: false },
  { title: 'URL', key: 'url', sortable: false },
  { title: 'Status', key: 'status', sortable: false, width: '120px' },
  { title: 'Actions', key: 'actions', sortable: false, width: '100px' }
]

// Watch chineseMode and persist to localStorage
watch(chineseMode, (newValue) => {
  localStorage.setItem('chineseMode', newValue.toString())
})

onMounted(() => {
  // Get data from route params
  if (router.currentRoute.value.params.data) {
    try {
      const data = JSON.parse(decodeURIComponent(router.currentRoute.value.params.data))
      chapters.value = data.chapters || []
      selectedLinks.value = data.selectedUrls || []

      // Get metadata and source URL
      if (data.metadata) {
        metadata.value = { ...data.metadata }
        tagsInput.value = (data.metadata.tags || []).join(', ')
      }
      sourceUrl.value = data.sourceUrl || ''
      mode.value = data.mode || 'index_page'

      // Initialize status for all chapters
      chapters.value.forEach(ch => {
        ch.status = null
      })
    } catch (error) {
      console.error('Failed to parse route data:', error)
    }
  }
})

function selectAll() {
  selectedLinks.value = displayChapters.value.map(ch => ch.url)
}

function deselectAll() {
  selectedLinks.value = []
}

function truncateUrl(url) {
  if (url.length > 80) {
    return url.substring(0, 77) + '...'
  }
  return url
}

async function startScraping() {
  if (selectedLinks.value.length === 0) {
    return
  }

  // Validate metadata
  if (!metadata.value.title || metadata.value.title.trim() === '') {
    errorMessage.value = 'Please enter a book title before scraping.'
    errorDialog.value = true
    return
  }

  // Parse tags from input
  metadata.value.tags = tagsInput.value
    .split(',')
    .map(tag => tag.trim())
    .filter(tag => tag.length > 0)

  scraping.value = true
  scrapedCount.value = 0
  errorCount.value = 0

  try {
    // Step 1: Create book with metadata
    console.log('[Scrape Chapter] Creating book with metadata')
    const createResponse = await api.scraper.createBook({
      title: metadata.value.title,
      source_url: sourceUrl.value,
      author: metadata.value.author || null,
      language: metadata.value.language,
      tags: metadata.value.tags,
      description: metadata.value.description || null,
      scrape_mode: mode.value
    })

    if (!createResponse.data.success) {
      throw new Error(createResponse.data.message || 'Failed to create book')
    }

    const bookId = createResponse.data.book_id
    console.log('[Scrape Chapter] Book created with ID:', bookId)

    // Step 2: Scrape each selected chapter sequentially
    const selectedChaptersList = displayChapters.value.filter(ch =>
      selectedLinks.value.includes(ch.url)
    )

    for (let i = 0; i < selectedChaptersList.length; i++) {
      const chapter = selectedChaptersList[i]

      // Update status to scraping
      chapter.status = 'scraping'

      try {
        console.log(`[Scrape Chapter] Scraping chapter ${i + 1}/${selectedChaptersList.length}: ${chapter.name}`)

        // Check if this chapter has edited content
        const editedData = editedChapterData.value.get(chapter.url)

        let chapterResponse
        if (editedData) {
          console.log(`[Scrape Chapter] Using edited content for: ${chapter.name}`)
          chapterResponse = await api.scraper.addChapter(
            bookId,
            chapter.url,
            i,
            chapter.name,
            editedData.customContent,
            editedData.selectedContainers,
            chineseMode.value
          )
        } else {
          console.log(`[Scrape Chapter] Scraping from URL: ${chapter.url}`)
          chapterResponse = await api.scraper.addChapter(
            bookId,
            chapter.url,
            i,
            chapter.name,
            null,
            null,
            chineseMode.value
          )
        }

        if (chapterResponse.data.success) {
          chapter.status = 'done'
          scrapedCount.value++
        } else {
          chapter.status = 'error'
          errorCount.value++
          console.error(`Failed to scrape chapter ${chapter.name}:`, chapterResponse.data.error)
        }
      } catch (error) {
        chapter.status = 'error'
        errorCount.value++
        console.error(`Error scraping chapter ${chapter.name}:`, error)
      }
    }

    // Step 3: Show success and redirect
    scraping.value = false
    if (scrapedCount.value > 0) {
      successDialog.value = true
    } else {
      errorMessage.value = 'All chapters failed to scrape. Please check the URLs and try again.'
      errorDialog.value = true
    }

  } catch (error) {
    scraping.value = false
    errorMessage.value = error.message || 'Failed to create book. Please try again.'
    errorDialog.value = true
    console.error('[Scrape Chapter] Error:', error)
  }
}

function goToWelcome() {
  router.push({ name: 'welcome' })
}

function getStatusColor(status) {
  switch (status) {
    case 'queued': return 'grey'
    case 'scraping': return 'primary'
    case 'done': return 'success'
    case 'error': return 'error'
    default: return 'grey'
  }
}

// Chapter preview functions
async function openChapterPreview(chapter) {
  previewingChapter.value = chapter
  previewDialog.value = true
  loadingPreview.value = true
  chapterPreviewData.value = null
  editedChapterContent.value = ''
  selectedChapterContainers.value = []

  try {
    console.log('[Chapter Preview] Previewing chapter:', chapter.name, chapter.url)

    // Call preview API with one_page mode
    const response = await api.scraper.preview(chapter.url, 'one_page', true, chineseMode.value)

    if (response.data.success) {
      chapterPreviewData.value = response.data
      editedChapterContent.value = response.data.full_content || ''

      // Initialize selected containers (all selected by default)
      if (response.data.containers && response.data.containers.length > 0) {
        selectedChapterContainers.value = response.data.containers.map((_, idx) => idx)
      }

      console.log('[Chapter Preview] Preview loaded successfully')
    } else {
      errorMessage.value = 'Failed to load chapter preview: ' + (response.data.error || 'Unknown error')
      errorDialog.value = true
      previewDialog.value = false
    }
  } catch (error) {
    console.error('[Chapter Preview] Error loading preview:', error)
    errorMessage.value = 'Failed to load chapter preview: ' + (error.message || 'Unknown error')
    errorDialog.value = true
    previewDialog.value = false
  } finally {
    loadingPreview.value = false
  }
}

function saveChapterPreview() {
  if (!previewingChapter.value) return

  // Store edited content and selected containers
  editedChapterData.value.set(previewingChapter.value.url, {
    customContent: editedChapterContent.value,
    selectedContainers: selectedChapterContainers.value.length === chapterPreviewData.value?.containers?.length
      ? null // All containers selected, pass null
      : selectedChapterContainers.value
  })

  console.log('[Chapter Preview] Saved edits for:', previewingChapter.value.name)

  // Close dialog
  previewDialog.value = false
  previewingChapter.value = null
  chapterPreviewData.value = null
}

function closeChapterPreview() {
  previewDialog.value = false
  previewingChapter.value = null
  chapterPreviewData.value = null
  editedChapterContent.value = ''
  selectedChapterContainers.value = []
}

function hasEditedContent(chapterUrl) {
  return editedChapterData.value.has(chapterUrl)
}

function selectAllPreviewContainers() {
  if (chapterPreviewData.value?.containers) {
    selectedChapterContainers.value = chapterPreviewData.value.containers.map((_, idx) => idx)
  }
}

function deselectAllPreviewContainers() {
  selectedChapterContainers.value = []
}

// URL similarity calculation
function calculateUrlSimilarity(url1, url2) {
  const getPathSegments = (url) => {
    try {
      const parsed = new URL(url)
      return parsed.pathname.split('/').filter(s => s.length > 0)
    } catch {
      return []
    }
  }

  const segments1 = getPathSegments(url1)
  const segments2 = getPathSegments(url2)

  if (segments1.length !== segments2.length) return 0.0

  let matching = 0
  for (let i = 0; i < segments1.length; i++) {
    if (segments1[i] === segments2[i]) {
      matching += 1
    } else {
      // Check if segments differ only in numbers
      const seg1NoDigits = segments1[i].replace(/\d+/g, '')
      const seg2NoDigits = segments2[i].replace(/\d+/g, '')
      if (seg1NoDigits === seg2NoDigits && seg1NoDigits.length > 0) {
        matching += 0.9
      }
    }
  }

  return segments1.length > 0 ? matching / segments1.length : 0.0
}

// Clustering algorithm
function clusterLinks(links, threshold) {
  if (links.length < 2) return [links]

  const clusters = []
  const used = new Set()

  for (let i = 0; i < links.length; i++) {
    if (used.has(i)) continue

    const cluster = [links[i]]
    used.add(i)

    for (let j = i + 1; j < links.length; j++) {
      if (used.has(j)) continue

      const similarity = calculateUrlSimilarity(links[i].url, links[j].url)

      if (similarity >= threshold) {
        cluster.push(links[j])
        used.add(j)
      }
    }

    if (cluster.length > 1) {
      clusters.push(cluster)
    }
  }

  // Sort by cluster size (largest first)
  clusters.sort((a, b) => b.length - a.length)

  return clusters
}

// Apply clustering filter
function applyClusteringFilter() {
  if (chapters.value.length === 0) return

  // When threshold is 1.0, show all links
  if (clusterThreshold.value >= 1.0) {
    filteredChapters.value = [...chapters.value]
    // Renumber order sequentially
    filteredChapters.value.forEach((ch, idx) => {
      ch.order = idx
    })
    clusteringApplied.value = true
    return
  }

  // Cluster the links
  const clusters = clusterLinks(chapters.value, clusterThreshold.value)

  if (clusters.length > 0) {
    // Show only the largest cluster
    filteredChapters.value = clusters[0]
    // Renumber order sequentially
    filteredChapters.value.forEach((ch, idx) => {
      ch.order = idx
    })
    clusteringApplied.value = true

    // Update selection to only include links from cluster
    selectedLinks.value = selectedLinks.value.filter(url =>
      filteredChapters.value.some(ch => ch.url === url)
    )
  } else {
    // No clusters found - show all
    filteredChapters.value = [...chapters.value]
    // Renumber order sequentially
    filteredChapters.value.forEach((ch, idx) => {
      ch.order = idx
    })
    clusteringApplied.value = true
  }
}

// Reset clustering
function resetClustering() {
  filteredChapters.value = []
  clusteringApplied.value = false
  clusterThreshold.value = 0.9
}

// Helper functions for threshold display
function getThresholdColor(value) {
  if (value >= 1.0) return 'grey'
  if (value >= 0.95) return 'success'
  if (value >= 0.8) return 'warning'
  return 'error'
}

function getThresholdLabel(value) {
  if (value >= 1.0) return 'All Links'
  if (value >= 0.95) return 'Very Strict'
  if (value >= 0.85) return 'Strict'
  if (value >= 0.75) return 'Moderate'
  return 'Lenient'
}
</script>

<style scoped>
.v-data-table {
  border-radius: 8px;
}

:deep(.v-data-table__th) {
  font-weight: 600 !important;
  background-color: rgba(var(--v-theme-primary), 0.05);
}

:deep(.v-data-table__tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.02);
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.rotating {
  animation: rotate 1s linear infinite;
}
</style>

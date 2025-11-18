<template>
  <v-app>
    <v-app-bar color="primary" density="compact">
      <v-app-bar-nav-icon @click="goBack"></v-app-bar-nav-icon>
      <v-app-bar-title>Import Book</v-app-bar-title>
    </v-app-bar>

    <v-main>
      <v-container class="py-6">
        <v-card>
          <v-tabs v-model="tab" bg-color="primary">
            <v-tab value="file">Single File</v-tab>
            <v-tab value="folder">Folder (ZIP)</v-tab>
          </v-tabs>

          <v-card-text class="px-0">
            <!-- Single File Import Tab -->
            <v-window v-model="tab">
              <v-window-item value="file">
                <v-container>
                  <!-- File Upload Area -->
                  <v-card
                    variant="outlined"
                    :class="{
                      'drop-zone': true,
                      'drop-zone-active': isDraggingFile
                    }"
                    @drop.prevent="handleFileDrop"
                    @dragover.prevent="isDraggingFile = true"
                    @dragleave.prevent="isDraggingFile = false"
                  >
                    <v-card-text class="text-center pa-8">
                      <v-icon icon="mdi-file-document-outline" size="64" color="primary"></v-icon>
                      <h3 class="text-h6 mt-4">Drop .txt or .md file here</h3>
                      <p class="text-grey mt-2">or</p>
                      <v-btn color="primary" class="mt-2" @click="$refs.fileInput.click()">
                        Browse Files
                      </v-btn>
                      <input
                        ref="fileInput"
                        type="file"
                        accept=".txt,.md"
                        style="display: none"
                        @change="handleFileSelect"
                      />
                      <p v-if="selectedFile" class="mt-4 text-success">
                        <v-icon icon="mdi-check-circle" color="success"></v-icon>
                        {{ selectedFile.name }}
                      </p>
                    </v-card-text>
                  </v-card>

                  <!-- Metadata Form for File Import -->
                  <v-card v-if="selectedFile" class="mt-6" variant="outlined">
                    <v-card-title>Book Information</v-card-title>
                    <v-card-text>
                      <v-text-field
                        v-model="fileMetadata.title"
                        label="Title"
                        hint="Auto-detected from content if empty"
                        persistent-hint
                        variant="outlined"
                        density="comfortable"
                      ></v-text-field>

                      <v-text-field
                        v-model="fileMetadata.author"
                        label="Author"
                        variant="outlined"
                        density="comfortable"
                        class="mt-4"
                      ></v-text-field>

                      <v-select
                        v-model="fileMetadata.language"
                        :items="languageOptions"
                        label="Language"
                        variant="outlined"
                        density="comfortable"
                        class="mt-4"
                      ></v-select>

                      <v-combobox
                        v-model="fileMetadata.tags"
                        label="Tags"
                        hint="Press Enter to add tags"
                        persistent-hint
                        multiple
                        chips
                        variant="outlined"
                        density="comfortable"
                        class="mt-4"
                      ></v-combobox>

                      <v-textarea
                        v-model="fileMetadata.description"
                        label="Description"
                        variant="outlined"
                        rows="3"
                        class="mt-4"
                      ></v-textarea>
                    </v-card-text>
                  </v-card>

                  <!-- Import Button -->
                  <v-card-actions v-if="selectedFile" class="mt-4">
                    <v-spacer></v-spacer>
                    <v-btn variant="text" @click="resetFileImport">Cancel</v-btn>
                    <v-btn color="primary" @click="importFile" :loading="importing">
                      Import Book
                    </v-btn>
                  </v-card-actions>
                </v-container>
              </v-window-item>

              <!-- Folder Import Tab -->
              <v-window-item value="folder">
                <v-container>
                  <!-- ZIP Upload Area -->
                  <v-card
                    variant="outlined"
                    :class="{
                      'drop-zone': true,
                      'drop-zone-active': isDraggingZip
                    }"
                    @drop.prevent="handleZipDrop"
                    @dragover.prevent="isDraggingZip = true"
                    @dragleave.prevent="isDraggingZip = false"
                  >
                    <v-card-text class="text-center pa-8">
                      <v-icon icon="mdi-folder-zip-outline" size="64" color="primary"></v-icon>
                      <h3 class="text-h6 mt-4">Drop ZIP file here</h3>
                      <p class="text-grey mt-2">or</p>
                      <v-btn color="primary" class="mt-2" @click="$refs.zipInput.click()">
                        Browse Files
                      </v-btn>
                      <input
                        ref="zipInput"
                        type="file"
                        accept=".zip"
                        style="display: none"
                        @change="handleZipSelect"
                      />
                      <p v-if="selectedZip" class="mt-4 text-success">
                        <v-icon icon="mdi-check-circle" color="success"></v-icon>
                        {{ selectedZip.name }}
                      </p>
                    </v-card-text>
                  </v-card>

                  <!-- Validate Button -->
                  <v-card-actions v-if="selectedZip && !validationResult" class="mt-4">
                    <v-spacer></v-spacer>
                    <v-btn variant="text" @click="resetZipImport">Cancel</v-btn>
                    <v-btn color="primary" @click="validateZip" :loading="validating">
                      Validate & Preview
                    </v-btn>
                  </v-card-actions>

                  <!-- Validation Results -->
                  <v-card v-if="validationResult" class="mt-6" variant="outlined">
                    <v-card-title>
                      <v-icon
                        :icon="validationResult.valid ? 'mdi-check-circle' : 'mdi-alert-circle'"
                        :color="validationResult.valid ? 'success' : 'error'"
                        class="mr-2"
                      ></v-icon>
                      Validation {{ validationResult.valid ? 'Passed' : 'Failed' }}
                    </v-card-title>

                    <!-- Errors -->
                    <v-card-text v-if="validationResult.errors.length > 0">
                      <v-alert type="error" variant="tonal" class="mb-4">
                        <div class="text-subtitle-2 mb-2">Errors:</div>
                        <ul>
                          <li v-for="(error, idx) in validationResult.errors" :key="idx">{{ error }}</li>
                        </ul>
                      </v-alert>
                    </v-card-text>

                    <!-- Warnings -->
                    <v-card-text v-if="validationResult.warnings.length > 0">
                      <v-alert type="warning" variant="tonal" class="mb-4">
                        <div class="text-subtitle-2 mb-2">Warnings:</div>
                        <ul>
                          <li v-for="(warning, idx) in validationResult.warnings" :key="idx">{{ warning }}</li>
                        </ul>
                      </v-alert>
                    </v-card-text>

                    <!-- Detected Info -->
                    <v-card-text v-if="validationResult.valid">
                      <div class="mb-4">
                        <h4 class="text-subtitle-1 mb-2">Detected Information:</h4>
                        <v-chip class="mr-2 mb-2" size="small">
                          {{ validationResult.chapters_count }} chapter{{validationResult.chapters_count !== 1 ? 's' : ''}}
                        </v-chip>
                        <v-chip v-if="validationResult.metadata" class="mr-2 mb-2" size="small">
                          Language: {{ validationResult.metadata.language }}
                        </v-chip>
                      </div>

                      <!-- Metadata Override Form -->
                      <v-divider class="my-4"></v-divider>
                      <h4 class="text-subtitle-1 mb-4">Edit Book Information:</h4>

                      <v-text-field
                        v-model="folderMetadata.title"
                        label="Title"
                        variant="outlined"
                        density="comfortable"
                      ></v-text-field>

                      <v-text-field
                        v-model="folderMetadata.author"
                        label="Author"
                        variant="outlined"
                        density="comfortable"
                        class="mt-4"
                      ></v-text-field>

                      <v-select
                        v-model="folderMetadata.language"
                        :items="languageOptions"
                        label="Language"
                        variant="outlined"
                        density="comfortable"
                        class="mt-4"
                      ></v-select>

                      <v-combobox
                        v-model="folderMetadata.tags"
                        label="Tags"
                        hint="Press Enter to add tags"
                        persistent-hint
                        multiple
                        chips
                        variant="outlined"
                        density="comfortable"
                        class="mt-4"
                      ></v-combobox>

                      <v-textarea
                        v-model="folderMetadata.description"
                        label="Description"
                        variant="outlined"
                        rows="3"
                        class="mt-4"
                      ></v-textarea>
                    </v-card-text>
                  </v-card>

                  <!-- Import Actions -->
                  <v-card-actions v-if="validationResult && validationResult.valid" class="mt-4">
                    <v-spacer></v-spacer>
                    <v-btn variant="text" @click="resetZipImport">Cancel</v-btn>
                    <v-btn color="primary" @click="importFolder" :loading="importing">
                      Import {{ validationResult.chapters_count }} Chapter{{validationResult.chapters_count !== 1 ? 's' : ''}}
                    </v-btn>
                  </v-card-actions>
                </v-container>
              </v-window-item>
            </v-window>
          </v-card-text>
        </v-card>

        <!-- Help Card -->
        <v-card class="mt-6" variant="tonal" color="info">
          <v-card-text>
            <h3 class="text-h6 mb-2">
              <v-icon icon="mdi-information-outline" class="mr-2"></v-icon>
              Import Guide
            </h3>
            <p class="mb-2">
              <strong>Single File:</strong> Import .txt or .md files as a single-chapter book.
            </p>
            <p>
              <strong>Folder:</strong> Import a ZIP file containing metadata.json, index.json, and chapters/ folder.
              See <code>BOOK_IMPORT_GUIDE.md</code> for details.
            </p>
          </v-card-text>
        </v-card>
      </v-container>

      <!-- Success Snackbar -->
      <v-snackbar
        v-model="successSnackbar"
        :timeout="3000"
        color="success"
        location="top"
      >
        <v-icon icon="mdi-check-circle" class="mr-2"></v-icon>
        {{ successMessage }}
        <template v-slot:actions>
          <v-btn variant="text" @click="goToLibrary">View Library</v-btn>
        </template>
      </v-snackbar>

      <!-- Error Snackbar -->
      <v-snackbar
        v-model="errorSnackbar"
        :timeout="5000"
        color="error"
        location="top"
      >
        <v-icon icon="mdi-alert-circle" class="mr-2"></v-icon>
        {{ errorMessage }}
      </v-snackbar>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()
const tab = ref('file')

// File import state
const selectedFile = ref(null)
const isDraggingFile = ref(false)
const fileMetadata = reactive({
  title: '',
  author: '',
  language: 'en',
  tags: [],
  description: ''
})

// Folder import state
const selectedZip = ref(null)
const isDraggingZip = ref(false)
const validationResult = ref(null)
const validating = ref(false)
const folderMetadata = reactive({
  title: '',
  author: '',
  language: 'en',
  tags: [],
  description: ''
})

// Import state
const importing = ref(false)
const successSnackbar = ref(false)
const errorSnackbar = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// Language options
const languageOptions = [
  { title: 'English', value: 'en' },
  { title: 'Chinese (Simplified)', value: 'zh' },
  { title: 'Chinese (Traditional)', value: 'zh-TW' },
  { title: 'Japanese', value: 'ja' },
  { title: 'Korean', value: 'ko' },
  { title: 'Spanish', value: 'es' },
  { title: 'French', value: 'fr' },
  { title: 'German', value: 'de' },
  { title: 'Russian', value: 'ru' },
  { title: 'Arabic', value: 'ar' }
]

// File upload handlers
function handleFileDrop(event) {
  isDraggingFile.value = false
  const files = event.dataTransfer.files
  if (files.length > 0) {
    const file = files[0]
    if (file.name.endsWith('.txt') || file.name.endsWith('.md')) {
      selectedFile.value = file
    } else {
      showError('Please select a .txt or .md file')
    }
  }
}

function handleFileSelect(event) {
  const files = event.target.files
  if (files.length > 0) {
    selectedFile.value = files[0]
  }
}

function resetFileImport() {
  selectedFile.value = null
  fileMetadata.title = ''
  fileMetadata.author = ''
  fileMetadata.language = 'en'
  fileMetadata.tags = []
  fileMetadata.description = ''
}

async function importFile() {
  if (!selectedFile.value) return

  importing.value = true
  try {
    const result = await api.imports.importFile(
      selectedFile.value,
      fileMetadata
    )

    showSuccess(result.message)
    resetFileImport()
  } catch (error) {
    showError(error.response?.data?.detail || 'Failed to import file')
  } finally {
    importing.value = false
  }
}

// ZIP upload handlers
function handleZipDrop(event) {
  isDraggingZip.value = false
  const files = event.dataTransfer.files
  if (files.length > 0) {
    const file = files[0]
    if (file.name.endsWith('.zip')) {
      selectedZip.value = file
      validationResult.value = null
    } else {
      showError('Please select a ZIP file')
    }
  }
}

function handleZipSelect(event) {
  const files = event.target.files
  if (files.length > 0) {
    selectedZip.value = files[0]
    validationResult.value = null
  }
}

function resetZipImport() {
  selectedZip.value = null
  validationResult.value = null
  folderMetadata.title = ''
  folderMetadata.author = ''
  folderMetadata.language = 'en'
  folderMetadata.tags = []
  folderMetadata.description = ''
}

async function validateZip() {
  if (!selectedZip.value) return

  validating.value = true
  try {
    const result = await api.imports.validateFolder(selectedZip.value)
    validationResult.value = result

    // Populate form with detected metadata
    if (result.valid && result.metadata) {
      folderMetadata.title = result.metadata.title || ''
      folderMetadata.author = result.metadata.author || ''
      folderMetadata.language = result.metadata.language || 'en'
      folderMetadata.tags = result.metadata.tags || []
      folderMetadata.description = result.metadata.description || ''
    }
  } catch (error) {
    showError(error.response?.data?.detail || 'Failed to validate ZIP file')
  } finally {
    validating.value = false
  }
}

async function importFolder() {
  if (!selectedZip.value || !validationResult.value?.valid) return

  importing.value = true
  try {
    const result = await api.imports.importFolder(
      selectedZip.value,
      folderMetadata
    )

    showSuccess(result.message)
    resetZipImport()
  } catch (error) {
    showError(error.response?.data?.detail || 'Failed to import folder')
  } finally {
    importing.value = false
  }
}

// Navigation
function goBack() {
  router.push({ name: 'welcome' })
}

function goToLibrary() {
  router.push({ name: 'welcome' })
}

// Notifications
function showSuccess(message) {
  successMessage.value = message
  successSnackbar.value = true
}

function showError(message) {
  errorMessage.value = message
  errorSnackbar.value = true
}
</script>

<style scoped>
.drop-zone {
  border: 2px dashed rgba(var(--v-theme-primary), 0.3);
  transition: all 0.3s ease;
  cursor: pointer;
}

.drop-zone:hover {
  border-color: rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.drop-zone-active {
  border-color: rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.1);
  transform: scale(1.02);
}

code {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.9em;
}
</style>

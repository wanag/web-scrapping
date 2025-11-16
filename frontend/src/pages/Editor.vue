<template>
  <v-container fluid class="pa-0 editor-container">
    <!-- Top App Bar -->
    <v-app-bar color="primary" density="compact" flat>
      <v-btn icon @click="handleBack">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <v-toolbar-title>Edit Content & Metadata</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-chip v-if="editorStore.hasUnsavedChanges" color="warning" size="small" variant="flat">
        <v-icon start>mdi-pencil</v-icon>
        Unsaved Changes
      </v-chip>
    </v-app-bar>

    <!-- Main Content Area -->
    <v-container fluid class="pa-0 content-wrapper">
      <v-row no-gutters class="fill-height">
        <!-- Left Sidebar - Metadata -->
        <v-col cols="12" md="4" lg="3" class="metadata-sidebar">
          <v-card flat class="pa-4 metadata-card">
            <h3 class="mb-4">
              <v-icon class="mr-2">mdi-information</v-icon>
              Metadata
            </h3>

            <v-form>
              <!-- Title -->
              <v-text-field
                v-model="editorStore.editableMetadata.title"
                label="Title"
                variant="outlined"
                density="comfortable"
                @update:model-value="handleMetadataChange"
                prepend-inner-icon="mdi-format-title"
              ></v-text-field>

              <!-- Author -->
              <v-text-field
                v-model="editorStore.editableMetadata.author"
                label="Author"
                variant="outlined"
                density="comfortable"
                @update:model-value="handleMetadataChange"
                prepend-inner-icon="mdi-account"
                class="mt-3"
              ></v-text-field>

              <!-- Language -->
              <v-select
                v-model="editorStore.editableMetadata.language"
                :items="languageOptions"
                label="Language"
                variant="outlined"
                density="comfortable"
                @update:model-value="handleMetadataChange"
                prepend-inner-icon="mdi-translate"
                class="mt-3"
              ></v-select>

              <!-- Description -->
              <v-textarea
                v-model="editorStore.editableMetadata.description"
                label="Description"
                variant="outlined"
                density="comfortable"
                rows="3"
                @update:model-value="handleMetadataChange"
                prepend-inner-icon="mdi-text"
                class="mt-3"
              ></v-textarea>

              <!-- Tags -->
              <v-combobox
                v-model="editorStore.editableMetadata.tags"
                label="Tags"
                variant="outlined"
                density="comfortable"
                chips
                multiple
                @update:model-value="handleMetadataChange"
                prepend-inner-icon="mdi-tag-multiple"
                class="mt-3"
                closable-chips
              ></v-combobox>

              <!-- Source URL (Read-only) -->
              <v-text-field
                :model-value="editorStore.sourceUrl"
                label="Source URL"
                variant="outlined"
                density="comfortable"
                readonly
                prepend-inner-icon="mdi-link"
                class="mt-3"
              ></v-text-field>

              <!-- Content Stats -->
              <v-card variant="tonal" class="mt-4 pa-3">
                <div class="text-caption mb-1">Content Statistics</div>
                <v-list density="compact">
                  <v-list-item density="compact">
                    <v-list-item-title class="text-caption">Characters</v-list-item-title>
                    <v-list-item-subtitle class="text-caption">
                      {{ editorStore.editedContent.length.toLocaleString() }}
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item density="compact">
                    <v-list-item-title class="text-caption">Words (approx)</v-list-item-title>
                    <v-list-item-subtitle class="text-caption">
                      {{ Math.ceil(editorStore.editedContent.length / 5).toLocaleString() }}
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item density="compact">
                    <v-list-item-title class="text-caption">Lines</v-list-item-title>
                    <v-list-item-subtitle class="text-caption">
                      {{ lineCount.toLocaleString() }}
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-card>

              <!-- HTML Containers -->
              <v-card v-if="editorStore.containers.length > 0" variant="tonal" class="mt-4 pa-3">
                <div class="d-flex align-center justify-space-between mb-2">
                  <div class="text-caption">HTML Containers</div>
                  <v-chip size="x-small" variant="flat">
                    {{ editorStore.selectedContainers.length }} / {{ editorStore.containers.length }}
                  </v-chip>
                </div>
                <div class="text-caption text-grey mb-3">
                  Select containers to include in content. Changes refresh automatically.
                </div>
                <div class="d-flex gap-2 mb-3">
                  <v-btn
                    size="x-small"
                    variant="outlined"
                    @click="selectAllContainers"
                    :disabled="refreshing"
                  >
                    All
                  </v-btn>
                  <v-btn
                    size="x-small"
                    variant="outlined"
                    @click="deselectAllContainers"
                    :disabled="refreshing"
                  >
                    None
                  </v-btn>
                </div>

                <v-list density="compact" class="container-list">
                  <v-list-item
                    v-for="(container, index) in editorStore.containers"
                    :key="index"
                    class="pa-1 container-item-editor"
                  >
                    <template v-slot:prepend>
                      <v-checkbox
                        v-model="editorStore.selectedContainers"
                        :value="index"
                        hide-details
                        density="compact"
                        @update:model-value="handleContainerToggle"
                        :disabled="refreshing"
                      ></v-checkbox>
                    </template>

                    <div class="container-info">
                      <div class="text-caption">
                        <code class="container-tag">
                          &lt;{{ container.type }}
                          <span v-if="container.id" class="text-primary"> id="{{ container.id }}"</span>
                          <span v-if="container.classes" class="text-success"> class="{{ container.classes }}"</span>
                          &gt;
                        </code>
                      </div>
                      <div class="text-caption text-grey mt-1">
                        {{ container.content_length.toLocaleString() }} chars
                      </div>
                    </div>
                  </v-list-item>
                </v-list>

                <v-progress-linear
                  v-if="refreshing"
                  indeterminate
                  color="primary"
                  class="mt-2"
                ></v-progress-linear>
              </v-card>
            </v-form>
          </v-card>
        </v-col>

        <!-- Right Main Area - Code Editor -->
        <v-col cols="12" md="8" lg="9" class="editor-column">
          <v-card flat class="fill-height editor-card">
            <v-card-title class="d-flex align-center pa-3 border-b">
              <v-icon class="mr-2">mdi-file-document-edit</v-icon>
              <span>Content Editor (Markdown)</span>
              <v-spacer></v-spacer>
              <v-chip size="small" variant="tonal">
                {{ formatSize(editorStore.editedContent.length) }}
              </v-chip>
            </v-card-title>

            <v-card-text class="pa-0 editor-wrapper">
              <Codemirror
                v-model="editorStore.editedContent"
                :extensions="editorExtensions"
                :style="{ height: editorHeight, width: '100%' }"
                :autofocus="true"
                :indent-with-tab="true"
                :tab-size="2"
                @update:model-value="handleContentChange"
              />
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>

    <!-- Bottom Action Bar -->
    <v-footer app color="surface" class="border-t">
      <v-container>
        <v-row align="center" justify="space-between">
          <v-col cols="auto">
            <v-alert
              v-if="editorStore.hasUnsavedChanges"
              type="info"
              variant="tonal"
              density="compact"
              icon="mdi-information"
              class="mb-0"
            >
              <span class="text-caption">You have unsaved changes</span>
            </v-alert>
          </v-col>
          <v-col cols="auto">
            <v-btn
              variant="text"
              color="error"
              @click="handleDiscard"
              class="mr-2"
            >
              <v-icon start>mdi-delete-outline</v-icon>
              Discard Changes
            </v-btn>
            <v-btn
              variant="outlined"
              color="default"
              @click="handleCancel"
              class="mr-2"
            >
              <v-icon start>mdi-close</v-icon>
              Cancel
            </v-btn>
            <v-btn
              variant="flat"
              color="primary"
              @click="handleSave"
            >
              <v-icon start>mdi-content-save</v-icon>
              Save & Continue
            </v-btn>
          </v-col>
        </v-row>
      </v-container>
    </v-footer>

    <!-- Unsaved Changes Dialog -->
    <v-dialog v-model="showUnsavedDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h6">
          <v-icon color="warning" class="mr-2">mdi-alert</v-icon>
          Unsaved Changes
        </v-card-title>
        <v-card-text>
          You have unsaved changes. Are you sure you want to leave without saving?
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showUnsavedDialog = false">
            Stay
          </v-btn>
          <v-btn variant="text" color="error" @click="confirmLeave">
            Leave Without Saving
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import { useEditorStore } from '@/stores/editor'
import { Codemirror } from 'vue-codemirror'
import { markdown } from '@codemirror/lang-markdown'
import { oneDark } from '@codemirror/theme-one-dark'
import api from '@/services/api'

const router = useRouter()
const theme = useTheme()
const editorStore = useEditorStore()

// State
const showUnsavedDialog = ref(false)
const pendingNavigation = ref(null)
const refreshing = ref(false)

// Language options
const languageOptions = [
  { title: 'English', value: 'en' },
  { title: 'Chinese (Simplified)', value: 'zh-CN' },
  { title: 'Chinese (Traditional)', value: 'zh-TW' },
  { title: 'Japanese', value: 'ja' },
  { title: 'Korean', value: 'ko' },
  { title: 'Spanish', value: 'es' },
  { title: 'French', value: 'fr' },
  { title: 'German', value: 'de' },
  { title: 'Russian', value: 'ru' },
  { title: 'Arabic', value: 'ar' }
]

// Computed
const isDark = computed(() => theme.global.current.value.dark)

const editorExtensions = computed(() => {
  const extensions = [markdown()]
  if (isDark.value) {
    extensions.push(oneDark)
  }
  return extensions
})

const editorHeight = computed(() => {
  // Calculate available height (viewport - app bar - footer - card title)
  return 'calc(100vh - 48px - 80px - 64px)'
})

const lineCount = computed(() => {
  // Count lines in the content (split by newlines)
  if (!editorStore.editedContent) return 0
  return editorStore.editedContent.split('\n').length
})

// Methods
function handleContentChange() {
  editorStore.isContentEdited = true
}

function handleMetadataChange() {
  editorStore.isContentEdited = true
}

function formatSize(charCount) {
  const bytes = charCount * 2 // Rough estimate (UTF-8)
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

function handleSave() {
  // Save changes are already in the store (reactive binding)
  // Just navigate back to scraper with preview dialog
  router.push({ name: 'scraper', query: { fromEditor: 'true' } })
}

function handleDiscard() {
  // Revert all changes to original content and metadata
  editorStore.revertChanges()
  // Stay on editor page - just reset content
}

function handleCancel() {
  if (editorStore.hasUnsavedChanges) {
    showUnsavedDialog.value = true
    pendingNavigation.value = 'scraper'
  } else {
    router.push({ name: 'scraper', query: { fromEditor: 'true' } })
  }
}

function handleBack() {
  if (editorStore.hasUnsavedChanges) {
    showUnsavedDialog.value = true
    pendingNavigation.value = 'scraper'
  } else {
    router.push({ name: 'scraper', query: { fromEditor: 'true' } })
  }
}

function confirmLeave() {
  showUnsavedDialog.value = false
  if (pendingNavigation.value) {
    router.push({ name: pendingNavigation.value, query: { fromEditor: 'true' } })
  }
}

// Container selection functions
function selectAllContainers() {
  if (editorStore.containers.length > 0) {
    editorStore.selectedContainers = editorStore.containers.map((_, index) => index)
    refreshContent()
  }
}

function deselectAllContainers() {
  if (editorStore.selectedContainers.length > 0) {
    editorStore.selectedContainers = []
    refreshContent()
  }
}

async function handleContainerToggle() {
  // Debounce the refresh to avoid multiple calls
  if (refreshing.value) return
  await refreshContent()
}

async function refreshContent() {
  if (!editorStore.sourceUrl || editorStore.selectedContainers.length === 0) return

  refreshing.value = true
  try {
    // Make API call with selected containers
    const response = await api.scraper.previewWithContainers(
      editorStore.sourceUrl,
      'one_page',
      true,
      editorStore.selectedContainers
    )

    if (response.data.success && response.data.full_content) {
      // Update content without marking as edited (since it's a re-extraction)
      editorStore.editedContent = response.data.full_content
      editorStore.originalContent = response.data.full_content
      console.log('Content refreshed with', editorStore.selectedContainers.length, 'containers')
    }
  } catch (err) {
    console.error('Failed to refresh content:', err)
  } finally {
    refreshing.value = false
  }
}

// Lifecycle
onMounted(() => {
  // Data is already loaded from store via reactive binding
  // Navigation guard ensures we have an active session
  console.log('Editor mounted with session:', {
    sourceUrl: editorStore.sourceUrl,
    contentLength: editorStore.editedContent.length,
    firstChars: editorStore.editedContent.substring(0, 100),
    metadata: editorStore.editableMetadata
  })
})
</script>

<style scoped>
.editor-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.content-wrapper {
  flex: 1;
  overflow: hidden;
}

.metadata-sidebar {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  max-height: calc(100vh - 48px - 80px);
  height: calc(100vh - 48px - 80px);
  overflow: hidden; /* Hide overflow on column itself */
  display: flex;
  flex-direction: column;
}

.metadata-card {
  height: 100%;
  overflow-y: scroll !important;
  overflow-x: hidden;
  scrollbar-width: thin; /* For Firefox */
  display: flex;
  flex-direction: column;
}

/* Webkit scrollbar styling for metadata card */
.metadata-card::-webkit-scrollbar {
  width: 12px;
}

.metadata-card::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
}

.metadata-card::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
}

.metadata-card::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.5);
}

/* Dark mode scrollbar for metadata card */
.v-theme--dark .metadata-card::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

.v-theme--dark .metadata-card::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
}

.v-theme--dark .metadata-card::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

.editor-column {
  overflow: hidden;
}

.editor-card {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 48px - 80px); /* Fixed height to prevent auto-expansion */
  max-height: calc(100vh - 48px - 80px);
}

.editor-wrapper {
  position: relative;
  flex: 1; /* Take remaining space */
  overflow: visible; /* Changed from hidden to allow scrollbar */
  max-height: calc(100vh - 48px - 80px - 64px); /* Constrain to force scrolling */
}

.border-b {
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.border-t {
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

/* CodeMirror styling */
:deep(.cm-editor) {
  height: 100%;
  max-height: 100%; /* Prevent expansion beyond container */
  font-size: 14px;
  overflow: hidden; /* Let cm-scroller handle scrolling */
}

:deep(.cm-scroller) {
  font-family: 'Courier New', Courier, monospace;
  line-height: 1.6;
  overflow-y: scroll !important; /* Changed from auto to scroll to force scrollbar */
  overflow-x: auto !important;
  scrollbar-width: thin; /* For Firefox */
  max-height: 100%; /* Constrain scroller to trigger overflow */
  height: 100%;
}

/* Webkit scrollbar styling to ensure visibility */
:deep(.cm-scroller::-webkit-scrollbar) {
  width: 12px;
  height: 12px;
}

:deep(.cm-scroller::-webkit-scrollbar-track) {
  background: rgba(0, 0, 0, 0.1);
}

:deep(.cm-scroller::-webkit-scrollbar-thumb) {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
}

:deep(.cm-scroller::-webkit-scrollbar-thumb:hover) {
  background: rgba(0, 0, 0, 0.5);
}

/* Dark mode scrollbar */
.v-theme--dark :deep(.cm-scroller::-webkit-scrollbar-track) {
  background: rgba(255, 255, 255, 0.1);
}

.v-theme--dark :deep(.cm-scroller::-webkit-scrollbar-thumb) {
  background: rgba(255, 255, 255, 0.3);
}

.v-theme--dark :deep(.cm-scroller::-webkit-scrollbar-thumb:hover) {
  background: rgba(255, 255, 255, 0.5);
}

:deep(.cm-content) {
  padding: 16px;
  /* Removed min-height: 100% to allow proper scrolling when content exceeds container */
}

/* Ensure CodeMirror gutter is visible */
:deep(.cm-gutters) {
  position: sticky;
  left: 0;
  z-index: 1;
}

/* Container selection styling in editor */
.container-list {
  max-height: 300px;
  overflow-y: auto;
  background: transparent;
}

.container-item-editor {
  border-left: 2px solid rgba(var(--v-theme-primary), 0.3);
  margin-bottom: 4px;
  background: rgba(var(--v-theme-surface), 0.5);
}

.container-info {
  flex: 1;
}

.container-tag {
  font-size: 0.7rem;
  font-family: monospace;
}

/* Mobile responsive */
@media (max-width: 960px) {
  .metadata-sidebar {
    max-height: 400px;
    border-right: none;
    border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  }

  .editor-column {
    height: calc(100vh - 48px - 80px - 400px);
  }
}
</style>

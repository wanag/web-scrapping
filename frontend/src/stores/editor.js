import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useEditorStore = defineStore('editor', () => {
  // State - stores current editing session data
  const sourceUrl = ref('')
  const previewData = ref(null)
  const editedContent = ref('')
  const originalContent = ref('') // Store original content for reverting
  const editableMetadata = ref({
    title: '',
    author: '',
    language: 'en',
    description: '',
    tags: []
  })
  const originalMetadata = ref({
    title: '',
    author: '',
    language: 'en',
    description: '',
    tags: []
  }) // Store original metadata for reverting
  const scrapeMode = ref('one_page')
  const isContentEdited = ref(false) // Track if user has made changes

  // Container tracking
  const containers = ref([])
  const selectedContainers = ref([]) // Indices of selected containers

  // Getters
  const hasActiveSession = computed(() => {
    return sourceUrl.value !== '' && previewData.value !== null
  })

  const hasUnsavedChanges = computed(() => {
    return isContentEdited.value
  })

  // Actions
  function setEditorSession(sessionData) {
    sourceUrl.value = sessionData.sourceUrl || ''
    previewData.value = sessionData.previewData || null
    editedContent.value = sessionData.editedContent || ''
    originalContent.value = sessionData.editedContent || '' // Store original for reverting

    const metadata = {
      title: sessionData.editableMetadata?.title || '',
      author: sessionData.editableMetadata?.author || '',
      language: sessionData.editableMetadata?.language || 'en',
      description: sessionData.editableMetadata?.description || '',
      tags: sessionData.editableMetadata?.tags || []
    }
    editableMetadata.value = { ...metadata }
    originalMetadata.value = { ...metadata } // Store original for reverting

    scrapeMode.value = sessionData.scrapeMode || 'one_page'
    isContentEdited.value = false // Reset on new session

    // Set container data
    containers.value = sessionData.containers || []
    selectedContainers.value = sessionData.selectedContainers || []
  }

  function updateEditedContent(content) {
    editedContent.value = content
    isContentEdited.value = true
  }

  function updateMetadata(field, value) {
    if (editableMetadata.value.hasOwnProperty(field)) {
      editableMetadata.value[field] = value
      isContentEdited.value = true
    }
  }

  function revertChanges() {
    // Revert content and metadata to original state
    editedContent.value = originalContent.value
    editableMetadata.value = { ...originalMetadata.value }
    isContentEdited.value = false
  }

  function clearEditorSession() {
    sourceUrl.value = ''
    previewData.value = null
    editedContent.value = ''
    originalContent.value = ''
    editableMetadata.value = {
      title: '',
      author: '',
      language: 'en',
      description: '',
      tags: []
    }
    originalMetadata.value = {
      title: '',
      author: '',
      language: 'en',
      description: '',
      tags: []
    }
    scrapeMode.value = 'one_page'
    isContentEdited.value = false
    containers.value = []
    selectedContainers.value = []
  }

  function getSessionData() {
    return {
      sourceUrl: sourceUrl.value,
      previewData: previewData.value,
      editedContent: editedContent.value,
      editableMetadata: { ...editableMetadata.value },
      scrapeMode: scrapeMode.value,
      isContentEdited: isContentEdited.value,
      containers: containers.value,
      selectedContainers: selectedContainers.value
    }
  }

  return {
    // State
    sourceUrl,
    previewData,
    editedContent,
    originalContent,
    editableMetadata,
    originalMetadata,
    scrapeMode,
    isContentEdited,
    containers,
    selectedContainers,
    // Getters
    hasActiveSession,
    hasUnsavedChanges,
    // Actions
    setEditorSession,
    updateEditedContent,
    updateMetadata,
    revertChanges,
    clearEditorSession,
    getSessionData
  }
})

<template>
  <v-dialog v-model="dialogModel" max-width="600">
    <v-card>
      <v-card-title class="d-flex justify-space-between align-center">
        <span>Chapter Selection</span>
        <v-chip v-if="readChapters.length > 0" color="success" size="small">
          {{ readChapters.length }}/{{ chapters.length }} read
        </v-chip>
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pt-4">
        <!-- Chapter Dropdown Selector -->
        <v-select
          :model-value="currentChapterId"
          :items="chapterItems"
          item-title="displayTitle"
          item-value="id"
          label="Select a chapter"
          variant="outlined"
          density="comfortable"
          @update:model-value="selectChapter"
          hide-details
        >
          <!-- Custom item template with read indicator -->
          <template v-slot:item="{ props, item }">
            <v-list-item
              v-bind="props"
              :class="{
                'bg-primary': item.raw.id === currentChapterId,
                'text-white': item.raw.id === currentChapterId
              }"
            >
              <template v-slot:prepend>
                <v-icon
                  v-if="item.raw.isRead"
                  icon="mdi-check-circle"
                  color="success"
                  size="small"
                  class="mr-2"
                ></v-icon>
                <v-icon
                  v-else
                  icon="mdi-circle-outline"
                  color="grey"
                  size="small"
                  class="mr-2"
                ></v-icon>
              </template>
            </v-list-item>
          </template>

          <!-- Custom selected item template -->
          <template v-slot:selection="{ item }">
            <div class="d-flex align-center">
              <v-icon
                v-if="item.raw.isRead"
                icon="mdi-check-circle"
                color="success"
                size="small"
                class="mr-2"
              ></v-icon>
              <span>{{ item.raw.displayTitle }}</span>
            </div>
          </template>
        </v-select>

        <!-- Chapter List Info -->
        <div class="mt-6">
          <v-divider class="mb-3"></v-divider>
          <div class="text-caption text-grey d-flex align-center">
            <v-icon icon="mdi-information-outline" size="small" class="mr-1"></v-icon>
            Click a chapter to navigate. Completed chapters are marked with
            <v-icon icon="mdi-check-circle" color="success" size="small" class="mx-1"></v-icon>
          </div>
        </div>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="closeDialog">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  chapters: {
    type: Array,
    required: true,
    default: () => []
  },
  currentChapterId: {
    type: Number,
    required: true
  },
  readChapters: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'selectChapter'])

// Two-way binding for dialog visibility
const dialogModel = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Transform chapters for the select component
const chapterItems = computed(() => {
  return props.chapters.map(chapter => ({
    id: chapter.id,
    displayTitle: `${chapter.id + 1}. ${chapter.title}`,
    isRead: props.readChapters.includes(chapter.id)
  }))
})

// Handle chapter selection
const selectChapter = (chapterId) => {
  emit('selectChapter', chapterId)
  closeDialog()
}

// Close dialog
const closeDialog = () => {
  dialogModel.value = false
}

// Keyboard shortcuts
watch(dialogModel, (isOpen) => {
  if (isOpen) {
    // Add keyboard listener for ESC key
    const handleKeydown = (event) => {
      if (event.key === 'Escape') {
        closeDialog()
      }
    }
    window.addEventListener('keydown', handleKeydown)
    return () => window.removeEventListener('keydown', handleKeydown)
  }
})
</script>

<style scoped>
.v-list-item.bg-primary {
  background-color: rgb(var(--v-theme-primary));
}

.v-list-item.text-white .v-list-item-title {
  color: white !important;
}

.v-select :deep(.v-field__input) {
  cursor: pointer;
}
</style>

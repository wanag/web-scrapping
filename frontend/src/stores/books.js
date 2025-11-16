import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useBooksStore = defineStore('books', () => {
  // State
  const books = ref([])
  const currentBook = ref(null)
  const currentChapter = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const sortedBooks = computed(() => {
    return [...books.value].sort((a, b) => {
      return new Date(b.created_at) - new Date(a.created_at)
    })
  })

  const bookById = computed(() => (id) => {
    return books.value.find(book => book.id === id)
  })

  // Actions
  function setBooks(newBooks) {
    books.value = newBooks
  }

  function addBook(book) {
    books.value.push(book)
  }

  function removeBook(bookId) {
    const index = books.value.findIndex(b => b.id === bookId)
    if (index !== -1) {
      books.value.splice(index, 1)
    }
  }

  function setCurrentBook(book) {
    currentBook.value = book
  }

  function setCurrentChapter(chapter) {
    currentChapter.value = chapter
  }

  function setLoading(state) {
    loading.value = state
  }

  function setError(err) {
    error.value = err
  }

  function clearError() {
    error.value = null
  }

  function reset() {
    books.value = []
    currentBook.value = null
    currentChapter.value = null
    loading.value = false
    error.value = null
  }

  return {
    // State
    books,
    currentBook,
    currentChapter,
    loading,
    error,
    // Getters
    sortedBooks,
    bookById,
    // Actions
    setBooks,
    addBook,
    removeBook,
    setCurrentBook,
    setCurrentChapter,
    setLoading,
    setError,
    clearError,
    reset
  }
})

import { ref } from 'vue'

const STORAGE_KEY = 'reading_progress'

/**
 * Composable for managing reading progress in localStorage
 * Tracks the last read chapter for each book
 */
export function useReadingProgress() {
  /**
   * Get all reading progress data from localStorage
   * @returns {Object} Progress data or empty object
   */
  const getAllProgress = () => {
    try {
      const data = localStorage.getItem(STORAGE_KEY)
      return data ? JSON.parse(data) : {}
    } catch (error) {
      console.error('Error reading progress from localStorage:', error)
      return {}
    }
  }

  /**
   * Save all progress data to localStorage
   * @param {Object} progressData - Complete progress data
   */
  const saveAllProgress = (progressData) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(progressData))
    } catch (error) {
      console.error('Error saving progress to localStorage:', error)
    }
  }

  /**
   * Get reading progress for a specific book
   * @param {string} bookId - The book UUID
   * @returns {Object|null} Progress object with {chapterId, lastRead} or null
   */
  const getProgress = (bookId) => {
    if (!bookId) return null

    const allProgress = getAllProgress()
    return allProgress[bookId] || null
  }

  /**
   * Save reading progress for a specific book
   * @param {string} bookId - The book UUID
   * @param {number} chapterId - The chapter index/ID
   */
  const saveProgress = (bookId, chapterId) => {
    if (!bookId || chapterId === null || chapterId === undefined) {
      console.warn('Invalid bookId or chapterId provided to saveProgress')
      return
    }

    const allProgress = getAllProgress()
    allProgress[bookId] = {
      chapterId: chapterId,
      lastRead: new Date().toISOString()
    }
    saveAllProgress(allProgress)
  }

  /**
   * Calculate progress percentage
   * @param {string} bookId - The book UUID
   * @param {number} totalChapters - Total number of chapters in the book
   * @returns {number} Progress percentage (0-100)
   */
  const getProgressPercentage = (bookId, totalChapters) => {
    if (!bookId || !totalChapters || totalChapters === 0) return 0

    const progress = getProgress(bookId)
    if (!progress) return 0

    // Progress is based on last chapter read
    // If read chapter 0, that's 1 chapter complete
    const chaptersRead = progress.chapterId + 1
    const percentage = (chaptersRead / totalChapters) * 100

    // Cap at 100%
    return Math.min(Math.round(percentage), 100)
  }

  /**
   * Clear reading progress for a specific book
   * @param {string} bookId - The book UUID
   */
  const clearProgress = (bookId) => {
    if (!bookId) return

    const allProgress = getAllProgress()
    if (allProgress[bookId]) {
      delete allProgress[bookId]
      saveAllProgress(allProgress)
    }
  }

  /**
   * Clear all reading progress (for debugging/reset)
   */
  const clearAllProgress = () => {
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch (error) {
      console.error('Error clearing all progress:', error)
    }
  }

  /**
   * Check if a book has any reading progress
   * @param {string} bookId - The book UUID
   * @returns {boolean} True if progress exists
   */
  const hasProgress = (bookId) => {
    return getProgress(bookId) !== null
  }

  /**
   * Get formatted last read time (e.g., "2 hours ago")
   * @param {string} bookId - The book UUID
   * @returns {string|null} Formatted time string or null
   */
  const getLastReadTime = (bookId) => {
    const progress = getProgress(bookId)
    if (!progress || !progress.lastRead) return null

    try {
      const lastRead = new Date(progress.lastRead)
      const now = new Date()
      const diffMs = now - lastRead
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMins / 60)
      const diffDays = Math.floor(diffHours / 24)

      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
      if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
      if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`

      return lastRead.toLocaleDateString()
    } catch (error) {
      return null
    }
  }

  return {
    getProgress,
    saveProgress,
    getProgressPercentage,
    clearProgress,
    clearAllProgress,
    hasProgress,
    getLastReadTime,
    getAllProgress
  }
}

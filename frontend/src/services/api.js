import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

// Create axios instance
// Use empty baseURL to use Vite proxy (configured in vite.config.js)
const api = axios.create({
  baseURL: '',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Unauthorized - clear auth and redirect to login
      const authStore = useAuthStore()
      authStore.logout()
    }
    return Promise.reject(error)
  }
)

// API methods
export default {
  // Authentication
  auth: {
    login(pin) {
      return api.post('/api/auth/login', { pin })
    },
    verify(token) {
      return api.post('/api/auth/verify', { token })
    },
    logout() {
      return api.post('/api/auth/logout')
    }
  },

  // Scraper
  scraper: {
    preview(url, mode = 'one_page', includeFullContent = false, chineseMode = false, simplifyMarkdown = false) {
      return api.post('/api/scraper/preview', {
        url,
        mode,
        include_full_content: includeFullContent,
        chinese_mode: chineseMode,
        simplify_markdown: simplifyMarkdown
      })
    },
    previewWithContainers(url, mode = 'one_page', includeFullContent = false, selectedContainers = null, chineseMode = false, simplifyMarkdown = false) {
      return api.post('/api/scraper/preview', {
        url,
        mode,
        include_full_content: includeFullContent,
        selected_containers: selectedContainers,
        chinese_mode: chineseMode,
        simplify_markdown: simplifyMarkdown
      })
    },
    execute(url, mode = 'one_page', metadataOverrides = null, customContent = null, selectedChapters = null, chineseMode = false, simplifyMarkdown = false) {
      return api.post('/api/scraper/execute', {
        url,
        mode,
        metadata_overrides: metadataOverrides,
        custom_content: customContent,
        selected_chapters: selectedChapters,
        chinese_mode: chineseMode,
        simplify_markdown: simplifyMarkdown
      })
    },
    createBook(metadata) {
      return api.post('/api/scraper/create-book', {
        title: metadata.title,
        source_url: metadata.source_url,
        author: metadata.author,
        language: metadata.language,
        tags: metadata.tags || [],
        description: metadata.description,
        scrape_mode: metadata.scrape_mode || 'index_page'
      })
    },
    addChapter(bookId, chapterUrl, chapterIndex, chapterName, customContent = null, selectedContainers = null, chineseMode = false, simplifyMarkdown = false) {
      return api.post('/api/scraper/add-chapter', {
        book_id: bookId,
        chapter_url: chapterUrl,
        chapter_index: chapterIndex,
        chapter_name: chapterName,
        custom_content: customContent,
        selected_containers: selectedContainers,
        chinese_mode: chineseMode,
        simplify_markdown: simplifyMarkdown
      })
    }
  },

  // Books
  books: {
    list() {
      return api.get('/api/books')
    },
    get(bookId) {
      return api.get(`/api/books/${bookId}`)
    },
    getChapter(bookId, chapterId) {
      return api.get(`/api/books/${bookId}/chapters/${chapterId}`)
    },
    delete(bookId) {
      return api.delete(`/api/books/${bookId}`)
    }
  },

  // Import
  imports: {
    async importFile(file, metadata) {
      const formData = new FormData()
      formData.append('file', file)

      if (metadata.title) formData.append('title', metadata.title)
      if (metadata.author) formData.append('author', metadata.author)
      if (metadata.language) formData.append('language', metadata.language)
      if (metadata.description) formData.append('description', metadata.description)
      if (metadata.tags && metadata.tags.length > 0) {
        formData.append('tags', JSON.stringify(metadata.tags))
      }

      return api.post('/api/books/import-file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    },

    async validateFolder(zipFile) {
      const formData = new FormData()
      formData.append('file', zipFile)

      return api.post('/api/books/validate-folder', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    },

    async importFolder(zipFile, metadata) {
      const formData = new FormData()
      formData.append('file', zipFile)

      if (metadata.title) formData.append('title', metadata.title)
      if (metadata.author) formData.append('author', metadata.author)
      if (metadata.language) formData.append('language', metadata.language)
      if (metadata.description) formData.append('description', metadata.description)
      if (metadata.tags && metadata.tags.length > 0) {
        formData.append('tags', JSON.stringify(metadata.tags))
      }

      return api.post('/api/books/import-folder', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    }
  },

  // System
  system: {
    getStats() {
      return api.get('/api/system/stats')
    },
    health() {
      return api.get('/health')
    }
  }
}

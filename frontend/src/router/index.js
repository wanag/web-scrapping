import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useEditorStore } from '@/stores/editor'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/pages/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'welcome',
      component: () => import('@/pages/Welcome.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/scraper',
      name: 'scraper',
      component: () => import('@/pages/Scraper.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/scrape-chapter/:data?',
      name: 'scrape-chapter',
      component: () => import('@/pages/ScrapChapter.vue'),
      meta: { requiresAuth: true },
      props: true
    },
    {
      path: '/editor',
      name: 'editor',
      component: () => import('@/pages/Editor.vue'),
      meta: { requiresAuth: true, requiresEditorSession: true }
    },
    {
      path: '/reader/:bookId',
      name: 'reader',
      component: () => import('@/pages/Reader.vue'),
      meta: { requiresAuth: true },
      props: true
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/'
    }
  ]
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const editorStore = useEditorStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // Redirect to login if not authenticated
    next({ name: 'login' })
  } else if (to.name === 'login' && authStore.isAuthenticated) {
    // Redirect to home if already authenticated
    next({ name: 'welcome' })
  } else if (to.meta.requiresEditorSession && !editorStore.hasActiveSession) {
    // Redirect to scraper if trying to access editor without active session
    next({ name: 'scraper' })
  } else {
    next()
  }
})

export default router

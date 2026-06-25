import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, getMeApi, logoutApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('vehicle_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('vehicle_user') || 'null'))
  const visibleModules = ref(JSON.parse(localStorage.getItem('vehicle_modules') || '[]'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  /** 是否有权看某个模块 code */
  function hasModule(code) {
    return visibleModules.value.some((m) => m.code === code)
  }

  async function login(username, password) {
    const res = await loginApi(username, password)
    token.value = res.data.access_token
    user.value = res.data.user
    visibleModules.value = res.data.visible_modules || []
    localStorage.setItem('vehicle_token', token.value)
    localStorage.setItem('vehicle_user', JSON.stringify(user.value))
    localStorage.setItem('vehicle_modules', JSON.stringify(visibleModules.value))
    return res
  }

  async function fetchMe() {
    if (!token.value) return null
    try {
      const res = await getMeApi()
      user.value = res.data
      visibleModules.value = res.data.visible_modules || []
      localStorage.setItem('vehicle_user', JSON.stringify(user.value))
      localStorage.setItem('vehicle_modules', JSON.stringify(visibleModules.value))
      return res.data
    } catch (e) {
      logout()
      return null
    }
  }

  async function logout() {
    try {
      if (token.value) await logoutApi()
    } catch (e) {}
    token.value = ''
    user.value = null
    visibleModules.value = []
    localStorage.removeItem('vehicle_token')
    localStorage.removeItem('vehicle_user')
    localStorage.removeItem('vehicle_modules')
  }

  return { token, user, visibleModules, isLoggedIn, isAdmin, hasModule, login, fetchMe, logout }
})

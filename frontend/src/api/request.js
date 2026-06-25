import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// 请求拦截器：加 token
request.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (err) => Promise.reject(err)
)

// 响应拦截器：统一处理错误
request.interceptors.response.use(
  (res) => {
    const data = res.data
    if (data && typeof data === 'object' && 'code' in data) {
      if (data.code === 0) return data
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(data)
    }
    return res
  },
  (err) => {
    const status = err.response?.status
    const message = err.response?.data?.message || err.message
    if (status === 401) {
      ElMessage.error('登录已过期')
      const authStore = useAuthStore()
      authStore.logout()
      router.push('/login')
    } else if (status === 403) {
      ElMessage.error(message || '无权限')
    } else {
      ElMessage.error(message || '网络错误')
    }
    return Promise.reject(err)
  }
)

export default request

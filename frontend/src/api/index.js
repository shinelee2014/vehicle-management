import request from './request'

// 用户管理
export * from './users'

// 岗亭
export * from './posts'

// 记录
export * from './records'

// 报告
export * from './reports'

// 认证
export * from './auth'

// 通用
export const listApproversApi = () => request.get('/approvers')

export const uploadPhotoApi = (formData) =>
  request.post('/files/photo', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

export const getDashboardStatsApi = () => request.get('/dashboard/stats')

export const listMessagesApi = (params) => request.get('/messages', { params })

export const unreadCountApi = () => request.get('/messages/unread-count')

export const markReadApi = (id) => request.put(`/messages/${id}/read`)

export const markAllReadApi = () => request.put('/messages/read-all')

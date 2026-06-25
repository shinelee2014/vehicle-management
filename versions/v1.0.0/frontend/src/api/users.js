import request from './request'

export const listUsersApi = (params) => request.get('/users', { params })

export const createUserApi = (data) => request.post('/users', data)

export const updateUserApi = (id, data) => request.put(`/users/${id}`, data)

export const deleteUserApi = (id) => request.delete(`/users/${id}`)

export const resetPasswordApi = (id, data) => request.post(`/users/${id}/reset-password`, data)

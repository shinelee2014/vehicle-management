import request from './request'

export const loginApi = (username, password) =>
  request.post('/auth/login', { username, password })

export const logoutApi = () => request.post('/auth/logout')

export const getMeApi = () => request.get('/auth/me')

export const changePasswordApi = (data) => request.put('/auth/password', data)

// 角色权限
export const getModuleCatalogApi = () => request.get('/role-modules/catalog')
export const listRoleModulesApi = () => request.get('/role-modules')
export const updateRoleModulesApi = (role, modules) =>
  request.put(`/role-modules/${role}`, { modules })

// 自定义模块 CRUD
export const listModulesApi = () => request.get('/modules')
export const createModuleApi = (data) => request.post('/modules', data)
export const updateModuleApi = (id, data) => request.put(`/modules/${id}`, data)
export const deleteModuleApi = (id) => request.delete(`/modules/${id}`)

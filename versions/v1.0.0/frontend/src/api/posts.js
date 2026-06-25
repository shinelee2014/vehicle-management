import request from './request'

export const listPostsApi = () => request.get('/posts')

export const createPostApi = (data) => request.post('/posts', data)

export const updatePostApi = (id, data) => request.put(`/posts/${id}`, data)

export const deletePostApi = (id) => request.delete(`/posts/${id}`)

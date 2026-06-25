import request from './request'

export const listRecordsApi = (params) => request.get('/records', { params })

export const getRecordApi = (id) => request.get(`/records/${id}`)

export const createInApi = (data) => request.post('/records/in', data)

export const createOutApi = (data) => request.post('/records/out', data)

export const pendingApprovalApi = (params) => request.get('/records/pending', { params })

export const approveApi = (id, data) => request.post(`/records/${id}/approve`, data)

export const rejectApi = (id, data) => request.post(`/records/${id}/reject`, data)

export const unbilledListApi = (plate_number) =>
  request.get('/records/unbilled-list', { params: { plate_number } })

export const exportExcelApi = (params) =>
  request.get('/records/export/excel', { params, responseType: 'blob' })

export const batchDeleteRecordsApi = (data) =>
  request.post('/records/batch-delete', data)

export const restoreRecordApi = (id) =>
  request.post(`/records/${id}/restore`)

import request from './request'

export const listVehicleTypesApi = () => request.get('/vehicle-types')
export const listActiveVehicleTypesApi = () => request.get('/vehicle-types/active')
export const createVehicleTypeApi = (data) => request.post('/vehicle-types', data)
export const updateVehicleTypeApi = (id, data) => request.put(`/vehicle-types/${id}`, data)
export const deleteVehicleTypeApi = (id) => request.delete(`/vehicle-types/${id}`)

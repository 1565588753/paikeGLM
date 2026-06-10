import request from './index'

export function getStaffTable(params) {
  return request.get('/staff', { params })
}

export function createStaffEntry(data) {
  return request.post('/staff', data)
}

export function updateStaffEntry(id, data) {
  return request.put(`/staff/${id}`, data)
}

export function deleteStaffEntry(id) {
  return request.delete(`/staff/${id}`)
}

export function batchUpdateStaff(data) {
  return request.put('/staff/batch', data)
}

export function importStaff(data) {
  return request.post('/staff/import', data)
}

export function exportStaff(params) {
  return request.get('/staff/export', { params, responseType: 'blob' })
}

export function syncFromTeaching() {
  return request.post('/staff/sync')
}

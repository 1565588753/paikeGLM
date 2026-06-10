import request from './index'

export function getBackups(params) {
  return request.get('/backups', { params })
}

export function createBackup(data) {
  return request.post('/backups', data)
}

export function restoreBackup(id) {
  return request.post(`/backups/${id}/restore`)
}

export function deleteBackup(id) {
  return request.delete(`/backups/${id}`)
}

export function downloadBackup(id) {
  return request.get(`/backups/${id}/download`, { responseType: 'blob' })
}

export function uploadBackup(data) {
  return request.post('/backups/upload', data, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

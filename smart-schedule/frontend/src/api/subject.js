import request from './index'

export function getSubjects(params) {
  return request.get('/subjects', { params })
}

export function getSubject(id) {
  return request.get(`/subjects/${id}`)
}

export function createSubject(data) {
  return request.post('/subjects', data)
}

export function updateSubject(id, data) {
  return request.put(`/subjects/${id}`, data)
}

export function deleteSubject(id) {
  return request.delete(`/subjects/${id}`)
}

export function importSubjects(data) {
  return request.post('/subjects/import', data)
}

export function exportSubjects(params) {
  return request.get('/subjects/export', { params, responseType: 'blob' })
}

export function getSubjectTemplate() {
  return request.get('/subjects/template', { responseType: 'blob' })
}

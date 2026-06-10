import request from './index'

export function getClasses(params) {
  return request.get('/classes', { params })
}

export function getClass(id) {
  return request.get(`/classes/${id}`)
}

export function createClass(data) {
  return request.post('/classes', data)
}

export function updateClass(id, data) {
  return request.put(`/classes/${id}`, data)
}

export function deleteClass(id) {
  return request.delete(`/classes/${id}`)
}

export function importClasses(data) {
  return request.post('/classes/import', data)
}

export function exportClasses(params) {
  return request.get('/classes/export', { params, responseType: 'blob' })
}

export function getClassesByGrade(grade) {
  return request.get('/classes', { params: { grade } })
}

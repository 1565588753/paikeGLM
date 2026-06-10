import request from './index'

export function getTeachingAssignments(params) {
  return request.get('/teaching-assignments', { params })
}

export function getTeachingAssignment(id) {
  return request.get(`/teaching-assignments/${id}`)
}

export function createTeachingAssignment(data) {
  return request.post('/teaching-assignments', data)
}

export function updateTeachingAssignment(id, data) {
  return request.put(`/teaching-assignments/${id}`, data)
}

export function deleteTeachingAssignment(id) {
  return request.delete(`/teaching-assignments/${id}`)
}

export function batchCreateTeachingAssignments(data) {
  return request.post('/teaching-assignments/batch', data)
}

export function importTeachingAssignments(data) {
  return request.post('/teaching-assignments/import', data)
}

export function exportTeachingAssignments(params) {
  return request.get('/teaching-assignments/export', { params, responseType: 'blob' })
}

export function getTeacherWorkload(teacherId, params) {
  return request.get(`/teaching-assignments/teacher/${teacherId}/workload`, { params })
}

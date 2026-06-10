import request from './index'

export function getClassrooms(params) {
  return request.get('/classrooms', { params })
}

export function getClassroom(id) {
  return request.get(`/classrooms/${id}`)
}

export function createClassroom(data) {
  return request.post('/classrooms', data)
}

export function updateClassroom(id, data) {
  return request.put(`/classrooms/${id}`, data)
}

export function deleteClassroom(id) {
  return request.delete(`/classrooms/${id}`)
}

export function getClassroomTypes() {
  return request.get('/classrooms/types')
}

export function importClassrooms(data) {
  return request.post('/classrooms/import', data)
}

export function exportClassrooms(params) {
  return request.get('/classrooms/export', { params, responseType: 'blob' })
}

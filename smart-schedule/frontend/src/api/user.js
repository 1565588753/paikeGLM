import request from './index'

export function getUsers(params) {
  return request.get('/users', { params })
}

export function getUser(id) {
  return request.get(`/users/${id}`)
}

export function createUser(data) {
  return request.post('/users', data)
}

export function updateUser(id, data) {
  return request.put(`/users/${id}`, data)
}

export function deleteUser(id) {
  return request.delete(`/users/${id}`)
}

export function resetPassword(id) {
  return request.put(`/users/${id}/reset-password`)
}

export function importUsers(data) {
  return request.post('/users/import', data)
}

export function exportUsers(params) {
  return request.get('/users/export', { params, responseType: 'blob' })
}

import request from './index'

export function login(data) {
  return request.post('/auth/login', data)
}

export function getUserInfo() {
  return request.get('/auth/userinfo')
}

export function changePassword(data) {
  return request.put('/auth/password', data)
}

export function logout() {
  return request.post('/auth/logout')
}

import request from './index'

export function createSwapRequest(data) {
  return request.post('/swaps', data)
}

export function getSwapRequests(params) {
  return request.get('/swaps', { params })
}

export function getSwapRequest(id) {
  return request.get(`/swaps/${id}`)
}

export function approveSwap(id, data) {
  return request.put(`/swaps/${id}/approve`, data)
}

export function rejectSwap(id, data) {
  return request.put(`/swaps/${id}/reject`, data)
}

export function cancelSwap(id) {
  return request.put(`/swaps/${id}/cancel`)
}

export function getSwapHistory(params) {
  return request.get('/swaps/history', { params })
}

export function checkSwapConflict(data) {
  return request.post('/swaps/check-conflict', data)
}

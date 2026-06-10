import request from './index'

export function getNotifications(params) {
  return request.get('/notifications', { params })
}

export function getNotification(id) {
  return request.get(`/notifications/${id}`)
}

export function markAsRead(id) {
  return request.put(`/notifications/${id}/read`)
}

export function markAllAsRead() {
  return request.put('/notifications/read-all')
}

export function deleteNotification(id) {
  return request.delete(`/notifications/${id}`)
}

export function getUnreadCount() {
  return request.get('/notifications/unread-count')
}

import request from './index'

export function exportTimetable(params) {
  return request.get('/export/timetable', { params, responseType: 'blob' })
}

export function exportAllTimetables(params) {
  return request.get('/export/all-timetables', { params, responseType: 'blob' })
}

export function exportTeacherTimetable(params) {
  return request.get('/export/teacher-timetable', { params, responseType: 'blob' })
}

export function importTimetable(data) {
  return request.post('/import/timetable', data)
}

export function getOperationLogs(params) {
  return request.get('/logs', { params })
}

export function clearLogs(beforeDate) {
  return request.delete('/logs', { params: { beforeDate } })
}

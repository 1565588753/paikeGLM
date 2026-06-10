import request from './index'

export function getClassTimetable(classId, params) {
  return request.get(`/timetable/class/${classId}`, { params })
}

export function getTeacherTimetable(teacherId, params) {
  return request.get(`/timetable/teacher/${teacherId}`, { params })
}

export function getRoomTimetable(roomId, params) {
  return request.get(`/timetable/room/${roomId}`, { params })
}

export function getAllClassTimetables(params) {
  return request.get('/timetable/all-classes', { params })
}

export function updateTimetableCell(data) {
  return request.put('/timetable/cell', data)
}

export function deleteTimetableCell(id) {
  return request.delete(`/timetable/cell/${id}`)
}

export function checkConflict(data) {
  return request.post('/timetable/check-conflict', data)
}

export function batchCheckConflict(data) {
  return request.post('/timetable/batch-check-conflict', data)
}

export function startAutoSchedule(data) {
  return request.post('/timetable/auto-schedule', data)
}

export function getAutoScheduleStatus(taskId) {
  return request.get(`/timetable/auto-schedule/status/${taskId}`)
}

export function cancelAutoSchedule(taskId) {
  return request.post(`/timetable/auto-schedule/cancel/${taskId}`)
}

export function pauseAutoSchedule(taskId) {
  return request.post(`/timetable/auto-schedule/pause/${taskId}`)
}

export function resumeAutoSchedule(taskId) {
  return request.post(`/timetable/auto-schedule/resume/${taskId}`)
}

export function dragScheduleCell(data) {
  return request.put('/timetable/drag', data)
}

export function getUnscheduledCourses(params) {
  return request.get('/timetable/unscheduled', { params })
}

export function lockTimetableCell(id) {
  return request.put(`/timetable/cell/${id}/lock`)
}

export function unlockTimetableCell(id) {
  return request.put(`/timetable/cell/${id}/unlock`)
}

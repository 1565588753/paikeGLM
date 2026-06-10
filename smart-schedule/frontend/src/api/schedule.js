import request from './index'

export function getScheduleTemplates(params) {
  return request.get('/schedule-templates', { params })
}

export function getScheduleTemplate(id) {
  return request.get(`/schedule-templates/${id}`)
}

export function createScheduleTemplate(data) {
  return request.post('/schedule-templates', data)
}

export function updateScheduleTemplate(id, data) {
  return request.put(`/schedule-templates/${id}`, data)
}

export function deleteScheduleTemplate(id) {
  return request.delete(`/schedule-templates/${id}`)
}

export function getTimeSlots(templateId) {
  return request.get(`/schedule-templates/${templateId}/timeslots`)
}

export function updateTimeSlots(templateId, data) {
  return request.put(`/schedule-templates/${templateId}/timeslots`, data)
}

export function addTimeSlot(templateId, data) {
  return request.post(`/schedule-templates/${templateId}/timeslots`, data)
}

export function deleteTimeSlot(templateId, slotId) {
  return request.delete(`/schedule-templates/${templateId}/timeslots/${slotId}`)
}

export function copyTemplateToGrades(templateId, data) {
  return request.post(`/schedule-templates/${templateId}/copy`, data)
}

export function setDefaultTemplate(templateId) {
  return request.put(`/schedule-templates/${templateId}/default`)
}

import request from './index'

export function getAcademicYears(params) {
  return request.get('/academic-years', { params })
}

export function getAcademicYear(id) {
  return request.get(`/academic-years/${id}`)
}

export function createAcademicYear(data) {
  return request.post('/academic-years', data)
}

export function updateAcademicYear(id, data) {
  return request.put(`/academic-years/${id}`, data)
}

export function deleteAcademicYear(id) {
  return request.delete(`/academic-years/${id}`)
}

export function getCurrentYear() {
  return request.get('/academic-years/current')
}

export function switchYear(id) {
  return request.post(`/academic-years/${id}/switch`)
}

export function getSemesters(yearId) {
  return request.get(`/academic-years/${yearId}/semesters`)
}

export function createSemester(yearId, data) {
  return request.post(`/academic-years/${yearId}/semesters`, data)
}

export function updateSemester(yearId, semesterId, data) {
  return request.put(`/academic-years/${yearId}/semesters/${semesterId}`, data)
}

export function deleteSemester(yearId, semesterId) {
  return request.delete(`/academic-years/${yearId}/semesters/${semesterId}`)
}

export function switchSemester(semesterId) {
  return request.post(`/semesters/${semesterId}/switch`)
}

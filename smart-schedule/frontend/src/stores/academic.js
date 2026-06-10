import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAcademicYears, getCurrentYear } from '../api/academic'

export const useAcademicStore = defineStore('academic', () => {
  const currentYear = ref(null)
  const currentSemester = ref(null)
  const academicYears = ref([])

  const yearLabel = computed(() => {
    if (!currentYear.value) return ''
    return currentYear.value.name || ''
  })

  const semesterLabel = computed(() => {
    if (!currentSemester.value) return ''
    return currentSemester.value.name || ''
  })

  const fullLabel = computed(() => {
    return `${yearLabel.value} ${semesterLabel.value}`
  })

  async function fetchCurrentYear() {
    try {
      const res = await getCurrentYear()
      currentYear.value = res.data.year
      currentSemester.value = res.data.semester
    } catch (e) {
      console.error('获取当前学年失败', e)
    }
  }

  async function fetchAcademicYears() {
    try {
      const res = await getAcademicYears()
      academicYears.value = res.data
    } catch (e) {
      console.error('获取学年列表失败', e)
    }
  }

  function setCurrentYear(year, semester) {
    currentYear.value = year
    currentSemester.value = semester
  }

  return {
    currentYear,
    currentSemester,
    academicYears,
    yearLabel,
    semesterLabel,
    fullLabel,
    fetchCurrentYear,
    fetchAcademicYears,
    setCurrentYear
  }
})

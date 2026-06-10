<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">教师课表</h2>
      <div class="no-print">
        <el-button @click="handlePrint"><el-icon><Printer /></el-icon>打印</el-button>
        <el-button @click="handleExport"><el-icon><Download /></el-icon>导出</el-button>
      </div>
    </div>

    <div class="search-bar no-print">
      <el-select v-model="selectedTeacherId" placeholder="选择教师" filterable @change="loadTimetable" style="width: 200px;">
        <el-option v-for="t in teacherOptions" :key="t.id" :label="t.name || t.username" :value="t.id" />
      </el-select>
      <el-radio-group v-model="weekFilter" @change="filterTimetable">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="odd">单周</el-radio-button>
        <el-radio-button value="even">双周</el-radio-button>
      </el-radio-group>
    </div>

    <div v-if="selectedTeacherId" class="teacher-timetable-wrapper">
      <div class="unified-timeline">
        <div class="timeline-header">
          <div class="timeline-time-col">时间</div>
          <div v-for="day in days" :key="day.index" class="timeline-day-col">{{ day.label }}</div>
        </div>

        <div class="timeline-body">
          <template v-for="timeSlot in unifiedTimeSlots" :key="timeSlot.time">
            <div class="timeline-row">
              <div class="timeline-time-cell">
                <span class="time-text">{{ timeSlot.time }}</span>
              </div>
              <div v-for="day in days" :key="day.index" class="timeline-day-cell">
                <template v-if="getCoursesAtTime(day.index, timeSlot.time).length > 0">
                  <div
                    v-for="course in getCoursesAtTime(day.index, timeSlot.time)"
                    :key="course.id"
                    class="course-block"
                    :style="getCourseStyle(course)"
                  >
                    <span
                      v-if="course.weekType && course.weekType !== 'all'"
                      class="week-badge"
                      :class="course.weekType === 'odd' ? 'week-badge-odd' : 'week-badge-even'"
                    >
                      {{ course.weekType === 'odd' ? '单' : '双' }}
                    </span>
                    <div class="course-subject">{{ course.subjectName }}</div>
                    <div class="course-class">{{ course.className }}</div>
                    <div class="course-grade">
                      <el-tag size="small" :type="getGradeTagType(course.grade)">{{ course.grade }}年级</el-tag>
                    </div>
                    <div class="course-room">{{ course.classroomName }}</div>
                    <div class="course-time">{{ course.startTime }}-{{ course.endTime }}</div>
                  </div>
                </template>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <el-empty v-else description="请选择教师查看课表" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getTeacherTimetable } from '../../api/timetable'
import { getUsers } from '../../api/user'
import { getSubjectColorByName } from '../../utils/format'
import { ElMessage } from 'element-plus'

const selectedTeacherId = ref('')
const weekFilter = ref('all')
const timetableData = ref([])
const filteredData = ref([])
const teacherOptions = ref([])

const days = [
  { index: 1, label: '周一' }, { index: 2, label: '周二' }, { index: 3, label: '周三' },
  { index: 4, label: '周四' }, { index: 5, label: '周五' }, { index: 6, label: '周六' }, { index: 7, label: '周日' }
]

const unifiedTimeSlots = computed(() => {
  const timeSet = new Set()
  filteredData.value.forEach(c => {
    if (c.startTime) timeSet.add(c.startTime)
    if (c.endTime) timeSet.add(c.endTime)
  })
  const times = Array.from(timeSet).sort()
  if (times.length === 0) {
    const defaultTimes = ['08:00', '08:45', '09:00', '09:45', '10:00', '10:45', '14:00', '14:45', '15:00', '15:45', '16:00', '16:45']
    return defaultTimes.map(t => ({ time: t }))
  }
  return times.map(t => ({ time: t }))
})

function getCoursesAtTime(dayIndex, time) {
  return filteredData.value.filter(c =>
    c.dayOfWeek === dayIndex &&
    c.startTime <= time && c.endTime > time
  )
}

function getCourseStyle(course) {
  const color = getSubjectColorByName(course.subjectName)
  return {
    background: `linear-gradient(135deg, ${color}20, ${color}10)`,
    borderLeft: `4px solid ${color}`,
    borderTop: course.startTime === unifiedTimeSlots.value.find(t => t.time >= course.startTime)?.time ? `2px solid ${color}` : 'none'
  }
}

function getGradeTagType(grade) {
  const types = ['primary', 'success', 'warning', 'danger', 'info', '']
  return types[(grade - 1) % types.length] || ''
}

function filterTimetable() {
  if (weekFilter.value === 'all') {
    filteredData.value = [...timetableData.value]
  } else {
    filteredData.value = timetableData.value.filter(c =>
      c.weekType === weekFilter.value || c.weekType === 'all'
    )
  }
}

async function loadTimetable() {
  if (!selectedTeacherId.value) return
  try {
    const res = await getTeacherTimetable(selectedTeacherId.value)
    timetableData.value = res.data || []
    filterTimetable()
  } catch (e) { console.error('加载教师课表失败', e) }
}

async function loadTeacherOptions() {
  try {
    const res = await getUsers({ pageSize: 999, role: 'teacher' })
    teacherOptions.value = res.data?.list || res.data || []
  } catch (e) { console.error('加载教师列表失败', e) }
}

function handlePrint() { window.print() }

function handleExport() {
  ElMessage.success('导出功能已触发')
  window.print()
}

onMounted(() => { loadTeacherOptions() })
</script>

<style scoped>
.teacher-timetable-wrapper { overflow-x: auto; }

.unified-timeline {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  min-width: 900px;
}

.timeline-header {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  background: #f5f7fa;
  border-bottom: 2px solid #ebeef5;
}

.timeline-time-col,
.timeline-day-col {
  padding: 12px 8px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.timeline-body {
  position: relative;
}

.timeline-row {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  border-bottom: 1px solid #f0f2f5;
  min-height: 40px;
}

.timeline-time-cell {
  padding: 8px 4px;
  text-align: center;
  background: #fafafa;
  border-right: 1px solid #f0f2f5;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.time-text {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}

.timeline-day-cell {
  padding: 4px;
  border-right: 1px solid #f0f2f5;
  min-height: 40px;
  position: relative;
}

.course-block {
  padding: 6px 8px;
  border-radius: 6px;
  margin: 2px 0;
  position: relative;
  transition: transform 0.15s;
}

.course-block:hover {
  transform: scale(1.02);
  z-index: 1;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.course-subject {
  font-size: 13px;
  font-weight: 700;
  color: #303133;
}

.course-class {
  font-size: 12px;
  color: #606266;
  margin-top: 2px;
}

.course-grade {
  margin-top: 2px;
}

.course-room {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.course-time {
  font-size: 10px;
  color: #c0c4cc;
  margin-top: 1px;
}

.week-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  font-size: 10px;
  padding: 0 4px;
  border-radius: 2px;
  line-height: 16px;
}

.week-badge-odd { background: #e6f7ff; color: #1890ff; }
.week-badge-even { background: #fff7e6; color: #fa8c16; }

@media (max-width: 768px) {
  .unified-timeline { min-width: auto; }
}
</style>

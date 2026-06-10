<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">班级课表</h2>
      <div class="no-print">
        <el-button @click="handlePrint"><el-icon><Printer /></el-icon>打印</el-button>
        <el-button @click="handleExport"><el-icon><Download /></el-icon>导出</el-button>
      </div>
    </div>

    <div class="search-bar no-print">
      <el-select v-model="selectedClassId" placeholder="选择班级" filterable @change="loadTimetable" style="width: 200px;">
        <el-option v-for="c in classOptions" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-radio-group v-model="weekFilter" @change="filterTimetable">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="odd">单周</el-radio-button>
        <el-radio-button value="even">双周</el-radio-button>
      </el-radio-group>
    </div>

    <div v-if="selectedClassId" class="timetable-wrapper">
      <div class="timetable-grid" :style="gridStyle">
        <div class="timetable-header"></div>
        <div v-for="day in days" :key="day.index" class="timetable-header">
          {{ day.label }}
        </div>

        <template v-for="(period, pIdx) in periods" :key="pIdx">
          <div class="timetable-period">
            <span class="period-index">{{ period.label || `第${pIdx + 1}节` }}</span>
            <span class="period-time">{{ period.startTime }}-{{ period.endTime }}</span>
          </div>
          <div
            v-for="day in days"
            :key="`${pIdx}-${day.index}`"
            class="timetable-cell"
            :style="getCellStyle(pIdx, day.index)"
          >
            <template v-if="getCellData(pIdx, day.index)">
              <span
                v-if="getCellData(pIdx, day.index).weekType && getCellData(pIdx, day.index).weekType !== 'all'"
                class="week-badge"
                :class="getCellData(pIdx, day.index).weekType === 'odd' ? 'week-badge-odd' : 'week-badge-even'"
              >
                {{ getCellData(pIdx, day.index).weekType === 'odd' ? '单' : '双' }}
              </span>
              <span class="subject-name">{{ getCellData(pIdx, day.index).subjectName }}</span>
              <span class="teacher-name">{{ getCellData(pIdx, day.index).teacherName }}</span>
              <span class="classroom-name">{{ getCellData(pIdx, day.index).classroomName }}</span>
            </template>
          </div>
        </template>
      </div>
    </div>

    <el-empty v-else description="请选择班级查看课表" />

    <div class="mobile-day-view" v-if="isMobile && selectedClassId">
      <el-select v-model="mobileDay" style="margin-bottom: 16px; width: 100%;">
        <el-option v-for="day in days" :key="day.index" :label="day.label" :value="day.index" />
      </el-select>
      <div class="mobile-schedule-list">
        <div v-for="period in periods" :key="period.index" class="mobile-schedule-item">
          <div class="mobile-time">{{ period.startTime }}-{{ period.endTime }}</div>
          <div class="mobile-info" v-if="getCellData(period.index - 1, mobileDay)" :style="{ borderLeftColor: getSubjectColorByName(getCellData(period.index - 1, mobileDay).subjectName) }">
            <div class="mobile-subject">{{ getCellData(period.index - 1, mobileDay).subjectName }}</div>
            <div class="mobile-detail">{{ getCellData(period.index - 1, mobileDay).teacherName }} · {{ getCellData(period.index - 1, mobileDay).classroomName }}</div>
          </div>
          <div class="mobile-info empty" v-else>
            <div class="mobile-subject" style="color: #c0c4cc;">无课程</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getClassTimetable } from '../../api/timetable'
import { getClasses } from '../../api/class'
import { getSubjectColorByName } from '../../utils/format'
import { exportTimetableToExcel } from '../../utils/excel'
import { ElMessage } from 'element-plus'

const selectedClassId = ref('')
const weekFilter = ref('all')
const timetableData = ref([])
const filteredData = ref([])
const periods = ref([])
const classOptions = ref([])
const mobileDay = ref(1)
const isMobile = ref(false)

const days = [
  { index: 1, label: '周一' }, { index: 2, label: '周二' }, { index: 3, label: '周三' },
  { index: 4, label: '周四' }, { index: 5, label: '周五' }, { index: 6, label: '周六' }, { index: 7, label: '周日' }
]

const gridStyle = computed(() => ({
  gridTemplateColumns: `80px repeat(${days.length}, 1fr)`,
  gridTemplateRows: `40px repeat(${periods.value.length}, minmax(60px, auto))`
}))

function getCellData(periodIdx, dayIdx) {
  return filteredData.value.find(c => c.periodIndex === periodIdx + 1 && c.dayOfWeek === dayIdx)
}

function getCellStyle(periodIdx, dayIdx) {
  const cell = getCellData(periodIdx, dayIdx)
  if (cell) {
    const color = getSubjectColorByName(cell.subjectName)
    return { background: color + '15', borderLeft: `3px solid ${color}` }
  }
  return {}
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
  if (!selectedClassId.value) return
  try {
    const res = await getClassTimetable(selectedClassId.value)
    timetableData.value = res.data?.cells || res.data || []
    periods.value = res.data?.periods || generateDefaultPeriods()
    filterTimetable()
  } catch (e) { console.error('加载课表失败', e) }
}

function generateDefaultPeriods() {
  return Array.from({ length: 8 }, (_, i) => ({
    index: i + 1,
    label: `第${i + 1}节`,
    startTime: '',
    endTime: ''
  }))
}

async function loadClassOptions() {
  try {
    const res = await getClasses({ pageSize: 999 })
    classOptions.value = res.data?.list || res.data || []
  } catch (e) { console.error('加载班级列表失败', e) }
}

function handlePrint() { window.print() }

function handleExport() {
  const dayLabels = days.map(d => d.label)
  exportTimetableToExcel(filteredData.value, dayLabels, periods.value, '班级课表')
  ElMessage.success('导出成功')
}

function checkMobile() { isMobile.value = window.innerWidth <= 768 }

onMounted(() => {
  loadClassOptions()
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => { window.removeEventListener('resize', checkMobile) })
</script>

<style scoped>
.timetable-wrapper { overflow-x: auto; }
.timetable-grid {
  display: grid;
  gap: 2px;
  background: #ebeef5;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  min-width: 700px;
}
.timetable-header {
  background: #f5f7fa;
  padding: 10px 8px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
.timetable-period {
  background: #f5f7fa;
  padding: 8px 6px;
  text-align: center;
  font-size: 12px;
  color: #606266;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
.period-index { font-weight: 600; font-size: 13px; }
.period-time { font-size: 10px; color: #909399; margin-top: 2px; }
.timetable-cell {
  background: #fff;
  padding: 6px;
  min-height: 60px;
  cursor: default;
  transition: background 0.2s;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
}
.timetable-cell:hover { filter: brightness(0.97); }
.subject-name { font-size: 13px; font-weight: 600; color: #303133; }
.teacher-name { font-size: 11px; color: #909399; margin-top: 2px; }
.classroom-name { font-size: 11px; color: #c0c4cc; margin-top: 1px; }
.week-badge {
  position: absolute; top: 2px; right: 2px;
  font-size: 10px; padding: 0 4px; border-radius: 2px; line-height: 16px;
}
.week-badge-odd { background: #e6f7ff; color: #1890ff; }
.week-badge-even { background: #fff7e6; color: #fa8c16; }

.mobile-day-view { display: none; }
@media (max-width: 768px) {
  .timetable-wrapper { display: none; }
  .mobile-day-view { display: block; }
}
.mobile-schedule-item { display: flex; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f0f2f5; }
.mobile-time { min-width: 80px; font-size: 13px; color: #909399; display: flex; align-items: center; }
.mobile-info { flex: 1; padding: 8px 12px; border-left: 3px solid #409EFF; border-radius: 0 6px 6px 0; background: #fafafa; }
.mobile-info.empty { border-left-color: #e4e7ed; }
.mobile-subject { font-size: 14px; font-weight: 600; color: #303133; }
.mobile-detail { font-size: 12px; color: #909399; margin-top: 4px; }
</style>

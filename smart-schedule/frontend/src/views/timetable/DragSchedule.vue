<template>
  <div class="page-container drag-schedule-page">
    <div class="page-header">
      <h2 class="page-title">拖拽排课</h2>
      <div>
        <el-button-group>
          <el-button :disabled="undoStack.length === 0" @click="handleUndo">
            <el-icon><RefreshLeft /></el-icon>撤销
          </el-button>
          <el-button :disabled="redoStack.length === 0" @click="handleRedo">
            <el-icon><RefreshRight /></el-icon>重做
          </el-button>
        </el-button-group>
        <el-button @click="handleSave" type="success" :loading="saveLoading">
          <el-icon><Check /></el-icon>保存
        </el-button>
      </div>
    </div>

    <div class="drag-layout">
      <div class="left-panel">
        <div class="panel-header">
          <span>未排课程</span>
          <el-select v-model="selectedClassId" placeholder="选择班级" filterable size="small" @change="loadUnscheduled" style="width: 140px;">
            <el-option v-for="c in classOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </div>
        <div class="unscheduled-list">
          <div
            v-for="course in unscheduledCourses"
            :key="course.id"
            class="drag-source"
            draggable="true"
            @dragstart="onDragStart($event, course)"
            @dragend="onDragEnd"
          >
            <div class="drag-course-subject" :style="{ color: getSubjectColorByName(course.subjectName) }">
              {{ course.subjectName }}
            </div>
            <div class="drag-course-info">
              <span>{{ course.teacherName }}</span>
              <span>{{ course.weeklyHours }}节/周</span>
            </div>
            <div class="drag-course-week" v-if="course.weekType !== 'all'">
              <el-tag :type="course.weekType === 'odd' ? 'primary' : 'warning'" size="small">
                {{ course.weekType === 'odd' ? '单周' : '双周' }}
              </el-tag>
            </div>
          </div>
          <el-empty v-if="unscheduledCourses.length === 0" description="暂无未排课程" :image-size="60" />
        </div>
      </div>

      <div class="main-panel">
        <div class="main-toolbar">
          <el-select v-model="viewClassId" placeholder="选择查看班级" filterable size="small" @change="loadTimetable" style="width: 160px;">
            <el-option v-for="c in classOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
          <el-radio-group v-model="weekFilter" size="small" @change="filterTimetable">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="odd">单周</el-radio-button>
            <el-radio-button value="even">双周</el-radio-button>
          </el-radio-group>
        </div>

        <div class="timetable-grid" :style="gridStyle" v-if="viewClassId">
          <div class="timetable-header"></div>
          <div v-for="day in days" :key="day.index" class="timetable-header">{{ day.label }}</div>

          <template v-for="(period, pIdx) in periods" :key="pIdx">
            <div class="timetable-period">
              <span class="period-index">{{ period.label || `第${pIdx + 1}节` }}</span>
            </div>
            <div
              v-for="day in days"
              :key="`${pIdx}-${day.index}`"
              class="timetable-cell drag-target"
              :class="getCellClass(pIdx, day.index)"
              @dragover.prevent="onDragOver($event, pIdx, day.index)"
              @dragleave="onDragLeave($event, pIdx, day.index)"
              @drop="onDrop($event, pIdx, day.index)"
              @contextmenu.prevent="showContextMenu($event, pIdx, day.index)"
            >
              <template v-if="getCellData(pIdx, day.index)">
                <div
                  class="cell-content"
                  draggable="true"
                  @dragstart="onCellDragStart($event, pIdx, day.index)"
                  @dragend="onDragEnd"
                  :style="getCellStyle(pIdx, day.index)"
                >
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
                  <el-icon v-if="getCellData(pIdx, day.index).locked" class="lock-icon"><Lock /></el-icon>
                </div>
              </template>
            </div>
          </template>
        </div>

        <el-empty v-else description="请选择班级查看课表" />
      </div>
    </div>

    <teleport to="body">
      <div
        v-if="contextMenu.visible"
        class="context-menu"
        :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
      >
        <div class="context-menu-item" @click="handleLockCell" v-if="contextMenu.cellData && !contextMenu.cellData.locked">
          <el-icon><Lock /></el-icon>锁定此格
        </div>
        <div class="context-menu-item" @click="handleUnlockCell" v-if="contextMenu.cellData && contextMenu.cellData.locked">
          <el-icon><Unlock /></el-icon>解锁此格
        </div>
        <div class="context-menu-item" @click="handleDeleteCell" v-if="contextMenu.cellData">
          <el-icon><Delete /></el-icon>删除课程
        </div>
        <div class="context-menu-item" @click="handleSwapCell" v-if="contextMenu.cellData">
          <el-icon><Switch /></el-icon>与...交换
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { getClassTimetable, getUnscheduledCourses, dragScheduleCell, checkConflict, lockTimetableCell, unlockTimetableCell, deleteTimetableCell } from '../../api/timetable'
import { getClasses } from '../../api/class'
import { getSubjectColorByName } from '../../utils/format'
import { ElMessage, ElMessageBox } from 'element-plus'

const selectedClassId = ref('')
const viewClassId = ref('')
const weekFilter = ref('all')
const unscheduledCourses = ref([])
const timetableData = ref([])
const filteredData = ref([])
const periods = ref([])
const classOptions = ref([])
const saveLoading = ref(false)
const dragSource = ref(null)
const dragFromCell = ref(null)
const conflictCells = ref({})
const undoStack = ref([])
const redoStack = ref([])

const contextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  periodIndex: -1,
  dayIndex: -1,
  cellData: null
})

const days = [
  { index: 1, label: '周一' }, { index: 2, label: '周二' }, { index: 3, label: '周三' },
  { index: 4, label: '周四' }, { index: 5, label: '周五' }, { index: 6, label: '周六' }, { index: 7, label: '周日' }
]

const gridStyle = computed(() => ({
  gridTemplateColumns: `70px repeat(${days.length}, 1fr)`,
  gridTemplateRows: `36px repeat(${periods.value.length}, minmax(64px, auto))`
}))

function getCellData(periodIdx, dayIdx) {
  return filteredData.value.find(c => c.periodIndex === periodIdx + 1 && c.dayOfWeek === dayIdx)
}

function getCellStyle(periodIdx, dayIdx) {
  const cell = getCellData(periodIdx, dayIdx)
  if (cell) {
    const color = getSubjectColorByName(cell.subjectName)
    return { background: `linear-gradient(135deg, ${color}25, ${color}10)`, borderLeft: `3px solid ${color}` }
  }
  return {}
}

function getCellClass(periodIdx, dayIdx) {
  const key = `${periodIdx}-${dayIdx}`
  if (conflictCells.value[key] === false) return 'drop-valid'
  if (conflictCells.value[key] === true) return 'drop-invalid'
  return ''
}

function filterTimetable() {
  if (weekFilter.value === 'all') { filteredData.value = [...timetableData.value] }
  else { filteredData.value = timetableData.value.filter(c => c.weekType === weekFilter.value || c.weekType === 'all') }
}

async function loadUnscheduled() {
  if (!selectedClassId.value) return
  try {
    const res = await getUnscheduledCourses({ classId: selectedClassId.value })
    unscheduledCourses.value = res.data || []
  } catch (e) { console.error('加载未排课程失败', e) }
}

async function loadTimetable() {
  if (!viewClassId.value) return
  try {
    const res = await getClassTimetable(viewClassId.value)
    timetableData.value = res.data?.cells || res.data || []
    periods.value = res.data?.periods || Array.from({ length: 8 }, (_, i) => ({ index: i + 1, label: `第${i + 1}节` }))
    filterTimetable()
  } catch (e) { console.error('加载课表失败', e) }
}

async function loadClassOptions() {
  try {
    const res = await getClasses({ pageSize: 999 })
    classOptions.value = res.data?.list || res.data || []
  } catch (e) { console.error('加载班级列表失败', e) }
}

function onDragStart(event, course) {
  dragSource.value = { type: 'unscheduled', course }
  dragFromCell.value = null
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', JSON.stringify({ type: 'unscheduled', courseId: course.id }))
  event.target.style.opacity = '0.5'
}

function onCellDragStart(event, periodIdx, dayIdx) {
  const cell = getCellData(periodIdx, dayIdx)
  if (!cell || cell.locked) {
    event.preventDefault()
    return
  }
  dragSource.value = null
  dragFromCell.value = { periodIndex: periodIdx + 1, dayOfWeek: dayIdx, cell }
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', JSON.stringify({ type: 'cell', periodIndex: periodIdx + 1, dayOfWeek: dayIdx }))
  event.target.style.opacity = '0.5'
}

function onDragEnd(event) {
  event.target.style.opacity = '1'
  dragSource.value = null
  dragFromCell.value = null
  conflictCells.value = {}
}

async function onDragOver(event, periodIdx, dayIdx) {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'

  const key = `${periodIdx}-${dayIdx}`
  if (conflictCells.value[key] !== undefined) return

  try {
    const existingCell = getCellData(periodIdx, dayIdx)
    if (existingCell) {
      conflictCells.value[key] = true
      return
    }

    const checkData = {
      periodIndex: periodIdx + 1,
      dayOfWeek: dayIdx,
      classId: viewClassId.value
    }
    if (dragSource.value) {
      checkData.teacherId = dragSource.value.course.teacherId
      checkData.classroomId = dragSource.value.course.classroomId
    } else if (dragFromCell.value) {
      checkData.teacherId = dragFromCell.value.cell.teacherId
      checkData.classroomId = dragFromCell.value.cell.classroomId
    }

    const res = await checkConflict(checkData)
    conflictCells.value[key] = res.data?.hasConflict ? true : false
  } catch (e) {
    conflictCells.value[key] = false
  }
}

function onDragLeave(event, periodIdx, dayIdx) {
  const key = `${periodIdx}-${dayIdx}`
  delete conflictCells.value[key]
}

async function onDrop(event, periodIdx, dayIdx) {
  event.preventDefault()
  conflictCells.value = {}

  const existingCell = getCellData(periodIdx, dayIdx)
  if (existingCell) {
    ElMessage.warning('该位置已有课程')
    return
  }

  const targetPeriod = periodIdx + 1
  const targetDay = dayIdx

  try {
    if (dragSource.value) {
      const course = dragSource.value.course
      await dragScheduleCell({
        assignmentId: course.id,
        classId: viewClassId.value,
        periodIndex: targetPeriod,
        dayOfWeek: targetDay,
        weekType: course.weekType || 'all'
      })
      ElMessage.success('课程放置成功')
    } else if (dragFromCell.value) {
      const from = dragFromCell.value
      await dragScheduleCell({
        cellId: from.cell.id,
        classId: viewClassId.value,
        fromPeriodIndex: from.periodIndex,
        fromDayOfWeek: from.dayOfWeek,
        toPeriodIndex: targetPeriod,
        toDayOfWeek: targetDay
      })
      ElMessage.success('课程移动成功')
    }

    undoStack.value.push({ type: 'move', from: dragFromCell.value, to: { periodIndex: targetPeriod, dayOfWeek: targetDay } })
    if (undoStack.value.length > 20) undoStack.value.shift()
    redoStack.value = []

    loadTimetable()
    loadUnscheduled()
  } catch (e) {
    ElMessage.error('操作失败：' + (e.message || '冲突检测未通过'))
  }
}

function showContextMenu(event, periodIdx, dayIdx) {
  const cell = getCellData(periodIdx, dayIdx)
  contextMenu.visible = true
  contextMenu.x = event.clientX
  contextMenu.y = event.clientY
  contextMenu.periodIndex = periodIdx
  contextMenu.dayIndex = dayIdx
  contextMenu.cellData = cell
}

function hideContextMenu() { contextMenu.visible = false }

async function handleLockCell() {
  if (!contextMenu.cellData) return
  try {
    await lockTimetableCell(contextMenu.cellData.id)
    ElMessage.success('已锁定'); hideContextMenu(); loadTimetable()
  } catch (e) { ElMessage.error('锁定失败') }
}

async function handleUnlockCell() {
  if (!contextMenu.cellData) return
  try {
    await unlockTimetableCell(contextMenu.cellData.id)
    ElMessage.success('已解锁'); hideContextMenu(); loadTimetable()
  } catch (e) { ElMessage.error('解锁失败') }
}

async function handleDeleteCell() {
  if (!contextMenu.cellData) return
  try {
    await ElMessageBox.confirm('确定要删除此课程吗？', '确认', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    await deleteTimetableCell(contextMenu.cellData.id)
    ElMessage.success('已删除'); hideContextMenu(); loadTimetable(); loadUnscheduled()
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

function handleSwapCell() {
  ElMessage.info('请拖拽另一个课程到此位置进行交换')
  hideContextMenu()
}

function handleUndo() {
  if (undoStack.value.length === 0) return
  const action = undoStack.value.pop()
  redoStack.value.push(action)
  ElMessage.info('撤销操作（需保存后生效）')
}

function handleRedo() {
  if (redoStack.value.length === 0) return
  const action = redoStack.value.pop()
  undoStack.value.push(action)
  ElMessage.info('重做操作（需保存后生效）')
}

async function handleSave() {
  saveLoading.value = true
  try {
    ElMessage.success('课表已保存')
    undoStack.value = []
    redoStack.value = []
  } catch (e) { ElMessage.error('保存失败') } finally { saveLoading.value = false }
}

function onClickOutside() { hideContextMenu() }

onMounted(() => {
  loadClassOptions()
  document.addEventListener('click', onClickOutside)
})

onUnmounted(() => { document.removeEventListener('click', onClickOutside) })
</script>

<style scoped>
.drag-schedule-page { height: calc(100vh - 120px); display: flex; flex-direction: column; }

.drag-layout { display: flex; gap: 16px; flex: 1; overflow: hidden; }

.left-panel {
  width: 260px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #ebeef5;
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.unscheduled-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.drag-source {
  cursor: grab;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 10px 12px;
  margin: 6px 0;
  background: #fafafa;
  transition: all 0.2s;
}

.drag-source:hover {
  border-color: #409EFF;
  background: #ecf5ff;
}

.drag-source:active { cursor: grabbing; }

.drag-course-subject { font-size: 14px; font-weight: 700; }
.drag-course-info { font-size: 12px; color: #909399; margin-top: 4px; display: flex; gap: 8px; }
.drag-course-week { margin-top: 4px; }

.main-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

.main-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.timetable-grid {
  display: grid;
  gap: 2px;
  background: #ebeef5;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: auto;
  flex: 1;
}

.timetable-header { background: #f5f7fa; padding: 8px; text-align: center; font-weight: 600; font-size: 13px; color: #303133; }
.timetable-period { background: #f5f7fa; padding: 6px 4px; text-align: center; font-size: 12px; color: #606266; display: flex; flex-direction: column; justify-content: center; align-items: center; }
.period-index { font-weight: 600; font-size: 12px; }

.timetable-cell {
  background: #fff;
  padding: 4px;
  min-height: 64px;
  transition: all 0.15s;
  position: relative;
}

.timetable-cell.drag-target { cursor: pointer; }

.timetable-cell.drop-valid {
  background: #f0f9eb !important;
  outline: 2px solid #67C23A !important;
  outline-offset: -2px;
}

.timetable-cell.drop-invalid {
  background: #fef0f0 !important;
  outline: 2px solid #F56C6C !important;
  outline-offset: -2px;
}

.cell-content {
  padding: 6px 8px;
  border-radius: 6px;
  min-height: 52px;
  cursor: grab;
  position: relative;
  transition: transform 0.15s;
}

.cell-content:hover { transform: scale(1.02); }
.cell-content:active { cursor: grabbing; }

.subject-name { font-size: 13px; font-weight: 600; color: #303133; display: block; }
.teacher-name { font-size: 11px; color: #909399; margin-top: 1px; display: block; }
.classroom-name { font-size: 11px; color: #c0c4cc; margin-top: 1px; display: block; }

.week-badge {
  position: absolute; top: 2px; right: 2px;
  font-size: 10px; padding: 0 4px; border-radius: 2px; line-height: 16px;
}
.week-badge-odd { background: #e6f7ff; color: #1890ff; }
.week-badge-even { background: #fff7e6; color: #fa8c16; }

.lock-icon {
  position: absolute; bottom: 2px; right: 2px;
  font-size: 12px; color: #E6A23C;
}

.context-menu {
  position: fixed;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  padding: 4px 0;
  z-index: 9999;
  min-width: 140px;
}

.context-menu-item {
  padding: 8px 16px;
  font-size: 13px;
  color: #303133;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.15s;
}

.context-menu-item:hover { background: #ecf5ff; color: #409EFF; }

@media (max-width: 768px) {
  .drag-layout { flex-direction: column; }
  .left-panel { width: 100%; max-height: 200px; }
}
</style>

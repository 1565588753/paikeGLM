<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">时间段编辑</h2>
      <div>
        <el-button @click="$router.push('/schedules')">
          <el-icon><ArrowLeft /></el-icon>返回模板列表
        </el-button>
        <el-button type="primary" :loading="saveLoading" @click="handleSave">
          <el-icon><Check /></el-icon>保存
        </el-button>
      </div>
    </div>

    <el-card v-if="template" shadow="never" style="margin-bottom: 20px;">
      <div style="display: flex; align-items: center; gap: 16px;">
        <el-tag type="primary" size="large">{{ template.name }}</el-tag>
        <span style="color: #909399;">{{ template.daysPerWeek }}天/周 · {{ template.periodsPerDay }}节/天</span>
      </div>
    </el-card>

    <div class="timeslot-editor">
      <div v-for="day in days" :key="day.index" class="day-column">
        <div class="day-header">{{ day.label }}</div>
        <div class="day-timeline">
          <div
            v-for="slot in getSlotsForDay(day.index)"
            :key="slot.id || slot.tempId"
            class="timeslot-block"
            :class="'type-' + (slot.periodType || 'class')"
            :style="getSlotStyle(slot)"
            @click="editSlot(slot)"
          >
            <div class="slot-label">{{ slot.label || `第${slot.periodIndex}节` }}</div>
            <div class="slot-time">{{ slot.startTime }} - {{ slot.endTime }}</div>
            <div class="slot-type-badge">{{ getTypeLabel(slot.periodType) }}</div>
          </div>
          <el-button
            class="add-slot-btn"
            type="primary"
            text
            @click="addSlot(day.index)"
          >
            <el-icon><Plus /></el-icon>添加时间段
          </el-button>
        </div>
      </div>
    </div>

    <el-dialog v-model="slotDialogVisible" :title="editingSlot ? '编辑时间段' : '添加时间段'" width="450px" destroy-on-close>
      <el-form ref="slotFormRef" :model="slotForm" :rules="slotFormRules" label-width="100px">
        <el-form-item label="标签" prop="label">
          <el-input v-model="slotForm.label" placeholder="例如：第一节" />
        </el-form-item>
        <el-form-item label="节次" prop="periodIndex">
          <el-input-number v-model="slotForm.periodIndex" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="开始时间" prop="startTime">
          <el-time-picker v-model="slotForm.startTime" format="HH:mm" value-format="HH:mm" placeholder="选择开始时间" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="结束时间" prop="endTime">
          <el-time-picker v-model="slotForm.endTime" format="HH:mm" value-format="HH:mm" placeholder="选择结束时间" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="类型" prop="periodType">
          <el-select v-model="slotForm.periodType" style="width: 100%;">
            <el-option label="上课" value="class" />
            <el-option label="课间操" value="break" />
            <el-option label="午休" value="lunch" />
            <el-option label="晚自习" value="evening" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="slotDialogVisible = false">取消</el-button>
        <el-button v-if="editingSlot" type="danger" @click="removeSlot">删除</el-button>
        <el-button type="primary" @click="handleSlotSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { getScheduleTemplate, getTimeSlots, updateTimeSlots, addTimeSlot, deleteTimeSlot } from '../../api/schedule'
import { ElMessage } from 'element-plus'

const route = useRoute()
const templateId = route.params.id
const template = ref(null)
const timeSlots = ref([])
const saveLoading = ref(false)
const slotDialogVisible = ref(false)
const editingSlot = ref(null)
const slotFormRef = ref(null)

const days = [
  { index: 1, label: '周一' }, { index: 2, label: '周二' }, { index: 3, label: '周三' },
  { index: 4, label: '周四' }, { index: 5, label: '周五' }, { index: 6, label: '周六' }, { index: 7, label: '周日' }
]

const slotForm = reactive({
  label: '', periodIndex: 1, startTime: '', endTime: '', periodType: 'class', dayOfWeek: 1
})

const slotFormRules = {
  label: [{ required: true, message: '请输入标签', trigger: 'blur' }],
  startTime: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  endTime: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  periodType: [{ required: true, message: '请选择类型', trigger: 'change' }]
}

const typeLabels = { class: '上课', break: '课间操', lunch: '午休', evening: '晚自习' }
function getTypeLabel(type) { return typeLabels[type] || type }

function getSlotsForDay(dayIndex) {
  return timeSlots.value.filter(s => s.dayOfWeek === dayIndex).sort((a, b) => {
    if (a.startTime < b.startTime) return -1
    if (a.startTime > b.startTime) return 1
    return 0
  })
}

function getSlotStyle(slot) {
  return {}
}

async function loadData() {
  try {
    const tplRes = await getScheduleTemplate(templateId)
    template.value = tplRes.data
    const slotsRes = await getTimeSlots(templateId)
    timeSlots.value = (slotsRes.data || []).map(s => ({ ...s, tempId: s.id || Math.random().toString(36).substr(2, 9) }))
  } catch (e) { console.error('加载数据失败', e) }
}

function addSlot(dayIndex) {
  editingSlot.value = null
  const existingSlots = getSlotsForDay(dayIndex)
  Object.assign(slotForm, {
    label: `第${existingSlots.length + 1}节`,
    periodIndex: existingSlots.length + 1,
    startTime: '', endTime: '', periodType: 'class', dayOfWeek: dayIndex
  })
  slotDialogVisible.value = true
}

function editSlot(slot) {
  editingSlot.value = slot
  Object.assign(slotForm, { ...slot })
  slotDialogVisible.value = true
}

async function handleSlotSubmit() {
  if (!slotFormRef.value) return
  await slotFormRef.value.validate(async (valid) => {
    if (!valid) return
    if (editingSlot.value) {
      const idx = timeSlots.value.findIndex(s => (s.id || s.tempId) === (editingSlot.value.id || editingSlot.value.tempId))
      if (idx >= 0) {
        timeSlots.value[idx] = { ...timeSlots.value[idx], ...slotForm }
      }
    } else {
      timeSlots.value.push({ ...slotForm, tempId: Math.random().toString(36).substr(2, 9) })
    }
    slotDialogVisible.value = false
  })
}

function removeSlot() {
  const idx = timeSlots.value.findIndex(s => (s.id || s.tempId) === (editingSlot.value.id || editingSlot.value.tempId))
  if (idx >= 0) {
    timeSlots.value.splice(idx, 1)
  }
  slotDialogVisible.value = false
}

async function handleSave() {
  saveLoading.value = true
  try {
    await updateTimeSlots(templateId, timeSlots.value)
    ElMessage.success('保存成功')
    loadData()
  } catch (e) { console.error('保存失败', e) } finally { saveLoading.value = false }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.timeslot-editor {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 16px;
}

.day-column {
  min-width: 200px;
  flex: 1;
}

.day-header {
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  color: #303133;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 8px 8px 0 0;
  border: 1px solid #ebeef5;
  border-bottom: none;
}

.day-timeline {
  border: 1px solid #ebeef5;
  border-radius: 0 0 8px 8px;
  padding: 8px;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.timeslot-block {
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.timeslot-block:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.type-class { background: #ecf5ff; border-left: 3px solid #409EFF; }
.type-break { background: #f0f9eb; border-left: 3px solid #67C23A; }
.type-lunch { background: #fdf6ec; border-left: 3px solid #E6A23C; }
.type-evening { background: #f3e8ff; border-left: 3px solid #9C27B0; }

.slot-label { font-size: 13px; font-weight: 600; color: #303133; }
.slot-time { font-size: 11px; color: #909399; margin-top: 2px; }
.slot-type-badge { font-size: 10px; color: #c0c4cc; margin-top: 2px; }

.add-slot-btn { width: 100%; margin-top: 4px; }
</style>

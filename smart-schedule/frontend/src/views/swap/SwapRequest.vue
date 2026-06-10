<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">申请换课</h2>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="14">
        <el-card shadow="hover">
          <template #header>
            <span class="card-title">我的课表（点击选择要换出的课程）</span>
          </template>
          <div class="my-timetable">
            <div class="timetable-grid" :style="gridStyle">
              <div class="timetable-header"></div>
              <div v-for="day in days" :key="day.index" class="timetable-header">{{ day.label }}</div>
              <template v-for="(period, pIdx) in periods" :key="pIdx">
                <div class="timetable-period">
                  <span>{{ period.label || `第${pIdx + 1}节` }}</span>
                </div>
                <div
                  v-for="day in days"
                  :key="`${pIdx}-${day.index}`"
                  class="timetable-cell"
                  :class="{ selected: isSelected(pIdx, day.index) }"
                  @click="selectSourceCourse(pIdx, day.index)"
                >
                  <template v-if="getCourse(pIdx, day.index)">
                    <span class="subject-name">{{ getCourse(pIdx, day.index).subjectName }}</span>
                    <span class="teacher-name">{{ getCourse(pIdx, day.index).className }}</span>
                  </template>
                </div>
              </template>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card shadow="hover">
          <template #header>
            <span class="card-title">换课信息</span>
          </template>

          <div v-if="sourceCourse" class="swap-info">
            <h4>换出课程</h4>
            <div class="course-detail" :style="{ borderLeftColor: getSubjectColorByName(sourceCourse.subjectName) }">
              <div><strong>{{ sourceCourse.subjectName }}</strong></div>
              <div>{{ sourceCourse.className }} · {{ getDayOfWeek(sourceCourse.dayOfWeek) }} 第{{ sourceCourse.periodIndex }}节</div>
              <div>{{ sourceCourse.startTime }}-{{ sourceCourse.endTime }}</div>
            </div>

            <h4 style="margin-top: 16px;">换入目标</h4>
            <el-form label-width="80px" size="default">
              <el-form-item label="目标教师">
                <el-select v-model="swapForm.targetTeacherId" placeholder="选择目标教师" filterable style="width: 100%;" @change="loadTargetTimetable">
                  <el-option v-for="t in teacherOptions" :key="t.id" :label="t.name || t.username" :value="t.id" />
                </el-select>
              </el-form-item>
            </el-form>

            <div v-if="targetTimetable.length > 0" class="target-timetable">
              <p style="font-size: 13px; color: #909399; margin-bottom: 8px;">点击选择目标时间段：</p>
              <div class="target-grid">
                <div v-for="day in days" :key="'th-' + day.index" class="target-header">{{ day.label }}</div>
                <template v-for="(period, pIdx) in periods" :key="'tp-' + pIdx">
                  <div class="target-period">{{ pIdx + 1 }}</div>
                  <div
                    v-for="day in days"
                    :key="`t-${pIdx}-${day.index}`"
                    class="target-cell"
                    :class="{
                      occupied: getTargetCourse(pIdx, day.index),
                      'target-selected': isTargetSelected(pIdx, day.index),
                      'conflict-cell': targetConflict
                    }"
                    @click="selectTarget(pIdx, day.index)"
                  >
                    <span v-if="getTargetCourse(pIdx, day.index)" style="font-size: 10px;">
                      {{ getTargetCourse(pIdx, day.index).subjectName?.charAt(0) }}
                    </span>
                  </div>
                </template>
              </div>
            </div>

            <div v-if="targetSelected" class="conflict-check" style="margin-top: 16px;">
              <el-alert
                :type="targetConflict ? 'error' : 'success'"
                :title="targetConflict ? '存在冲突' : '无冲突，可以换课'"
                :description="targetConflictDetail || '该时间段可用'"
                :closable="false"
                show-icon
              />
            </div>

            <el-form label-width="80px" style="margin-top: 16px;">
              <el-form-item label="换课原因">
                <el-input v-model="swapForm.reason" type="textarea" :rows="3" placeholder="请说明换课原因" />
              </el-form-item>
            </el-form>

            <el-button
              type="primary"
              style="width: 100%; margin-top: 8px;"
              :disabled="!sourceCourse || !targetSelected || targetConflict"
              :loading="submitLoading"
              @click="submitSwap"
            >
              提交换课申请
            </el-button>
          </div>

          <el-empty v-else description="请在左侧课表中选择要换出的课程" :image-size="80" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useUserStore } from '../../stores/user'
import { useAcademicStore } from '../../stores/academic'
import { getTeacherTimetable } from '../../api/timetable'
import { getUsers } from '../../api/user'
import { createSwapRequest, checkSwapConflict } from '../../api/swap'
import { getSubjectColorByName, getDayOfWeek } from '../../utils/format'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const academicStore = useAcademicStore()
const myTimetable = ref([])
const targetTimetable = ref([])
const teacherOptions = ref([])
const periods = ref([])
const sourceCourse = ref(null)
const targetSelected = ref(false)
const targetPeriod = ref(null)
const targetDay = ref(null)
const targetConflict = ref(false)
const targetConflictDetail = ref('')
const submitLoading = ref(false)

const swapForm = reactive({
  targetTeacherId: '',
  reason: ''
})

const days = [
  { index: 1, label: '周一' }, { index: 2, label: '周二' }, { index: 3, label: '周三' },
  { index: 4, label: '周四' }, { index: 5, label: '周五' }, { index: 6, label: '周六' }, { index: 7, label: '周日' }
]

const gridStyle = computed(() => ({
  gridTemplateColumns: `50px repeat(${days.length}, 1fr)`,
  gridTemplateRows: `32px repeat(${periods.value.length || 8}, 50px)`
}))

function getCourse(periodIdx, dayIdx) {
  return myTimetable.value.find(c => c.periodIndex === periodIdx + 1 && c.dayOfWeek === dayIdx)
}

function getTargetCourse(periodIdx, dayIdx) {
  return targetTimetable.value.find(c => c.periodIndex === periodIdx + 1 && c.dayOfWeek === dayIdx)
}

function isSelected(periodIdx, dayIdx) {
  return sourceCourse.value && sourceCourse.value.periodIndex === periodIdx + 1 && sourceCourse.value.dayOfWeek === dayIdx
}

function isTargetSelected(periodIdx, dayIdx) {
  return targetSelected.value && targetPeriod.value === periodIdx + 1 && targetDay.value === dayIdx
}

function selectSourceCourse(periodIdx, dayIdx) {
  const course = getCourse(periodIdx, dayIdx)
  if (course) {
    sourceCourse.value = course
    targetSelected.value = false
    targetConflict.value = false
  }
}

async function selectTarget(periodIdx, dayIdx) {
  targetPeriod.value = periodIdx + 1
  targetDay.value = dayIdx
  targetSelected.value = true

  if (sourceCourse.value && swapForm.targetTeacherId) {
    try {
      const res = await checkSwapConflict({
        sourceCellId: sourceCourse.value.id,
        targetTeacherId: swapForm.targetTeacherId,
        targetPeriodIndex: periodIdx + 1,
        targetDayOfWeek: dayIdx
      })
      targetConflict.value = res.data?.hasConflict || false
      targetConflictDetail.value = res.data?.conflictDetail || ''
    } catch (e) {
      targetConflict.value = true
      targetConflictDetail.value = '冲突检测失败'
    }
  }
}

async function loadMyTimetable() {
  if (!userStore.userInfo.id) return
  try {
    const res = await getTeacherTimetable(userStore.userInfo.id)
    myTimetable.value = res.data || []
    if (myTimetable.value.length > 0) {
      const maxPeriod = Math.max(...myTimetable.value.map(c => c.periodIndex))
      periods.value = Array.from({ length: maxPeriod }, (_, i) => ({ index: i + 1, label: `第${i + 1}节` }))
    } else {
      periods.value = Array.from({ length: 8 }, (_, i) => ({ index: i + 1, label: `第${i + 1}节` }))
    }
  } catch (e) { console.error('加载课表失败', e) }
}

async function loadTargetTimetable() {
  if (!swapForm.targetTeacherId) return
  try {
    const res = await getTeacherTimetable(swapForm.targetTeacherId)
    targetTimetable.value = res.data || []
  } catch (e) { console.error('加载目标教师课表失败', e) }
}

async function loadTeacherOptions() {
  try {
    const res = await getUsers({ pageSize: 999, role: 'teacher' })
    teacherOptions.value = (res.data?.list || res.data || []).filter(t => t.id !== userStore.userInfo.id)
  } catch (e) { console.error('加载教师列表失败', e) }
}

async function submitSwap() {
  if (!sourceCourse.value || !targetSelected.value) return
  submitLoading.value = true
  try {
    await createSwapRequest({
      sourceCellId: sourceCourse.value.id,
      targetTeacherId: swapForm.targetTeacherId,
      targetPeriodIndex: targetPeriod.value,
      targetDayOfWeek: targetDay.value,
      reason: swapForm.reason
    })
    ElMessage.success('换课申请已提交')
    sourceCourse.value = null
    targetSelected.value = false
    swapForm.reason = ''
    swapForm.targetTeacherId = ''
    targetTimetable.value = []
  } catch (e) { ElMessage.error('提交失败：' + (e.message || '未知错误')) } finally { submitLoading.value = false }
}

onMounted(() => { loadMyTimetable(); loadTeacherOptions() })
</script>

<style scoped>
.card-title { font-size: 15px; font-weight: 600; color: #303133; }
.timetable-grid { display: grid; gap: 2px; background: #ebeef5; border: 1px solid #ebeef5; border-radius: 8px; overflow: hidden; }
.timetable-header { background: #f5f7fa; padding: 6px; text-align: center; font-weight: 600; font-size: 12px; color: #303133; }
.timetable-period { background: #f5f7fa; padding: 4px; text-align: center; font-size: 11px; color: #606266; display: flex; align-items: center; justify-content: center; }
.timetable-cell { background: #fff; padding: 4px; min-height: 50px; cursor: pointer; transition: all 0.15s; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }
.timetable-cell:hover { background: #ecf5ff; }
.timetable-cell.selected { background: #409EFF30; outline: 2px solid #409EFF; outline-offset: -2px; }
.subject-name { font-size: 12px; font-weight: 600; color: #303133; }
.teacher-name { font-size: 10px; color: #909399; }
.course-detail { padding: 12px; border-left: 4px solid #409EFF; background: #fafafa; border-radius: 0 8px 8px 0; margin-top: 8px; }
.target-grid { display: grid; grid-template-columns: 24px repeat(7, 1fr); gap: 2px; }
.target-header { background: #f5f7fa; text-align: center; font-size: 11px; font-weight: 600; padding: 4px; border-radius: 2px; }
.target-period { background: #f5f7fa; text-align: center; font-size: 10px; padding: 4px; display: flex; align-items: center; justify-content: center; }
.target-cell { background: #fff; min-height: 24px; cursor: pointer; border: 1px solid #ebeef5; border-radius: 2px; display: flex; align-items: center; justify-content: center; transition: all 0.15s; }
.target-cell:hover { background: #ecf5ff; }
.target-cell.occupied { background: #f0f2f5; }
.target-cell.target-selected { background: #409EFF30; border-color: #409EFF; }
.target-cell.conflict-cell { background: #fef0f0; border-color: #F56C6C; }
</style>

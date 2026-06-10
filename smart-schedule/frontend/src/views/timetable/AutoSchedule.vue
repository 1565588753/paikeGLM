<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">智能排课</h2>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <span class="card-title">排课配置</span>
          </template>

          <el-form label-width="120px" label-position="top">
            <el-form-item label="选择排课班级">
              <el-checkbox-group v-model="selectedClasses">
                <div v-for="grade in groupedClasses" :key="grade.grade" class="grade-group">
                  <div class="grade-label">{{ grade.grade }}年级</div>
                  <el-checkbox v-for="cls in grade.classes" :key="cls.id" :label="cls.name" :value="cls.id" />
                </div>
              </el-checkbox-group>
              <div style="margin-top: 8px;">
                <el-button size="small" text type="primary" @click="selectAllClasses">全选</el-button>
                <el-button size="small" text @click="selectedClasses = []">清空</el-button>
              </div>
            </el-form-item>

            <el-form-item label="排课周次">
              <el-radio-group v-model="scheduleWeekType">
                <el-radio value="all">全周课程</el-radio>
                <el-radio value="odd">仅单周</el-radio>
                <el-radio value="even">仅双周</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="排课规则">
              <div class="rules-list">
                <el-checkbox v-model="rules.noTeacherConflict" disabled>教师不冲突</el-checkbox>
                <el-checkbox v-model="rules.noClassConflict" disabled>班级不冲突</el-checkbox>
                <el-checkbox v-model="rules.noRoomConflict">教室不冲突</el-checkbox>
                <el-checkbox v-model="rules.mainSubjectFirst">主科优先上午</el-checkbox>
                <el-checkbox v-model="rules.noDoubleMain">语数外不同天连排</el-checkbox>
                <el-checkbox v-model="rules.teacherDailyLimit">教师每日课时上限</el-checkbox>
                <el-checkbox v-model="rules.balancedDistribution">课程均匀分布</el-checkbox>
                <el-checkbox v-model="rules.respectLocked">保留已锁定课程</el-checkbox>
                <el-checkbox v-model="rules.subSubjectMapping">启用语数外匹配小课</el-checkbox>
              </div>
            </el-form-item>

            <el-form-item label="教师每日最大课时" v-if="rules.teacherDailyLimit">
              <el-input-number v-model="teacherDailyMax" :min="2" :max="8" />
            </el-form-item>
          </el-form>

          <div class="action-buttons">
            <el-button
              type="primary"
              size="large"
              :loading="isScheduling"
              :disabled="selectedClasses.length === 0 || isScheduling"
              @click="startSchedule"
            >
              <el-icon><MagicStick /></el-icon>
              {{ isScheduling ? '排课中...' : '开始排课' }}
            </el-button>
            <el-button
              v-if="isScheduling"
              type="warning"
              size="large"
              @click="pauseSchedule"
            >
              <el-icon><VideoPause /></el-icon>暂停
            </el-button>
            <el-button
              v-if="isScheduling"
              type="danger"
              size="large"
              @click="cancelSchedule"
            >
              <el-icon><Close /></el-icon>取消
            </el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <span class="card-title">排课进度</span>
          </template>

          <div class="progress-section">
            <el-progress
              :percentage="progress"
              :stroke-width="20"
              :text-inside="true"
              :status="progressStatus"
              style="margin-bottom: 16px;"
            />
            <div class="status-text">
              <el-icon v-if="isScheduling" class="is-loading"><Loading /></el-icon>
              {{ statusText }}
            </div>
          </div>

          <div v-if="scheduleCompleted" class="result-section">
            <el-divider>排课结果</el-divider>

            <el-row :gutter="16">
              <el-col :span="8">
                <div class="result-stat">
                  <div class="result-value success">{{ resultStats.totalHours }}</div>
                  <div class="result-label">总排课时</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="result-stat">
                  <div class="result-value" :class="resultStats.conflicts > 0 ? 'danger' : 'success'">{{ resultStats.conflicts }}</div>
                  <div class="result-label">冲突数量</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="result-stat">
                  <div class="result-value" :class="resultStats.satisfaction >= 90 ? 'success' : 'warning'">{{ resultStats.satisfaction }}%</div>
                  <div class="result-label">规则满足率</div>
                </div>
              </el-col>
            </el-row>

            <div v-if="resultStats.conflictList && resultStats.conflictList.length > 0" class="conflict-list">
              <h4>冲突详情</h4>
              <el-alert
                v-for="(conflict, idx) in resultStats.conflictList"
                :key="idx"
                :title="conflict.message"
                :description="conflict.detail"
                type="warning"
                :closable="false"
                show-icon
                style="margin-bottom: 8px;"
              />
            </div>

            <el-button type="primary" size="large" @click="viewResult" style="width: 100%; margin-top: 16px;">
              <el-icon><View /></el-icon>查看排课结果
            </el-button>
          </div>
        </el-card>

        <el-card shadow="hover" style="margin-top: 20px;">
          <template #header>
            <span class="card-title">排课历史</span>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="item in scheduleHistory"
              :key="item.id"
              :timestamp="item.time"
              :type="item.status === 'success' ? 'success' : (item.status === 'failed' ? 'danger' : 'primary')"
            >
              {{ item.description }}
            </el-timeline-item>
          </el-timeline>
          <el-empty v-if="scheduleHistory.length === 0" description="暂无排课记录" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { startAutoSchedule, getAutoScheduleStatus, cancelAutoSchedule, pauseAutoSchedule, resumeAutoSchedule } from '../../api/timetable'
import { getClasses } from '../../api/class'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const selectedClasses = ref([])
const scheduleWeekType = ref('all')
const teacherDailyMax = ref(4)
const isScheduling = ref(false)
const isPaused = ref(false)
const progress = ref(0)
const statusText = ref('等待开始排课')
const scheduleCompleted = ref(false)
const currentTaskId = ref(null)
const classList = ref([])
const scheduleHistory = ref([])
let pollTimer = null

const rules = reactive({
  noTeacherConflict: true,
  noClassConflict: true,
  noRoomConflict: true,
  mainSubjectFirst: true,
  noDoubleMain: true,
  teacherDailyLimit: true,
  balancedDistribution: true,
  respectLocked: true,
  subSubjectMapping: false
})

const resultStats = reactive({
  totalHours: 0,
  conflicts: 0,
  satisfaction: 0,
  conflictList: []
})

const groupedClasses = computed(() => {
  const groups = {}
  classList.value.forEach(cls => {
    if (!groups[cls.grade]) groups[cls.grade] = { grade: cls.grade, classes: [] }
    groups[cls.grade].classes.push(cls)
  })
  return Object.values(groups).sort((a, b) => a.grade - b.grade)
})

const progressStatus = computed(() => {
  if (progress.value === 100) return 'success'
  if (isScheduling.value) return ''
  return ''
})

async function loadClasses() {
  try {
    const res = await getClasses({ pageSize: 999 })
    classList.value = res.data?.list || res.data || []
  } catch (e) { console.error('加载班级失败', e) }
}

function selectAllClasses() {
  selectedClasses.value = classList.value.map(c => c.id)
}

async function startSchedule() {
  if (selectedClasses.value.length === 0) {
    ElMessage.warning('请选择至少一个班级')
    return
  }

  try {
    await ElMessageBox.confirm(
      `即将为 ${selectedClasses.value.length} 个班级进行智能排课，此操作可能需要几分钟时间。是否继续？`,
      '确认排课',
      { confirmButtonText: '开始排课', cancelButtonText: '取消', type: 'info' }
    )
  } catch { return }

  isScheduling.value = true
  isPaused.value = false
  progress.value = 0
  statusText.value = '正在初始化排课引擎...'
  scheduleCompleted.value = false

  try {
    const res = await startAutoSchedule({
      classIds: selectedClasses.value,
      weekType: scheduleWeekType.value,
      rules: { ...rules, teacherDailyMax: teacherDailyMax.value }
    })
    currentTaskId.value = res.data?.taskId || 'task-1'
    startPolling()
  } catch (e) {
    ElMessage.error('启动排课失败：' + (e.message || '未知错误'))
    isScheduling.value = false
    statusText.value = '排课启动失败'
  }
}

function startPolling() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(async () => {
    try {
      const res = await getAutoScheduleStatus(currentTaskId.value)
      const data = res.data || {}
      progress.value = data.progress || 0
      statusText.value = data.statusText || '排课进行中...'

      if (data.status === 'completed') {
        clearInterval(pollTimer)
        pollTimer = null
        isScheduling.value = false
        scheduleCompleted.value = true
        resultStats.totalHours = data.totalHours || 0
        resultStats.conflicts = data.conflicts || 0
        resultStats.satisfaction = data.satisfaction || 95
        resultStats.conflictList = data.conflictList || []
        statusText.value = '排课完成！'
        scheduleHistory.value.unshift({
          id: Date.now(),
          time: new Date().toLocaleString(),
          status: 'success',
          description: `为 ${selectedClasses.value.length} 个班级排课完成，满足率 ${resultStats.satisfaction}%`
        })
        ElMessage.success('智能排课完成！')
      } else if (data.status === 'failed') {
        clearInterval(pollTimer)
        pollTimer = null
        isScheduling.value = false
        statusText.value = '排课失败：' + (data.error || '未知错误')
        scheduleHistory.value.unshift({
          id: Date.now(),
          time: new Date().toLocaleString(),
          status: 'failed',
          description: '排课失败：' + (data.error || '未知错误')
        })
      } else if (data.status === 'paused') {
        isPaused.value = true
      }
    } catch (e) {
      console.error('轮询状态失败', e)
    }
  }, 2000)
}

async function pauseSchedule() {
  try {
    if (isPaused.value) {
      await resumeAutoSchedule(currentTaskId.value)
      isPaused.value = false
      statusText.value = '排课继续中...'
    } else {
      await pauseAutoSchedule(currentTaskId.value)
      isPaused.value = true
      statusText.value = '排课已暂停'
    }
  } catch (e) { ElMessage.error('操作失败') }
}

async function cancelSchedule() {
  try {
    await ElMessageBox.confirm('确定要取消排课吗？已排课程将回滚。', '确认', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    await cancelAutoSchedule(currentTaskId.value)
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
    isScheduling.value = false
    progress.value = 0
    statusText.value = '排课已取消'
    scheduleHistory.value.unshift({
      id: Date.now(), time: new Date().toLocaleString(), status: 'failed', description: '排课被用户取消'
    })
  } catch (e) { if (e !== 'cancel') ElMessage.error('取消失败') }
}

function viewResult() {
  router.push('/timetable/class')
}

loadClasses()

onUnmounted(() => {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
})
</script>

<style scoped>
.card-title { font-size: 16px; font-weight: 600; color: #303133; }
.grade-group { margin-bottom: 8px; }
.grade-label { font-size: 13px; font-weight: 600; color: #606266; margin-bottom: 4px; }
.rules-list { display: flex; flex-direction: column; gap: 8px; }
.action-buttons { display: flex; gap: 12px; margin-top: 20px; }
.action-buttons .el-button { flex: 1; }
.progress-section { margin-bottom: 20px; }
.status-text { font-size: 14px; color: #606266; display: flex; align-items: center; gap: 8px; }
.result-section { margin-top: 16px; }
.result-stat { text-align: center; padding: 16px 0; }
.result-value { font-size: 32px; font-weight: 700; }
.result-value.success { color: #67C23A; }
.result-value.danger { color: #F56C6C; }
.result-value.warning { color: #E6A23C; }
.result-label { font-size: 13px; color: #909399; margin-top: 4px; }
.conflict-list { margin-top: 16px; }
.conflict-list h4 { font-size: 14px; color: #303133; margin-bottom: 8px; }
</style>

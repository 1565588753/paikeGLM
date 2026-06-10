<template>
  <div class="dashboard-container">
    <div class="welcome-section">
      <div class="welcome-text">
        <h2>{{ greeting }}，{{ userStore.displayName }}</h2>
        <p>{{ academicStore.fullLabel || '暂未设置学年学期' }}</p>
      </div>
      <div class="quick-actions">
        <el-button type="primary" @click="$router.push('/auto-schedule')">
          <el-icon><MagicStick /></el-icon>智能排课
        </el-button>
        <el-button @click="$router.push('/timetable/teacher')">
          <el-icon><Grid /></el-icon>我的课表
        </el-button>
        <el-button @click="$router.push('/swap/request')">
          <el-icon><Switch /></el-icon>申请换课
        </el-button>
      </div>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #ecf5ff;">
            <el-icon :size="28" color="#409EFF"><School /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalClasses }}</div>
            <div class="stat-label">班级总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #f0f9eb;">
            <el-icon :size="28" color="#67C23A"><UserFilled /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalTeachers }}</div>
            <div class="stat-label">教师总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #fdf6ec;">
            <el-icon :size="28" color="#E6A23C"><Reading /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalSubjects }}</div>
            <div class="stat-label">科目总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #fef0f0;">
            <el-icon :size="28" color="#F56C6C"><Calendar /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.todayCourses }}</div>
            <div class="stat-label">今日课程</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="content-row">
      <el-col :xs="24" :lg="16">
        <el-card shadow="hover" class="schedule-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">今日课表</span>
              <el-button text type="primary" @click="$router.push('/timetable/teacher')">
                查看完整课表 <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </template>
          <div v-if="todaySchedule.length === 0" class="empty-schedule">
            <el-empty description="今日无课程安排" :image-size="80" />
          </div>
          <div v-else class="today-schedule">
            <div
              v-for="(item, index) in todaySchedule"
              :key="index"
              class="schedule-item"
              :style="{ borderLeftColor: getSubjectColorByName(item.subject) }"
            >
              <div class="schedule-time">
                <span class="time-start">{{ item.startTime }}</span>
                <span class="time-end">{{ item.endTime }}</span>
              </div>
              <div class="schedule-info">
                <div class="schedule-subject">{{ item.subject }}</div>
                <div class="schedule-detail">
                  <span v-if="item.className">{{ item.className }}</span>
                  <span v-if="item.classroom">{{ item.classroom }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <el-card v-if="userStore.isTeacher" shadow="hover" class="week-schedule-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span class="card-title">本周课表概览</span>
            </div>
          </template>
          <div class="week-overview">
            <div v-for="day in weekDays" :key="day.index" class="week-day-col">
              <div class="week-day-header" :class="{ today: day.isToday }">
                {{ day.label }}
              </div>
              <div class="week-day-courses">
                <div
                  v-for="course in weekSchedule[day.index] || []"
                  :key="course.id"
                  class="week-course-dot"
                  :style="{ background: getSubjectColorByName(course.subject) }"
                  :title="`${course.subject} ${course.startTime}-${course.endTime}`"
                ></div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card shadow="hover" class="notification-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">最近通知</span>
              <el-button text type="primary" @click="$router.push('/notifications')">
                全部 <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </template>
          <div v-if="recentNotifications.length === 0" class="empty-schedule">
            <el-empty description="暂无通知" :image-size="60" />
          </div>
          <div v-else class="notification-list">
            <div
              v-for="item in recentNotifications"
              :key="item.id"
              class="notification-item"
              :class="{ unread: !item.read }"
              @click="handleNotification(item)"
            >
              <div class="notification-dot" v-if="!item.read"></div>
              <div class="notification-content">
                <div class="notification-title">{{ item.title }}</div>
                <div class="notification-time">{{ getRelativeTime(item.createdAt) }}</div>
              </div>
            </div>
          </div>
        </el-card>

        <el-card v-if="userStore.isAdmin" shadow="hover" class="system-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span class="card-title">系统概览</span>
            </div>
          </template>
          <div class="system-stats">
            <div class="system-stat-item">
              <span class="label">排课完成率</span>
              <el-progress :percentage="stats.scheduleCompletion || 0" :stroke-width="8" />
            </div>
            <div class="system-stat-item">
              <span class="label">冲突数量</span>
              <span class="value" :class="{ danger: stats.conflicts > 0 }">{{ stats.conflicts || 0 }}</span>
            </div>
            <div class="system-stat-item">
              <span class="label">待处理换课</span>
              <span class="value" :class="{ warning: stats.pendingSwaps > 0 }">{{ stats.pendingSwaps || 0 }}</span>
            </div>
            <div class="system-stat-item">
              <span class="label">换课申请</span>
              <el-button text type="primary" size="small" @click="$router.push('/swap')">
                去处理 <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useAcademicStore } from '../stores/academic'
import { useNotificationStore } from '../stores/notification'
import { getTeacherTimetable } from '../api/timetable'
import { getClasses } from '../api/class'
import { getSubjects } from '../api/subject'
import { getUsers } from '../api/user'
import { getSubjectColorByName, getRelativeTime } from '../utils/format'
import dayjs from 'dayjs'

const router = useRouter()
const userStore = useUserStore()
const academicStore = useAcademicStore()
const notificationStore = useNotificationStore()

const stats = ref({
  totalClasses: 0,
  totalTeachers: 0,
  totalSubjects: 0,
  todayCourses: 0,
  scheduleCompletion: 0,
  conflicts: 0,
  pendingSwaps: 0
})

const todaySchedule = ref([])
const weekSchedule = ref({})

const greeting = computed(() => {
  const hour = dayjs().hour()
  if (hour < 6) return '凌晨好'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const weekDays = computed(() => {
  const today = dayjs().day()
  const adjustedToday = today === 0 ? 7 : today
  return [
    { index: 1, label: '周一', isToday: adjustedToday === 1 },
    { index: 2, label: '周二', isToday: adjustedToday === 2 },
    { index: 3, label: '周三', isToday: adjustedToday === 3 },
    { index: 4, label: '周四', isToday: adjustedToday === 4 },
    { index: 5, label: '周五', isToday: adjustedToday === 5 },
    { index: 6, label: '周六', isToday: adjustedToday === 6 },
    { index: 7, label: '周日', isToday: adjustedToday === 7 }
  ]
})

const recentNotifications = computed(() => {
  return notificationStore.notifications.slice(0, 8)
})

function handleNotification(item) {
  if (!item.read) {
    notificationStore.readNotification(item.id)
  }
  router.push('/notifications')
}

async function loadDashboardData() {
  try {
    const [classesRes, subjectsRes, usersRes] = await Promise.all([
      getClasses({ page: 1, pageSize: 1 }),
      getSubjects({ page: 1, pageSize: 1 }),
      getUsers({ page: 1, pageSize: 1 })
    ])
    stats.value.totalClasses = classesRes.data?.total || 0
    stats.value.totalSubjects = subjectsRes.data?.total || 0
    stats.value.totalTeachers = usersRes.data?.total || 0
  } catch (e) {
    console.error('加载统计数据失败', e)
  }

  if (userStore.userInfo.id) {
    try {
      const res = await getTeacherTimetable(userStore.userInfo.id, {
        yearId: academicStore.currentYear?.id,
        semesterId: academicStore.currentSemester?.id
      })
      const timetableData = res.data || []
      const today = dayjs().day() || 7
      const todayCourses = timetableData.filter(c => c.dayOfWeek === today)
      todaySchedule.value = todayCourses
      stats.value.todayCourses = todayCourses.length

      const weekData = {}
      timetableData.forEach(c => {
        if (!weekData[c.dayOfWeek]) weekData[c.dayOfWeek] = []
        weekData[c.dayOfWeek].push(c)
      })
      weekSchedule.value = weekData
    } catch (e) {
      console.error('加载课表数据失败', e)
    }
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.dashboard-container {
  max-width: 1400px;
}

.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px 28px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: #fff;
}

.welcome-text h2 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 4px;
}

.welcome-text p {
  font-size: 14px;
  opacity: 0.85;
}

.quick-actions {
  display: flex;
  gap: 10px;
}

.quick-actions .el-button {
  border-radius: 8px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 0;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  padding: 20px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 2px;
}

.content-row {
  margin-top: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.empty-schedule {
  padding: 20px 0;
}

.today-schedule {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.schedule-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-left: 4px solid #409EFF;
  background: #fafafa;
  border-radius: 0 8px 8px 0;
  transition: background 0.2s;
}

.schedule-item:hover {
  background: #f0f2f5;
}

.schedule-time {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 50px;
}

.time-start {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.time-end {
  font-size: 12px;
  color: #909399;
}

.schedule-subject {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.schedule-detail {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
  display: flex;
  gap: 12px;
}

.week-overview {
  display: flex;
  gap: 8px;
  justify-content: space-between;
}

.week-day-col {
  flex: 1;
  text-align: center;
}

.week-day-header {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  padding: 6px 0;
  margin-bottom: 8px;
  border-radius: 4px;
}

.week-day-header.today {
  background: #409EFF;
  color: #fff;
}

.week-day-courses {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
}

.week-course-dot {
  width: 24px;
  height: 8px;
  border-radius: 4px;
}

.notification-list {
  display: flex;
  flex-direction: column;
}

.notification-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 4px;
  border-bottom: 1px solid #f0f2f5;
  cursor: pointer;
  transition: background 0.2s;
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item:hover {
  background: #f5f7fa;
}

.notification-item.unread {
  background: #ecf5ff;
}

.notification-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #409EFF;
  flex-shrink: 0;
}

.notification-title {
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-time {
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 2px;
}

.system-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.system-stat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.system-stat-item .label {
  font-size: 14px;
  color: #606266;
}

.system-stat-item .value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.system-stat-item .value.danger {
  color: #F56C6C;
}

.system-stat-item .value.warning {
  color: #E6A23C;
}

.system-stat-item .el-progress {
  width: 140px;
}

@media (max-width: 768px) {
  .welcome-section {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .quick-actions {
    flex-wrap: wrap;
    justify-content: center;
  }

  .stats-row .el-col {
    margin-bottom: 12px;
  }
}
</style>

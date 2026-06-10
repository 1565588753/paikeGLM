<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">通知中心</h2>
      <el-button @click="markAllRead">
        <el-icon><Check /></el-icon>全部标记已读
      </el-button>
    </div>

    <div class="search-bar">
      <el-radio-group v-model="filterType" @change="filterNotifications">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="unread">未读</el-radio-button>
        <el-radio-button value="read">已读</el-radio-button>
      </el-radio-group>
    </div>

    <div class="notification-list" v-loading="loading">
      <div
        v-for="item in filteredNotifications"
        :key="item.id"
        class="notification-item"
        :class="{ unread: !item.read }"
        @click="readNotification(item)"
      >
        <div class="notification-dot" v-if="!item.read"></div>
        <div class="notification-icon">
          <el-icon :size="20" :color="getIconColor(item.type)">
            <Bell v-if="item.type === 'system'" />
            <Switch v-else-if="item.type === 'swap'" />
            <Warning v-else-if="item.type === 'warning'" />
            <SuccessFilled v-else-if="item.type === 'success'" />
            <InfoFilled v-else />
          </el-icon>
        </div>
        <div class="notification-body">
          <div class="notification-title">{{ item.title }}</div>
          <div class="notification-content">{{ item.content }}</div>
          <div class="notification-meta">
            <span class="notification-time">{{ getRelativeTime(item.createdAt) }}</span>
            <el-tag v-if="item.type" size="small" :type="getTagType(item.type)">{{ getTypeLabel(item.type) }}</el-tag>
          </div>
        </div>
        <div class="notification-actions">
          <el-button text type="danger" size="small" @click.stop="handleDeleteNotification(item)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>

      <el-empty v-if="filteredNotifications.length === 0" description="暂无通知" />
    </div>

    <div class="pagination-wrap" v-if="pagination.total > pagination.pageSize">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        layout="prev, pager, next"
        @current-change="loadData"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useNotificationStore } from '../../stores/notification'
import { deleteNotification as deleteNotificationApi } from '../../api/notification'
import { getRelativeTime } from '../../utils/format'
import { ElMessage, ElMessageBox } from 'element-plus'

const notificationStore = useNotificationStore()
const loading = ref(false)
const filterType = ref('all')
const pagination = ref({ page: 1, pageSize: 20, total: 0 })

const filteredNotifications = computed(() => {
  const list = notificationStore.notifications
  if (filterType.value === 'unread') return list.filter(n => !n.read)
  if (filterType.value === 'read') return list.filter(n => n.read)
  return list
})

function getIconColor(type) {
  const map = { system: '#409EFF', swap: '#E6A23C', warning: '#F56C6C', success: '#67C23A' }
  return map[type] || '#909399'
}

function getTagType(type) {
  const map = { system: 'primary', swap: 'warning', warning: 'danger', success: 'success' }
  return map[type] || 'info'
}

function getTypeLabel(type) {
  const map = { system: '系统', swap: '换课', warning: '警告', success: '成功' }
  return map[type] || '通知'
}

async function readNotification(item) {
  if (!item.read) {
    await notificationStore.readNotification(item.id)
  }
}

async function markAllRead() {
  await notificationStore.readAllNotifications()
  ElMessage.success('已全部标记为已读')
}

async function doDeleteNotification(item) {
  await deleteNotificationApi(item.id)
  const idx = notificationStore.notifications.findIndex(n => n.id === item.id)
  if (idx >= 0) notificationStore.notifications.splice(idx, 1)
  ElMessage.success('已删除')
}

async function handleDeleteNotification(item) {
  try {
    await ElMessageBox.confirm('确定要删除此通知吗？', '确认', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'info' })
    await doDeleteNotification(item)
  } catch (e) { if (e !== 'cancel') console.error('删除失败', e) }
}

function filterNotifications() {}

async function loadData() {
  loading.value = true
  try {
    await notificationStore.fetchNotifications()
  } catch (e) { console.error('加载通知失败', e) } finally { loading.value = false }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.notification-list { display: flex; flex-direction: column; gap: 8px; }
.notification-item {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 16px; background: #fff; border: 1px solid #ebeef5;
  border-radius: 8px; cursor: pointer; transition: all 0.2s;
}
.notification-item:hover { box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06); }
.notification-item.unread { background: #ecf5ff; border-color: #d9ecff; }
.notification-dot { width: 8px; height: 8px; border-radius: 50%; background: #409EFF; flex-shrink: 0; margin-top: 6px; }
.notification-icon { flex-shrink: 0; margin-top: 2px; }
.notification-body { flex: 1; min-width: 0; }
.notification-title { font-size: 15px; font-weight: 600; color: #303133; }
.notification-content { font-size: 13px; color: #606266; margin-top: 4px; line-height: 1.5; }
.notification-meta { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
.notification-time { font-size: 12px; color: #c0c4cc; }
.notification-actions { flex-shrink: 0; }
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>

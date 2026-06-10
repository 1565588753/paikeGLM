import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getNotifications, markAsRead, markAllAsRead } from '../api/notification'

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref([])
  const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)

  async function fetchNotifications() {
    try {
      const res = await getNotifications({ page: 1, pageSize: 50 })
      notifications.value = res.data.list || []
    } catch (e) {
      console.error('获取通知失败', e)
    }
  }

  async function readNotification(id) {
    try {
      await markAsRead(id)
      const n = notifications.value.find(item => item.id === id)
      if (n) n.read = true
    } catch (e) {
      console.error('标记已读失败', e)
    }
  }

  async function readAllNotifications() {
    try {
      await markAllAsRead()
      notifications.value.forEach(n => { n.read = true })
    } catch (e) {
      console.error('全部标记已读失败', e)
    }
  }

  function addNotification(notification) {
    notifications.value.unshift(notification)
  }

  return {
    notifications,
    unreadCount,
    fetchNotifications,
    readNotification,
    readAllNotifications,
    addNotification
  }
})

<template>
  <el-container class="main-layout">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
      <div class="logo-area">
        <el-icon :size="28" color="#409EFF"><MagicStick /></el-icon>
        <span v-show="!isCollapse" class="logo-text">智能排课系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="true"
        router
        background-color="#001529"
        text-color="#ffffffb3"
        active-text-color="#409EFF"
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>首页仪表盘</template>
        </el-menu-item>

        <el-menu-item index="/academic">
          <el-icon><Calendar /></el-icon>
          <template #title>学年管理</template>
        </el-menu-item>

        <el-menu-item index="/classes">
          <el-icon><School /></el-icon>
          <template #title>班级管理</template>
        </el-menu-item>

        <el-menu-item index="/subjects">
          <el-icon><Reading /></el-icon>
          <template #title>科目管理</template>
        </el-menu-item>

        <el-menu-item index="/classrooms">
          <el-icon><House /></el-icon>
          <template #title>教室管理</template>
        </el-menu-item>

        <el-menu-item index="/schedules">
          <el-icon><Clock /></el-icon>
          <template #title>作息时间</template>
        </el-menu-item>

        <el-menu-item index="/teaching">
          <el-icon><UserFilled /></el-icon>
          <template #title>任课安排</template>
        </el-menu-item>

        <el-menu-item index="/auto-schedule">
          <el-icon><MagicStick /></el-icon>
          <template #title>智能排课</template>
        </el-menu-item>

        <el-sub-menu index="timetable-sub">
          <template #title>
            <el-icon><Grid /></el-icon>
            <span>课表查看</span>
          </template>
          <el-menu-item index="/timetable/class">班级课表</el-menu-item>
          <el-menu-item index="/timetable/teacher">教师课表</el-menu-item>
          <el-menu-item index="/timetable/room">教室课表</el-menu-item>
          <el-menu-item index="/timetable/all">全校课表</el-menu-item>
        </el-sub-menu>

        <el-menu-item v-if="userStore.isAdmin" index="/timetable/drag">
          <el-icon><Rank /></el-icon>
          <template #title>拖拽排课</template>
        </el-menu-item>

        <el-menu-item index="/swap">
          <el-icon><Switch /></el-icon>
          <template #title>在线换课</template>
        </el-menu-item>

        <el-menu-item index="/staff">
          <el-icon><Notebook /></el-icon>
          <template #title>人事表</template>
        </el-menu-item>

        <el-menu-item v-if="userStore.isAdmin" index="/users">
          <el-icon><User /></el-icon>
          <template #title>教师管理</template>
        </el-menu-item>

        <el-menu-item v-if="userStore.isAdmin" index="/backup">
          <el-icon><FolderOpened /></el-icon>
          <template #title>数据备份</template>
        </el-menu-item>

        <el-menu-item v-if="userStore.isAdmin" index="/logs">
          <el-icon><Document /></el-icon>
          <template #title>操作日志</template>
        </el-menu-item>

        <el-menu-item v-if="userStore.isAdmin" index="/schedules/mapping">
          <el-icon><Connection /></el-icon>
          <template #title>语数外匹配</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="main-container">
      <el-header class="header">
        <div class="header-left">
          <el-icon
            class="collapse-btn"
            @click="isCollapse = !isCollapse"
            :size="20"
          >
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentRoute.meta?.title">
              {{ currentRoute.meta.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <div class="academic-selector">
            <el-tag type="primary" effect="plain" size="large">
              {{ academicStore.fullLabel || '未设置学年' }}
            </el-tag>
          </div>
          <el-badge :value="notificationStore.unreadCount" :hidden="notificationStore.unreadCount === 0" :max="99" class="notification-badge">
            <el-icon :size="20" class="header-icon" @click="$router.push('/notifications')">
              <Bell />
            </el-icon>
          </el-badge>
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32" class="user-avatar">
                {{ userStore.displayName?.charAt(0) || 'U' }}
              </el-avatar>
              <span class="user-name">{{ userStore.displayName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><Setting /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item command="notifications">
                  <el-icon><Bell /></el-icon>通知中心
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useAcademicStore } from '../stores/academic'
import { useNotificationStore } from '../stores/notification'
import { ElMessageBox, ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const academicStore = useAcademicStore()
const notificationStore = useNotificationStore()

const isCollapse = ref(false)

const activeMenu = computed(() => route.path)
const currentRoute = computed(() => route)

function handleCommand(command) {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'notifications':
      router.push('/notifications')
      break
    case 'logout':
      ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        userStore.logout()
        router.push('/login')
        ElMessage.success('已退出登录')
      }).catch(() => {})
      break
  }
}

onMounted(async () => {
  try {
    await userStore.fetchUserInfo()
    await academicStore.fetchCurrentYear()
    await notificationStore.fetchNotifications()
  } catch (e) {
    console.error('初始化数据失败', e)
  }
})
</script>

<style scoped>
.main-layout {
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  background: #001529;
  overflow-y: auto;
  overflow-x: hidden;
  transition: width 0.3s;
  box-shadow: 2px 0 6px rgba(0, 21, 41, 0.35);
}

.sidebar::-webkit-scrollbar {
  width: 0;
}

.logo-area {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0 16px;
  border-bottom: 1px solid #ffffff1a;
}

.logo-text {
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
}

.sidebar-menu {
  border-right: none;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 220px;
}

:deep(.el-menu-item.is-active) {
  background-color: #409EFF1a !important;
}

:deep(.el-sub-menu .el-menu-item) {
  padding-left: 52px !important;
  min-width: auto;
}

.main-container {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  color: #606266;
  transition: color 0.2s;
}

.collapse-btn:hover {
  color: #409EFF;
}

.breadcrumb {
  line-height: 60px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.academic-selector {
  display: flex;
  align-items: center;
}

.notification-badge {
  display: flex;
  align-items: center;
}

.header-icon {
  cursor: pointer;
  color: #606266;
  transition: color 0.2s;
}

.header-icon:hover {
  color: #409EFF;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.user-info:hover {
  background: #f5f7fa;
}

.user-avatar {
  background: #409EFF;
  color: #fff;
  font-size: 14px;
}

.user-name {
  font-size: 14px;
  color: #303133;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  background: #f0f2f5;
  padding: 20px;
}

@media (max-width: 768px) {
  .header {
    padding: 0 12px;
  }

  .breadcrumb {
    display: none;
  }

  .academic-selector {
    display: none;
  }

  .user-name {
    display: none;
  }

  .main-content {
    padding: 12px;
  }
}
</style>

import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '../utils/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录', noAuth: true }
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '首页仪表盘', icon: 'Odometer' }
      },
      {
        path: 'academic',
        name: 'AcademicYear',
        component: () => import('../views/academic/YearManagement.vue'),
        meta: { title: '学年管理', icon: 'Calendar' }
      },
      {
        path: 'academic/semester',
        name: 'SemesterManagement',
        component: () => import('../views/academic/SemesterManagement.vue'),
        meta: { title: '学期管理', icon: 'Date' }
      },
      {
        path: 'classes',
        name: 'ClassManagement',
        component: () => import('../views/class/ClassManagement.vue'),
        meta: { title: '班级管理', icon: 'School' }
      },
      {
        path: 'subjects',
        name: 'SubjectManagement',
        component: () => import('../views/subject/SubjectManagement.vue'),
        meta: { title: '科目管理', icon: 'Reading' }
      },
      {
        path: 'classrooms',
        name: 'ClassroomManagement',
        component: () => import('../views/classroom/ClassroomManagement.vue'),
        meta: { title: '教室管理', icon: 'House' }
      },
      {
        path: 'schedules',
        name: 'ScheduleTemplate',
        component: () => import('../views/schedule/ScheduleTemplate.vue'),
        meta: { title: '作息时间', icon: 'Clock' }
      },
      {
        path: 'schedules/editor/:id',
        name: 'TimeSlotEditor',
        component: () => import('../views/schedule/TimeSlotEditor.vue'),
        meta: { title: '时间段编辑', icon: 'Timer' }
      },
      {
        path: 'schedules/mapping',
        name: 'SubjectSubMapping',
        component: () => import('../views/schedule/SubjectSubMapping.vue'),
        meta: { title: '语数外匹配', icon: 'Connection', adminOnly: true }
      },
      {
        path: 'teaching',
        name: 'TeachingAssignment',
        component: () => import('../views/teaching/TeachingAssignment.vue'),
        meta: { title: '任课安排', icon: 'UserFilled' }
      },
      {
        path: 'auto-schedule',
        name: 'AutoSchedule',
        component: () => import('../views/timetable/AutoSchedule.vue'),
        meta: { title: '智能排课', icon: 'MagicStick' }
      },
      {
        path: 'timetable/class',
        name: 'ClassTimetable',
        component: () => import('../views/timetable/ClassTimetable.vue'),
        meta: { title: '班级课表', icon: 'Grid' }
      },
      {
        path: 'timetable/teacher',
        name: 'TeacherTimetable',
        component: () => import('../views/timetable/TeacherTimetable.vue'),
        meta: { title: '教师课表', icon: 'Avatar' }
      },
      {
        path: 'timetable/room',
        name: 'RoomTimetable',
        component: () => import('../views/timetable/RoomTimetable.vue'),
        meta: { title: '教室课表', icon: 'OfficeBuilding' }
      },
      {
        path: 'timetable/all',
        name: 'AllClassView',
        component: () => import('../views/timetable/AllClassView.vue'),
        meta: { title: '全校课表', icon: 'DataBoard' }
      },
      {
        path: 'timetable/drag',
        name: 'DragSchedule',
        component: () => import('../views/timetable/DragSchedule.vue'),
        meta: { title: '拖拽排课', icon: 'Rank', adminOnly: true }
      },
      {
        path: 'swap',
        name: 'SwapList',
        component: () => import('../views/swap/SwapList.vue'),
        meta: { title: '换课列表', icon: 'Switch' }
      },
      {
        path: 'swap/request',
        name: 'SwapRequest',
        component: () => import('../views/swap/SwapRequest.vue'),
        meta: { title: '申请换课', icon: 'Promotion' }
      },
      {
        path: 'swap/history',
        name: 'SwapHistory',
        component: () => import('../views/swap/SwapHistory.vue'),
        meta: { title: '换课记录', icon: 'Finished' }
      },
      {
        path: 'staff',
        name: 'StaffTable',
        component: () => import('../views/staff/StaffTable.vue'),
        meta: { title: '人事表', icon: 'Notebook' }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: () => import('../views/user/UserManagement.vue'),
        meta: { title: '教师管理', icon: 'User', adminOnly: true }
      },
      {
        path: 'backup',
        name: 'BackupManagement',
        component: () => import('../views/backup/BackupManagement.vue'),
        meta: { title: '数据备份', icon: 'FolderOpened', adminOnly: true }
      },
      {
        path: 'logs',
        name: 'OperationLog',
        component: () => import('../views/log/OperationLog.vue'),
        meta: { title: '操作日志', icon: 'Document', adminOnly: true }
      },
      {
        path: 'notifications',
        name: 'NotificationCenter',
        component: () => import('../views/notification/NotificationCenter.vue'),
        meta: { title: '通知中心', icon: 'Bell' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/profile/Profile.vue'),
        meta: { title: '个人中心', icon: 'Setting' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 智能排课系统` : '智能排课系统'
  if (to.meta.noAuth) {
    next()
  } else {
    const token = getToken()
    if (token) {
      next()
    } else {
      next({ path: '/login', query: { redirect: to.fullPath } })
    }
  }
})

export default router

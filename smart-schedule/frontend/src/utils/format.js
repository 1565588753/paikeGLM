import dayjs from 'dayjs'

export function formatDate(date, format = 'YYYY-MM-DD') {
  if (!date) return ''
  return dayjs(date).format(format)
}

export function formatDateTime(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return ''
  return dayjs(date).format(format)
}

export function formatTime(date, format = 'HH:mm') {
  if (!date) return ''
  return dayjs(date).format(format)
}

export function getWeekDay(date) {
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return days[dayjs(date).day()]
}

export function getDayOfWeek(index) {
  const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return days[index] || ''
}

export function getRelativeTime(date) {
  const now = dayjs()
  const target = dayjs(date)
  const diffMin = now.diff(target, 'minute')
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  const diffHour = now.diff(target, 'hour')
  if (diffHour < 24) return `${diffHour}小时前`
  const diffDay = now.diff(target, 'day')
  if (diffDay < 30) return `${diffDay}天前`
  return formatDate(date)
}

export const SUBJECT_COLORS = [
  '#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399',
  '#00BCD4', '#9C27B0', '#FF9800', '#4CAF50', '#E91E63',
  '#3F51B5', '#009688', '#FF5722', '#607D8B', '#795548',
  '#CDDC39', '#8BC34A', '#FFC107', '#03A9F4', '#FF4081'
]

export function getSubjectColor(index) {
  return SUBJECT_COLORS[index % SUBJECT_COLORS.length]
}

export function getSubjectColorByName(name) {
  const colorMap = {
    '语文': '#E6A23C',
    '数学': '#409EFF',
    '英语': '#67C23A',
    '物理': '#F56C6C',
    '化学': '#9C27B0',
    '生物': '#4CAF50',
    '历史': '#795548',
    '地理': '#00BCD4',
    '政治': '#E91E63',
    '体育': '#FF9800',
    '音乐': '#FF4081',
    '美术': '#3F51B5',
    '信息技术': '#607D8B',
    '综合实践': '#CDDC39',
    '劳动': '#8BC34A',
    '校本': '#FFC107',
    '自习': '#909399',
    '班会': '#03A9F4',
    '阅读': '#009688'
  }
  return colorMap[name] || SUBJECT_COLORS[Object.keys(colorMap).length % SUBJECT_COLORS.length]
}

export function formatWeekType(type) {
  const map = { all: '全周', odd: '单周', even: '双周' }
  return map[type] || type
}

export function formatRole(role) {
  const map = { admin: '管理员', teacher: '教师' }
  return map[role] || role
}

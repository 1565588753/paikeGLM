import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getUserInfo } from '../api/auth'
import { getToken, setToken, removeToken } from '../utils/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(getToken() || '')
  const userInfo = ref({
    id: null,
    username: '',
    name: '',
    role: '',
    avatar: ''
  })

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value.role === 'admin')
  const isTeacher = computed(() => userInfo.value.role === 'teacher')
  const displayName = computed(() => userInfo.value.name || userInfo.value.username)

  async function login(loginForm) {
    const res = await loginApi(loginForm)
    // 后端返回格式: { access_token, token_type, user: { real_name, ... } }
    // res.data 是经过 API 拦截器包装后的 { code, data: {...} }
    const rawData = res.data ? res.data : res
    const token = rawData.token || rawData.access_token
    const user = rawData.user || {}
    token.value = token
    setToken(token)
    userInfo.value = {
      id: user.id,
      username: user.username,
      name: user.name || user.real_name || user.username,
      role: user.role,
      avatar: user.avatar || ''
    }
    return rawData
  }

  async function fetchUserInfo() {
    const res = await getUserInfo()
    const rawData = res.data ? res.data : res
    userInfo.value = {
      id: rawData.id,
      username: rawData.username,
      name: rawData.name || rawData.real_name || rawData.username,
      role: rawData.role,
      avatar: rawData.avatar || ''
    }
    return rawData
  }

  function logout() {
    token.value = ''
    userInfo.value = { id: null, username: '', name: '', role: '', avatar: '' }
    removeToken()
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    isAdmin,
    isTeacher,
    displayName,
    login,
    fetchUserInfo,
    logout
  }
})

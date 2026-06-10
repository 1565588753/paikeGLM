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
    const data = res.data
    token.value = data.token
    setToken(data.token)
    userInfo.value = data.user
    return data
  }

  async function fetchUserInfo() {
    const res = await getUserInfo()
    userInfo.value = res.data
    return res.data
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

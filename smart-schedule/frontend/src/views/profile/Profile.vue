<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">个人中心</h2>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <span class="card-title">基本信息</span>
          </template>
          <div class="profile-info">
            <div class="avatar-section">
              <el-avatar :size="80" class="profile-avatar">
                {{ userStore.displayName?.charAt(0) || 'U' }}
              </el-avatar>
              <div class="avatar-text">
                <h3>{{ userStore.displayName }}</h3>
                <el-tag :type="userStore.isAdmin ? 'danger' : 'primary'">
                  {{ userStore.isAdmin ? '管理员' : '教师' }}
                </el-tag>
              </div>
            </div>

            <el-form :model="profileForm" label-width="80px" style="margin-top: 24px;">
              <el-form-item label="工号">
                <el-input :value="userStore.userInfo.username" disabled />
              </el-form-item>
              <el-form-item label="姓名">
                <el-input v-model="profileForm.name" />
              </el-form-item>
              <el-form-item label="性别">
                <el-radio-group v-model="profileForm.gender">
                  <el-radio value="男">男</el-radio>
                  <el-radio value="女">女</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="手机号">
                <el-input v-model="profileForm.phone" />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input v-model="profileForm.email" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="profileLoading" @click="saveProfile">保存修改</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <span class="card-title">修改密码</span>
          </template>
          <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="100px">
            <el-form-item label="当前密码" prop="oldPassword">
              <el-input v-model="passwordForm.oldPassword" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="passwordForm.newPassword" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="passwordLoading" @click="changePassword">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="hover" style="margin-top: 20px;">
          <template #header>
            <span class="card-title">快捷操作</span>
          </template>
          <div class="quick-links">
            <el-button @click="$router.push('/timetable/teacher')">查看我的课表</el-button>
            <el-button @click="$router.push('/swap/request')">申请换课</el-button>
            <el-button @click="$router.push('/swap')">换课记录</el-button>
            <el-button @click="$router.push('/notifications')">通知中心</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useUserStore } from '../../stores/user'
import { changePassword as changePasswordApi } from '../../api/auth'
import request from '../../api/index'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const profileLoading = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref(null)

const profileForm = reactive({
  name: '',
  gender: '男',
  phone: '',
  email: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirm = (rule, value, callback) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ]
}

async function saveProfile() {
  profileLoading.value = true
  try {
    await request.put(`/users/${userStore.userInfo.id}`, profileForm)
    await userStore.fetchUserInfo()
    ElMessage.success('保存成功')
  } catch (e) { ElMessage.error('保存失败') } finally { profileLoading.value = false }
}

async function changePassword() {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    passwordLoading.value = true
    try {
      await changePasswordApi({
        oldPassword: passwordForm.oldPassword,
        newPassword: passwordForm.newPassword
      })
      ElMessage.success('密码修改成功，请重新登录')
      passwordForm.oldPassword = ''
      passwordForm.newPassword = ''
      passwordForm.confirmPassword = ''
    } catch (e) { ElMessage.error('密码修改失败') } finally { passwordLoading.value = false }
  })
}

onMounted(() => {
  profileForm.name = userStore.userInfo.name || ''
  profileForm.gender = userStore.userInfo.gender || '男'
  profileForm.phone = userStore.userInfo.phone || ''
  profileForm.email = userStore.userInfo.email || ''
})
</script>

<style scoped>
.card-title { font-size: 16px; font-weight: 600; color: #303133; }
.profile-info { padding: 8px 0; }
.avatar-section { display: flex; align-items: center; gap: 20px; }
.profile-avatar { background: #409EFF; color: #fff; font-size: 28px; }
.avatar-text h3 { font-size: 20px; font-weight: 600; color: #303133; margin-bottom: 4px; }
.quick-links { display: flex; flex-wrap: wrap; gap: 10px; }
</style>

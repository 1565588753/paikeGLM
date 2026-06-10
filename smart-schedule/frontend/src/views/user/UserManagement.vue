<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">教师管理</h2>
      <div>
        <el-button @click="handleImport">
          <el-icon><Upload /></el-icon>导入
        </el-button>
        <el-button @click="handleExport">
          <el-icon><Download /></el-icon>导出
        </el-button>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>添加教师
        </el-button>
      </div>
    </div>

    <div class="search-bar">
      <el-input v-model="searchKeyword" placeholder="搜索姓名/工号" clearable @clear="loadData" @keyup.enter="loadData" style="width: 200px;">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="searchRole" placeholder="角色" clearable @change="loadData" style="width: 120px;">
        <el-option label="管理员" value="admin" />
        <el-option label="教师" value="teacher" />
      </el-select>
    </div>

    <el-table :data="users" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="username" label="工号" width="120" />
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column prop="role" label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'" size="small">
            {{ row.role === 'admin' ? '管理员' : '教师' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="gender" label="性别" width="70" />
      <el-table-column prop="phone" label="手机号" width="130" />
      <el-table-column prop="email" label="邮箱" min-width="160" />
      <el-table-column prop="subjects" label="任教科目" min-width="120" />
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
            {{ row.status === 'active' ? '在职' : '离职' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="showEditDialog(row)">
            <el-icon><Edit /></el-icon>编辑
          </el-button>
          <el-button size="small" text type="warning" @click="handleResetPassword(row)">
            <el-icon><Key /></el-icon>重置密码
          </el-button>
          <el-button size="small" text type="danger" @click="handleDelete(row)">
            <el-icon><Delete /></el-icon>删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadData"
        @current-change="loadData"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑教师' : '添加教师'" width="500px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="80px">
        <el-form-item label="工号" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="form.password" type="password" show-password placeholder="初始密码" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%;">
            <el-option label="管理员" value="admin" />
            <el-option label="教师" value="teacher" />
          </el-select>
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-radio-group v-model="form.gender">
            <el-radio value="男">男</el-radio>
            <el-radio value="女">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDialogVisible" title="导入教师" width="450px">
      <el-upload drag :auto-upload="false" accept=".xlsx,.xls" :limit="1" :on-change="handleFileChange">
        <el-icon :size="40" style="color: #c0c4cc;"><Upload /></el-icon>
        <div style="margin-top: 8px;">将Excel文件拖到此处，或<em>点击上传</em></div>
      </el-upload>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="importLoading" @click="confirmImport">确认导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getUsers, createUser, updateUser, deleteUser, resetPassword, importUsers } from '../../api/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { exportToExcel, importFromExcel } from '../../utils/excel'

const loading = ref(false)
const submitLoading = ref(false)
const importLoading = ref(false)
const users = ref([])
const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const importFile = ref(null)
const searchKeyword = ref('')
const searchRole = ref('')
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  username: '', name: '', password: '', role: 'teacher', gender: '男', phone: '', email: ''
})

const formRules = {
  username: [{ required: true, message: '请输入工号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

async function loadData() {
  loading.value = true
  try {
    const res = await getUsers({
      page: pagination.page, pageSize: pagination.pageSize,
      keyword: searchKeyword.value || undefined, role: searchRole.value || undefined
    })
    users.value = res.data?.list || res.data || []
    pagination.total = res.data?.total || 0
  } catch (e) { console.error('加载用户数据失败', e) } finally { loading.value = false }
}

function showCreateDialog() {
  isEdit.value = false; editingId.value = null
  Object.assign(form, { username: '', name: '', password: '', role: 'teacher', gender: '男', phone: '', email: '' })
  dialogVisible.value = true
}

function showEditDialog(row) {
  isEdit.value = true; editingId.value = row.id
  Object.assign(form, { username: row.username, name: row.name, password: '', role: row.role, gender: row.gender || '男', phone: row.phone || '', email: row.email || '' })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (isEdit.value) { await updateUser(editingId.value, form); ElMessage.success('更新成功') }
      else { await createUser(form); ElMessage.success('创建成功') }
      dialogVisible.value = false; loadData()
    } catch (e) { console.error('操作失败', e) } finally { submitLoading.value = false }
  })
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除用户"${row.name}"吗？`, '警告', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    await deleteUser(row.id); ElMessage.success('删除成功'); loadData()
  } catch (e) { if (e !== 'cancel') console.error('删除失败', e) }
}

async function handleResetPassword(row) {
  try {
    await ElMessageBox.confirm(`确定要重置"${row.name}"的密码吗？`, '确认', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    await resetPassword(row.id); ElMessage.success('密码已重置为默认密码')
  } catch (e) { if (e !== 'cancel') console.error('重置失败', e) }
}

function handleFileChange(file) { importFile.value = file.raw }
function handleImport() { importFile.value = null; importDialogVisible.value = true }

async function confirmImport() {
  if (!importFile.value) { ElMessage.warning('请选择文件'); return }
  importLoading.value = true
  try {
    const { headers, rows } = await importFromExcel(importFile.value)
    const data = rows.map(row => { const obj = {}; headers.forEach((h, i) => { obj[h] = row[i] }); return obj })
    await importUsers(data); ElMessage.success('导入成功'); importDialogVisible.value = false; loadData()
  } catch (e) { ElMessage.error(e.message || '导入失败') } finally { importLoading.value = false }
}

function handleExport() {
  exportToExcel(users.value, [
    { prop: 'username', label: '工号' }, { prop: 'name', label: '姓名' },
    { prop: 'role', label: '角色', formatter: row => row.role === 'admin' ? '管理员' : '教师' },
    { prop: 'phone', label: '手机号' }, { prop: 'email', label: '邮箱' }
  ], '教师数据')
}

onMounted(() => { loadData() })
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>

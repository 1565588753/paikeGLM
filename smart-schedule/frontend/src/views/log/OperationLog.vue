<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">操作日志</h2>
      <el-button type="danger" @click="handleClearLogs" v-if="userStore.isAdmin">
        <el-icon><Delete /></el-icon>清理日志
      </el-button>
    </div>

    <div class="search-bar">
      <el-select v-model="searchModule" placeholder="操作模块" clearable @change="loadData" style="width: 150px;">
        <el-option label="登录" value="auth" />
        <el-option label="学年管理" value="academic" />
        <el-option label="班级管理" value="class" />
        <el-option label="科目管理" value="subject" />
        <el-option label="教室管理" value="classroom" />
        <el-option label="任课安排" value="teaching" />
        <el-option label="排课" value="schedule" />
        <el-option label="换课" value="swap" />
        <el-option label="用户管理" value="user" />
        <el-option label="备份" value="backup" />
      </el-select>
      <el-select v-model="searchAction" placeholder="操作类型" clearable @change="loadData" style="width: 130px;">
        <el-option label="创建" value="create" />
        <el-option label="更新" value="update" />
        <el-option label="删除" value="delete" />
        <el-option label="登录" value="login" />
        <el-option label="导出" value="export" />
        <el-option label="导入" value="import" />
      </el-select>
      <el-input v-model="searchUser" placeholder="操作人" clearable @clear="loadData" @keyup.enter="loadData" style="width: 150px;">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        @change="loadData"
        style="width: 280px;"
      />
    </div>

    <el-table :data="logs" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="operatorName" label="操作人" width="100" />
      <el-table-column prop="module" label="模块" width="110">
        <template #default="{ row }">
          <el-tag size="small">{{ getModuleLabel(row.module) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="action" label="操作" width="80">
        <template #default="{ row }">
          <el-tag :type="getActionType(row.action)" size="small">{{ getActionLabel(row.action) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="target" label="操作对象" min-width="160" show-overflow-tooltip />
      <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip />
      <el-table-column prop="ip" label="IP地址" width="130" />
      <el-table-column prop="createdAt" label="时间" width="170" />
    </el-table>

    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadData"
        @current-change="loadData"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useUserStore } from '../../stores/user'
import { getOperationLogs, clearLogs } from '../../api/export'
import { ElMessage, ElMessageBox } from 'element-plus'

const userStore = useUserStore()
const loading = ref(false)
const logs = ref([])
const searchModule = ref('')
const searchAction = ref('')
const searchUser = ref('')
const dateRange = ref(null)
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const moduleLabels = {
  auth: '登录', academic: '学年管理', class: '班级管理', subject: '科目管理',
  classroom: '教室管理', teaching: '任课安排', schedule: '排课', swap: '换课',
  user: '用户管理', backup: '备份'
}

const actionLabels = { create: '创建', update: '更新', delete: '删除', login: '登录', export: '导出', import: '导入' }

function getModuleLabel(m) { return moduleLabels[m] || m }
function getActionLabel(a) { return actionLabels[a] || a }
function getActionType(a) {
  const map = { create: 'success', update: 'primary', delete: 'danger', login: 'info', export: 'warning', import: 'warning' }
  return map[a] || 'info'
}

async function loadData() {
  loading.value = true
  try {
    const params = {
      page: pagination.page, pageSize: pagination.pageSize,
      module: searchModule.value || undefined,
      action: searchAction.value || undefined,
      operator: searchUser.value || undefined
    }
    if (dateRange.value && dateRange.value.length === 2) {
      params.startDate = dateRange.value[0]
      params.endDate = dateRange.value[1]
    }
    const res = await getOperationLogs(params)
    logs.value = res.data?.list || res.data || []
    pagination.total = res.data?.total || 0
  } catch (e) { console.error('加载日志失败', e) } finally { loading.value = false }
}

async function handleClearLogs() {
  try {
    const { value } = await ElMessageBox.prompt('请输入清理日期（将删除此日期之前的日志，格式：YYYY-MM-DD）', '清理日志', {
      confirmButtonText: '确定清理', cancelButtonText: '取消', inputPlaceholder: '2024-01-01'
    })
    await clearLogs(value)
    ElMessage.success('日志清理完成'); loadData()
  } catch (e) { if (e !== 'cancel') console.error('清理失败', e) }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">数据备份</h2>
      <el-button type="primary" @click="createNewBackup">
        <el-icon><Plus /></el-icon>创建备份
      </el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon style="margin-bottom: 20px;">
      <template #title>定期备份数据可以防止意外数据丢失。建议在每次大规模操作（如排课、学年切换）前后创建备份。</template>
    </el-alert>

    <el-table :data="backups" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="id" label="编号" width="70" />
      <el-table-column prop="name" label="备份名称" min-width="200" />
      <el-table-column prop="createdAt" label="创建时间" width="180" />
      <el-table-column prop="size" label="大小" width="100">
        <template #default="{ row }">{{ formatSize(row.size) }}</template>
      </el-table-column>
      <el-table-column prop="type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.type === 'auto' ? 'info' : 'primary'" size="small">
            {{ row.type === 'auto' ? '自动' : '手动' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip />
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="downloadBackupFile(row)">
            <el-icon><Download /></el-icon>下载
          </el-button>
          <el-button size="small" text type="warning" @click="restoreFromBackup(row)">
            <el-icon><RefreshRight /></el-icon>恢复
          </el-button>
          <el-button size="small" text type="danger" @click="handleDeleteBackup(row)">
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

    <el-dialog v-model="uploadDialogVisible" title="上传备份文件" width="450px">
      <el-upload drag :auto-upload="false" accept=".sql,.zip,.bak" :limit="1" :on-change="handleFileChange">
        <el-icon :size="40" style="color: #c0c4cc;"><Upload /></el-icon>
        <div style="margin-top: 8px;">将备份文件拖到此处，或<em>点击上传</em></div>
      </el-upload>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploadLoading" @click="confirmUpload">确认上传</el-button>
      </template>
    </el-dialog>

    <div style="margin-top: 20px;">
      <el-button @click="uploadDialogVisible = true">
        <el-icon><Upload /></el-icon>上传备份文件
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getBackups, createBackup, restoreBackup, deleteBackup as deleteBackupApi, downloadBackup as downloadBackupApi, uploadBackup } from '../../api/backup'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const uploadLoading = ref(false)
const backups = ref([])
const uploadDialogVisible = ref(false)
const uploadFile = ref(null)
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++ }
  return size.toFixed(1) + ' ' + units[i]
}

async function loadData() {
  loading.value = true
  try {
    const res = await getBackups({ page: pagination.page, pageSize: pagination.pageSize })
    backups.value = res.data?.list || res.data || []
    pagination.total = res.data?.total || 0
  } catch (e) { console.error('加载备份列表失败', e) } finally { loading.value = false }
}

async function createNewBackup() {
  try {
    const { value: name } = await ElMessageBox.prompt('请输入备份名称', '创建备份', {
      confirmButtonText: '创建', cancelButtonText: '取消',
      inputPlaceholder: '例如：排课前备份',
      inputValue: `手动备份 ${new Date().toLocaleString()}`
    })
    await createBackup({ name })
    ElMessage.success('备份创建成功'); loadData()
  } catch (e) { if (e !== 'cancel') console.error('创建备份失败', e) }
}

async function restoreFromBackup(row) {
  try {
    await ElMessageBox.confirm(
      `确定要从备份"${row.name}"恢复数据吗？当前数据将被覆盖，此操作不可撤销！`,
      '危险操作',
      { confirmButtonText: '确认恢复', cancelButtonText: '取消', type: 'error' }
    )
    await restoreBackup(row.id)
    ElMessage.success('数据恢复成功'); loadData()
  } catch (e) { if (e !== 'cancel') console.error('恢复失败', e) }
}

async function doDeleteBackup(row) {
  await deleteBackupApi(row.id)
  ElMessage.success('删除成功'); loadData()
}

async function handleDeleteBackup(row) {
  try {
    await ElMessageBox.confirm(`确定要删除备份"${row.name}"吗？`, '警告', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    await doDeleteBackup(row)
  } catch (e) { if (e !== 'cancel') console.error('删除失败', e) }
}

async function downloadBackupFile(row) {
  try {
    const res = await downloadBackupApi(row.id)
    const url = window.URL.createObjectURL(new Blob([res]))
    const link = document.createElement('a')
    link.href = url; link.setAttribute('download', `${row.name}.bak`)
    document.body.appendChild(link); link.click(); document.body.removeChild(link)
  } catch (e) { ElMessage.error('下载失败') }
}

function handleFileChange(file) { uploadFile.value = file.raw }

async function confirmUpload() {
  if (!uploadFile.value) { ElMessage.warning('请选择文件'); return }
  uploadLoading.value = true
  try {
    await uploadBackup({ file: uploadFile.value })
    ElMessage.success('上传成功'); uploadDialogVisible.value = false; loadData()
  } catch (e) { ElMessage.error('上传失败') } finally { uploadLoading.value = false }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>

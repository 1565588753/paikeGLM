<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">人事表管理</h2>
      <div>
        <el-button @click="handleSync">
          <el-icon><Refresh /></el-icon>同步任课数据
        </el-button>
        <el-button @click="handleImport">
          <el-icon><Upload /></el-icon>导入
        </el-button>
        <el-button @click="handleExport">
          <el-icon><Download /></el-icon>导出
        </el-button>
        <el-button type="primary" @click="addRow">
          <el-icon><Plus /></el-icon>添加行
        </el-button>
      </div>
    </div>

    <div class="search-bar">
      <el-select v-model="searchGrade" placeholder="筛选年级" clearable @change="loadData" style="width: 130px;">
        <el-option v-for="g in grades" :key="g" :label="g + '年级'" :value="g" />
      </el-select>
      <el-select v-model="searchSubject" placeholder="筛选科目" clearable @change="loadData" style="width: 130px;">
        <el-option label="语文" value="语文" />
        <el-option label="数学" value="数学" />
        <el-option label="英语" value="英语" />
        <el-option label="物理" value="物理" />
        <el-option label="化学" value="化学" />
        <el-option label="生物" value="生物" />
        <el-option label="历史" value="历史" />
        <el-option label="地理" value="地理" />
        <el-option label="政治" value="政治" />
        <el-option label="体育" value="体育" />
        <el-option label="音乐" value="音乐" />
        <el-option label="美术" value="美术" />
      </el-select>
    </div>

    <el-table :data="staffData" v-loading="loading" stripe border style="width: 100%" :row-class-name="tableRowClassName">
      <el-table-column prop="grade" label="年级" width="80">
        <template #default="{ row }">
          <el-input v-if="row.editing" v-model="row.grade" size="small" />
          <span v-else>{{ row.grade }}年级</span>
        </template>
      </el-table-column>
      <el-table-column prop="className" label="班级" width="120">
        <template #default="{ row }">
          <el-input v-if="row.editing" v-model="row.className" size="small" />
          <span v-else>{{ row.className }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="subject" label="科目" width="100">
        <template #default="{ row }">
          <el-input v-if="row.editing" v-model="row.subject" size="small" />
          <span v-else>{{ row.subject }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="teacher" label="教师" width="100">
        <template #default="{ row }">
          <el-input v-if="row.editing" v-model="row.teacher" size="small" />
          <span v-else>{{ row.teacher }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="weeklyHours" label="周课时" width="80">
        <template #default="{ row }">
          <el-input-number v-if="row.editing" v-model="row.weeklyHours" size="small" :min="1" :max="20" controls-position="right" />
          <span v-else>{{ row.weeklyHours }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="weekType" label="单/双周" width="90">
        <template #default="{ row }">
          <el-select v-if="row.editing" v-model="row.weekType" size="small">
            <el-option label="全周" value="all" />
            <el-option label="单周" value="odd" />
            <el-option label="双周" value="even" />
          </el-select>
          <el-tag v-else :type="row.weekType === 'odd' ? 'primary' : (row.weekType === 'even' ? 'warning' : 'info')" size="small">
            {{ row.weekType === 'odd' ? '单周' : (row.weekType === 'even' ? '双周' : '全周') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="notes" label="备注" min-width="140">
        <template #default="{ row }">
          <el-input v-if="row.editing" v-model="row.notes" size="small" />
          <span v-else>{{ row.notes }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <template v-if="row.editing">
            <el-button size="small" type="success" text @click="saveRow(row)">保存</el-button>
            <el-button size="small" text @click="cancelEdit(row)">取消</el-button>
          </template>
          <template v-else>
            <el-button size="small" text type="primary" @click="editRow(row)">
              <el-icon><Edit /></el-icon>编辑
            </el-button>
            <el-button size="small" text type="danger" @click="deleteRow(row)">
              <el-icon><Delete /></el-icon>删除
            </el-button>
          </template>
        </template>
      </el-table-column>
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

    <el-dialog v-model="importDialogVisible" title="导入人事表" width="450px">
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
import { getStaffTable, createStaffEntry, updateStaffEntry, deleteStaffEntry, importStaff, syncFromTeaching } from '../../api/staff'
import { ElMessage, ElMessageBox } from 'element-plus'
import { exportToExcel, importFromExcel } from '../../utils/excel'

const loading = ref(false)
const importLoading = ref(false)
const staffData = ref([])
const importDialogVisible = ref(false)
const importFile = ref(null)
const searchGrade = ref('')
const searchSubject = ref('')
const grades = [1, 2, 3, 4, 5, 6, 7, 8, 9]
const pagination = reactive({ page: 1, pageSize: 50, total: 0 })

function tableRowClassName({ row }) {
  return row.editing ? 'editing-row' : ''
}

async function loadData() {
  loading.value = true
  try {
    const res = await getStaffTable({
      page: pagination.page, pageSize: pagination.pageSize,
      grade: searchGrade.value || undefined, subject: searchSubject.value || undefined
    })
    staffData.value = (res.data?.list || res.data || []).map(r => ({ ...r, editing: false, _original: { ...r } }))
    pagination.total = res.data?.total || 0
  } catch (e) { console.error('加载人事表失败', e) } finally { loading.value = false }
}

function addRow() {
  staffData.value.unshift({ id: null, grade: '', className: '', subject: '', teacher: '', weeklyHours: 4, weekType: 'all', notes: '', editing: true, _original: {} })
}

function editRow(row) {
  row._original = { ...row }
  row.editing = true
}

function cancelEdit(row) {
  if (!row.id) {
    const idx = staffData.value.indexOf(row)
    if (idx >= 0) staffData.value.splice(idx, 1)
  } else {
    Object.assign(row, row._original)
    row.editing = false
  }
}

async function saveRow(row) {
  try {
    if (row.id) {
      await updateStaffEntry(row.id, row)
      ElMessage.success('保存成功')
    } else {
      const res = await createStaffEntry(row)
      row.id = res.data?.id
      ElMessage.success('添加成功')
    }
    row.editing = false
  } catch (e) { ElMessage.error('保存失败') }
}

async function deleteRow(row) {
  try {
    await ElMessageBox.confirm('确定要删除此条记录吗？', '警告', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    if (row.id) await deleteStaffEntry(row.id)
    const idx = staffData.value.indexOf(row)
    if (idx >= 0) staffData.value.splice(idx, 1)
    ElMessage.success('删除成功')
  } catch (e) { if (e !== 'cancel') console.error('删除失败', e) }
}

async function handleSync() {
  try {
    await syncFromTeaching()
    ElMessage.success('同步成功'); loadData()
  } catch (e) { ElMessage.error('同步失败') }
}

function handleFileChange(file) { importFile.value = file.raw }
function handleImport() { importFile.value = null; importDialogVisible.value = true }

async function confirmImport() {
  if (!importFile.value) { ElMessage.warning('请选择文件'); return }
  importLoading.value = true
  try {
    const { headers, rows } = await importFromExcel(importFile.value)
    const data = rows.map(row => { const obj = {}; headers.forEach((h, i) => { obj[h] = row[i] }); return obj })
    await importStaff(data); ElMessage.success('导入成功'); importDialogVisible.value = false; loadData()
  } catch (e) { ElMessage.error(e.message || '导入失败') } finally { importLoading.value = false }
}

function handleExport() {
  exportToExcel(staffData.value, [
    { prop: 'grade', label: '年级' }, { prop: 'className', label: '班级' },
    { prop: 'subject', label: '科目' }, { prop: 'teacher', label: '教师' },
    { prop: 'weeklyHours', label: '周课时' }, { prop: 'weekType', label: '单/双周' },
    { prop: 'notes', label: '备注' }
  ], '人事表')
}

onMounted(() => { loadData() })
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
:deep(.editing-row) { background: #ecf5ff !important; }
</style>

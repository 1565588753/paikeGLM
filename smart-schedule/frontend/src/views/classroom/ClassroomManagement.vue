<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">教室管理</h2>
      <div>
        <el-button @click="handleImport">
          <el-icon><Upload /></el-icon>导入
        </el-button>
        <el-button @click="handleExport">
          <el-icon><Download /></el-icon>导出
        </el-button>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>新建教室
        </el-button>
      </div>
    </div>

    <div class="search-bar">
      <el-select v-model="searchType" placeholder="教室类型" clearable @change="loadData" style="width: 150px;">
        <el-option label="普通教室" value="normal" />
        <el-option label="实验室" value="lab" />
        <el-option label="多媒体教室" value="multimedia" />
        <el-option label="音乐教室" value="music" />
        <el-option label="美术教室" value="art" />
        <el-option label="体育馆" value="gym" />
      </el-select>
      <el-input v-model="searchKeyword" placeholder="搜索教室名称/编号" clearable @clear="loadData" @keyup.enter="loadData" style="width: 200px;">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
    </div>

    <el-table :data="classrooms" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="name" label="教室名称" min-width="140" />
      <el-table-column prop="code" label="教室编号" width="120" />
      <el-table-column prop="building" label="所在楼栋" width="120" />
      <el-table-column prop="floor" label="楼层" width="80" />
      <el-table-column prop="type" label="类型" width="120">
        <template #default="{ row }">
          <el-tag size="small">{{ getClassroomTypeLabel(row.type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="capacity" label="容纳人数" width="100" />
      <el-table-column prop="hasMultimedia" label="多媒体" width="80">
        <template #default="{ row }">
          <el-icon v-if="row.hasMultimedia" color="#67C23A"><Check /></el-icon>
          <el-icon v-else color="#909399"><Close /></el-icon>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 'available' ? 'success' : 'danger'" size="small">
            {{ row.status === 'available' ? '可用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="showEditDialog(row)">
            <el-icon><Edit /></el-icon>编辑
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑教室' : '新建教室'" width="500px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="教室名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：1号教学楼101" />
        </el-form-item>
        <el-form-item label="教室编号" prop="code">
          <el-input v-model="form.code" placeholder="例如：A101" />
        </el-form-item>
        <el-form-item label="所在楼栋" prop="building">
          <el-input v-model="form.building" placeholder="例如：1号教学楼" />
        </el-form-item>
        <el-form-item label="楼层" prop="floor">
          <el-input-number v-model="form.floor" :min="-2" :max="20" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="form.type" placeholder="选择类型" style="width: 100%;">
            <el-option label="普通教室" value="normal" />
            <el-option label="实验室" value="lab" />
            <el-option label="多媒体教室" value="multimedia" />
            <el-option label="音乐教室" value="music" />
            <el-option label="美术教室" value="art" />
            <el-option label="体育馆" value="gym" />
          </el-select>
        </el-form-item>
        <el-form-item label="容纳人数" prop="capacity">
          <el-input-number v-model="form.capacity" :min="1" :max="500" />
        </el-form-item>
        <el-form-item label="多媒体设备" prop="hasMultimedia">
          <el-switch v-model="form.hasMultimedia" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-switch v-model="form.status" active-value="available" inactive-value="disabled" active-text="可用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDialogVisible" title="导入教室" width="450px">
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
import { getClassrooms, createClassroom, updateClassroom, deleteClassroom, importClassrooms } from '../../api/classroom'
import { ElMessage, ElMessageBox } from 'element-plus'
import { exportToExcel, importFromExcel } from '../../utils/excel'

const loading = ref(false)
const submitLoading = ref(false)
const importLoading = ref(false)
const classrooms = ref([])
const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const importFile = ref(null)
const searchType = ref('')
const searchKeyword = ref('')

const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  name: '', code: '', building: '', floor: 1, type: 'normal',
  capacity: 50, hasMultimedia: false, status: 'available'
})

const formRules = {
  name: [{ required: true, message: '请输入教室名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入教室编号', trigger: 'blur' }],
  type: [{ required: true, message: '请选择教室类型', trigger: 'change' }]
}

const typeLabels = { normal: '普通教室', lab: '实验室', multimedia: '多媒体教室', music: '音乐教室', art: '美术教室', gym: '体育馆' }
function getClassroomTypeLabel(type) { return typeLabels[type] || type }

async function loadData() {
  loading.value = true
  try {
    const res = await getClassrooms({
      page: pagination.page, pageSize: pagination.pageSize,
      type: searchType.value || undefined, keyword: searchKeyword.value || undefined
    })
    classrooms.value = res.data?.list || res.data || []
    pagination.total = res.data?.total || 0
  } catch (e) { console.error('加载教室数据失败', e) } finally { loading.value = false }
}

function showCreateDialog() {
  isEdit.value = false; editingId.value = null
  Object.assign(form, { name: '', code: '', building: '', floor: 1, type: 'normal', capacity: 50, hasMultimedia: false, status: 'available' })
  dialogVisible.value = true
}

function showEditDialog(row) {
  isEdit.value = true; editingId.value = row.id; Object.assign(form, row); dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (isEdit.value) { await updateClassroom(editingId.value, form); ElMessage.success('更新成功') }
      else { await createClassroom(form); ElMessage.success('创建成功') }
      dialogVisible.value = false; loadData()
    } catch (e) { console.error('操作失败', e) } finally { submitLoading.value = false }
  })
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除教室"${row.name}"吗？`, '警告', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    await deleteClassroom(row.id); ElMessage.success('删除成功'); loadData()
  } catch (e) { if (e !== 'cancel') console.error('删除失败', e) }
}

function handleFileChange(file) { importFile.value = file.raw }

async function confirmImport() {
  if (!importFile.value) { ElMessage.warning('请选择文件'); return }
  importLoading.value = true
  try {
    const { headers, rows } = await importFromExcel(importFile.value)
    const data = rows.map(row => { const obj = {}; headers.forEach((h, i) => { obj[h] = row[i] }); return obj })
    await importClassrooms(data); ElMessage.success('导入成功'); importDialogVisible.value = false; loadData()
  } catch (e) { ElMessage.error(e.message || '导入失败') } finally { importLoading.value = false }
}

function handleImport() { importFile.value = null; importDialogVisible.value = true }

function handleExport() {
  exportToExcel(classrooms.value, [
    { prop: 'name', label: '教室名称' }, { prop: 'code', label: '教室编号' },
    { prop: 'building', label: '所在楼栋' }, { prop: 'type', label: '类型', formatter: row => getClassroomTypeLabel(row.type) },
    { prop: 'capacity', label: '容纳人数' }
  ], '教室数据')
}

onMounted(() => { loadData() })
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>

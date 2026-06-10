<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">科目管理</h2>
      <div>
        <el-button @click="handleImport">
          <el-icon><Upload /></el-icon>导入
        </el-button>
        <el-button @click="handleDownloadTemplate">
          <el-icon><Download /></el-icon>下载模板
        </el-button>
        <el-button @click="handleExport">
          <el-icon><Document /></el-icon>导出
        </el-button>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>新建科目
        </el-button>
      </div>
    </div>

    <div class="search-bar">
      <el-select v-model="searchType" placeholder="科目类型" clearable @change="loadData" style="width: 150px;">
        <el-option label="主科" value="main" />
        <el-option label="副科" value="sub" />
        <el-option label="小科" value="minor" />
      </el-select>
      <el-input v-model="searchKeyword" placeholder="搜索科目名称" clearable @clear="loadData" @keyup.enter="loadData" style="width: 200px;">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
    </div>

    <el-table :data="subjects" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="name" label="科目名称" min-width="120" />
      <el-table-column prop="code" label="科目代码" width="100" />
      <el-table-column prop="type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.type === 'main' ? 'danger' : (row.type === 'sub' ? 'warning' : 'info')" size="small">
            {{ row.type === 'main' ? '主科' : (row.type === 'sub' ? '副科' : '小科') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="color" label="颜色" width="80">
        <template #default="{ row }">
          <div class="color-preview" :style="{ background: row.color || '#409EFF' }"></div>
        </template>
      </el-table-column>
      <el-table-column prop="weeklyHours" label="默认周课时" width="100" />
      <el-table-column prop="needsClassroom" label="需要专用教室" width="120">
        <template #default="{ row }">
          <el-tag :type="row.needsClassroom ? 'success' : 'info'" size="small">
            {{ row.needsClassroom ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="sortOrder" label="排序" width="70" />
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑科目' : '新建科目'" width="500px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="120px">
        <el-form-item label="科目名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：语文" />
        </el-form-item>
        <el-form-item label="科目代码" prop="code">
          <el-input v-model="form.code" placeholder="例如：CHN" />
        </el-form-item>
        <el-form-item label="科目类型" prop="type">
          <el-select v-model="form.type" placeholder="选择类型" style="width: 100%;">
            <el-option label="主科" value="main" />
            <el-option label="副科" value="sub" />
            <el-option label="小科" value="minor" />
          </el-select>
        </el-form-item>
        <el-form-item label="颜色" prop="color">
          <el-color-picker v-model="form.color" />
        </el-form-item>
        <el-form-item label="默认周课时" prop="weeklyHours">
          <el-input-number v-model="form.weeklyHours" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="需要专用教室" prop="needsClassroom">
          <el-switch v-model="form.needsClassroom" />
        </el-form-item>
        <el-form-item label="排序" prop="sortOrder">
          <el-input-number v-model="form.sortOrder" :min="0" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDialogVisible" title="导入科目" width="450px">
      <el-upload ref="uploadRef" drag :auto-upload="false" accept=".xlsx,.xls" :limit="1" :on-change="handleFileChange">
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
import { getSubjects, createSubject, updateSubject, deleteSubject, importSubjects } from '../../api/subject'
import { ElMessage, ElMessageBox } from 'element-plus'
import { exportToExcel, importFromExcel, downloadTemplate } from '../../utils/excel'

const loading = ref(false)
const submitLoading = ref(false)
const importLoading = ref(false)
const subjects = ref([])
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
  name: '',
  code: '',
  type: 'main',
  color: '#409EFF',
  weeklyHours: 4,
  needsClassroom: false,
  sortOrder: 0
})

const formRules = {
  name: [{ required: true, message: '请输入科目名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入科目代码', trigger: 'blur' }],
  type: [{ required: true, message: '请选择科目类型', trigger: 'change' }]
}

async function loadData() {
  loading.value = true
  try {
    const res = await getSubjects({
      page: pagination.page,
      pageSize: pagination.pageSize,
      type: searchType.value || undefined,
      keyword: searchKeyword.value || undefined
    })
    subjects.value = res.data?.list || res.data || []
    pagination.total = res.data?.total || 0
  } catch (e) {
    console.error('加载科目数据失败', e)
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, { name: '', code: '', type: 'main', color: '#409EFF', weeklyHours: 4, needsClassroom: false, sortOrder: 0 })
  dialogVisible.value = true
}

function showEditDialog(row) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, row)
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (isEdit.value) {
        await updateSubject(editingId.value, form)
        ElMessage.success('更新成功')
      } else {
        await createSubject(form)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadData()
    } catch (e) {
      console.error('操作失败', e)
    } finally {
      submitLoading.value = false
    }
  })
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除科目"${row.name}"吗？`, '警告', {
      confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
    })
    await deleteSubject(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    if (e !== 'cancel') console.error('删除失败', e)
  }
}

function handleImport() {
  importFile.value = null
  importDialogVisible.value = true
}

function handleFileChange(file) {
  importFile.value = file.raw
}

async function confirmImport() {
  if (!importFile.value) { ElMessage.warning('请选择文件'); return }
  importLoading.value = true
  try {
    const { headers, rows } = await importFromExcel(importFile.value)
    const data = rows.map(row => {
      const obj = {}
      headers.forEach((h, i) => { obj[h] = row[i] })
      return obj
    })
    await importSubjects(data)
    ElMessage.success('导入成功')
    importDialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.message || '导入失败')
  } finally {
    importLoading.value = false
  }
}

function handleExport() {
  exportToExcel(subjects.value, [
    { prop: 'name', label: '科目名称' },
    { prop: 'code', label: '科目代码' },
    { prop: 'type', label: '类型', formatter: row => row.type === 'main' ? '主科' : (row.type === 'sub' ? '副科' : '小科') },
    { prop: 'weeklyHours', label: '默认周课时' }
  ], '科目数据')
}

function handleDownloadTemplate() {
  downloadTemplate([
    { label: '科目名称' },
    { label: '科目代码' },
    { label: '类型(main/sub/minor)' },
    { label: '默认周课时' }
  ], '科目导入模板')
}

onMounted(() => { loadData() })
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
.color-preview { width: 24px; height: 24px; border-radius: 4px; border: 1px solid #dcdfe6; }
</style>

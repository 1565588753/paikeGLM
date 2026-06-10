<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">班级管理</h2>
      <div>
        <el-button @click="handleImport">
          <el-icon><Upload /></el-icon>导入
        </el-button>
        <el-button @click="handleExport">
          <el-icon><Download /></el-icon>导出
        </el-button>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>新建班级
        </el-button>
      </div>
    </div>

    <div class="search-bar">
      <el-select v-model="searchGrade" placeholder="筛选年级" clearable @change="loadData" style="width: 150px;">
        <el-option v-for="g in grades" :key="g" :label="g + '年级'" :value="g" />
      </el-select>
      <el-input v-model="searchKeyword" placeholder="搜索班级名称" clearable @clear="loadData" @keyup.enter="loadData" style="width: 200px;">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
    </div>

    <el-table :data="classes" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="name" label="班级名称" min-width="140" />
      <el-table-column prop="grade" label="年级" width="100">
        <template #default="{ row }">{{ row.grade }}年级</template>
      </el-table-column>
      <el-table-column prop="classNumber" label="班级序号" width="100" />
      <el-table-column prop="headTeacher" label="班主任" width="100" />
      <el-table-column prop="studentCount" label="学生人数" width="100" />
      <el-table-column prop="classroom" label="固定教室" width="120" />
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑班级' : '新建班级'" width="500px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="年级" prop="grade">
          <el-select v-model="form.grade" placeholder="选择年级" style="width: 100%;">
            <el-option v-for="g in grades" :key="g" :label="g + '年级'" :value="g" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：一年级1班" />
        </el-form-item>
        <el-form-item label="班级序号" prop="classNumber">
          <el-input-number v-model="form.classNumber" :min="1" :max="30" />
        </el-form-item>
        <el-form-item label="班主任" prop="headTeacherId">
          <el-input v-model="form.headTeacherId" placeholder="班主任工号" />
        </el-form-item>
        <el-form-item label="学生人数" prop="studentCount">
          <el-input-number v-model="form.studentCount" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="固定教室" prop="classroomId">
          <el-input v-model="form.classroomId" placeholder="教室编号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDialogVisible" title="导入班级" width="450px">
      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        accept=".xlsx,.xls"
        :limit="1"
        :on-change="handleFileChange"
      >
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
import { getClasses, createClass, updateClass, deleteClass, importClasses, exportClasses } from '../../api/class'
import { ElMessage, ElMessageBox } from 'element-plus'
import { exportToExcel, importFromExcel, downloadTemplate } from '../../utils/excel'

const loading = ref(false)
const submitLoading = ref(false)
const importLoading = ref(false)
const classes = ref([])
const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const uploadRef = ref(null)
const importFile = ref(null)
const searchGrade = ref('')
const searchKeyword = ref('')
const grades = [1, 2, 3, 4, 5, 6, 7, 8, 9]

const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  grade: null,
  name: '',
  classNumber: 1,
  headTeacherId: '',
  studentCount: 40,
  classroomId: ''
})

const formRules = {
  grade: [{ required: true, message: '请选择年级', trigger: 'change' }],
  name: [{ required: true, message: '请输入班级名称', trigger: 'blur' }],
  classNumber: [{ required: true, message: '请输入班级序号', trigger: 'blur' }]
}

async function loadData() {
  loading.value = true
  try {
    const res = await getClasses({
      page: pagination.page,
      pageSize: pagination.pageSize,
      grade: searchGrade.value || undefined,
      keyword: searchKeyword.value || undefined
    })
    classes.value = res.data?.list || res.data || []
    pagination.total = res.data?.total || 0
  } catch (e) {
    console.error('加载班级数据失败', e)
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, { grade: null, name: '', classNumber: 1, headTeacherId: '', studentCount: 40, classroomId: '' })
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
        await updateClass(editingId.value, form)
        ElMessage.success('更新成功')
      } else {
        await createClass(form)
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
    await ElMessageBox.confirm(`确定要删除班级"${row.name}"吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteClass(row.id)
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
  if (!importFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  importLoading.value = true
  try {
    const { headers, rows } = await importFromExcel(importFile.value)
    const data = rows.map(row => {
      const obj = {}
      headers.forEach((h, i) => { obj[h] = row[i] })
      return obj
    })
    await importClasses(data)
    ElMessage.success('导入成功')
    importDialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.message || '导入失败')
  } finally {
    importLoading.value = false
  }
}

async function handleExport() {
  try {
    const res = await getClasses({ pageSize: 9999 })
    const data = res.data?.list || res.data || []
    exportToExcel(data, [
      { prop: 'name', label: '班级名称' },
      { prop: 'grade', label: '年级' },
      { prop: 'classNumber', label: '班级序号' },
      { prop: 'headTeacher', label: '班主任' },
      { prop: 'studentCount', label: '学生人数' },
      { prop: 'classroom', label: '固定教室' }
    ], '班级数据')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>

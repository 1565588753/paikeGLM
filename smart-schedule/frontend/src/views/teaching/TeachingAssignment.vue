<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">任课安排</h2>
      <div>
        <el-button @click="handleImport">
          <el-icon><Upload /></el-icon>导入
        </el-button>
        <el-button @click="handleExport">
          <el-icon><Download /></el-icon>导出
        </el-button>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>添加任课
        </el-button>
        <el-button type="success" @click="showBatchDialog">
          <el-icon><List /></el-icon>批量添加
        </el-button>
      </div>
    </div>

    <div class="search-bar">
      <el-select v-model="searchGrade" placeholder="筛选年级" clearable @change="loadData" style="width: 130px;">
        <el-option v-for="g in grades" :key="g" :label="g + '年级'" :value="g" />
      </el-select>
      <el-select v-model="searchClassId" placeholder="筛选班级" clearable @change="loadData" style="width: 150px;">
        <el-option v-for="c in classOptions" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-select v-model="searchSubjectId" placeholder="筛选科目" clearable @change="loadData" style="width: 130px;">
        <el-option v-for="s in subjectOptions" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <el-input v-model="searchTeacher" placeholder="搜索教师" clearable @clear="loadData" @keyup.enter="loadData" style="width: 150px;">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
    </div>

    <el-table :data="assignments" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="className" label="班级" width="140" />
      <el-table-column prop="grade" label="年级" width="80">
        <template #default="{ row }">{{ row.grade }}年级</template>
      </el-table-column>
      <el-table-column prop="subjectName" label="科目" width="100" />
      <el-table-column prop="teacherName" label="教师" width="100" />
      <el-table-column prop="weeklyHours" label="周课时" width="80" />
      <el-table-column prop="weekType" label="单双周" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.weekType === 'odd'" type="primary" size="small">单周</el-tag>
          <el-tag v-else-if="row.weekType === 'even'" type="warning" size="small">双周</el-tag>
          <el-tag v-else type="info" size="small">全周</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="classroomName" label="指定教室" width="120" />
      <el-table-column prop="notes" label="备注" min-width="120" />
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑任课' : '添加任课'" width="500px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="班级" prop="classId">
          <el-select v-model="form.classId" placeholder="选择班级" filterable style="width: 100%;">
            <el-option v-for="c in classOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="科目" prop="subjectId">
          <el-select v-model="form.subjectId" placeholder="选择科目" style="width: 100%;">
            <el-option v-for="s in subjectOptions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="教师" prop="teacherId">
          <el-input v-model="form.teacherId" placeholder="教师工号" />
        </el-form-item>
        <el-form-item label="周课时" prop="weeklyHours">
          <el-input-number v-model="form.weeklyHours" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="单双周" prop="weekType">
          <el-select v-model="form.weekType" style="width: 100%;">
            <el-option label="全周" value="all" />
            <el-option label="单周" value="odd" />
            <el-option label="双周" value="even" />
          </el-select>
        </el-form-item>
        <el-form-item label="指定教室" prop="classroomId">
          <el-select v-model="form.classroomId" placeholder="可选" clearable filterable style="width: 100%;">
            <el-option v-for="r in classroomOptions" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="notes">
          <el-input v-model="form.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="batchDialogVisible" title="批量添加任课" width="600px" destroy-on-close>
      <el-form ref="batchFormRef" :model="batchForm" label-width="100px">
        <el-form-item label="年级" required>
          <el-select v-model="batchForm.grade" placeholder="选择年级" style="width: 100%;">
            <el-option v-for="g in grades" :key="g" :label="g + '年级'" :value="g" />
          </el-select>
        </el-form-item>
        <el-form-item label="科目" required>
          <el-select v-model="batchForm.subjectId" placeholder="选择科目" style="width: 100%;">
            <el-option v-for="s in subjectOptions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="教师" required>
          <el-input v-model="batchForm.teacherId" placeholder="教师工号" />
        </el-form-item>
        <el-form-item label="周课时">
          <el-input-number v-model="batchForm.weeklyHours" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="适用班级">
          <el-checkbox-group v-model="batchForm.classIds">
            <el-checkbox v-for="c in filteredBatchClasses" :key="c.id" :label="c.name" :value="c.id" />
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="batchLoading" @click="handleBatchSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDialogVisible" title="导入任课安排" width="450px">
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
import { ref, reactive, computed, onMounted } from 'vue'
import { getTeachingAssignments, createTeachingAssignment, updateTeachingAssignment, deleteTeachingAssignment, batchCreateTeachingAssignments, importTeachingAssignments } from '../../api/teaching'
import { getClasses } from '../../api/class'
import { getSubjects } from '../../api/subject'
import { getClassrooms } from '../../api/classroom'
import { ElMessage, ElMessageBox } from 'element-plus'
import { exportToExcel, importFromExcel } from '../../utils/excel'

const loading = ref(false)
const submitLoading = ref(false)
const batchLoading = ref(false)
const importLoading = ref(false)
const assignments = ref([])
const classOptions = ref([])
const subjectOptions = ref([])
const classroomOptions = ref([])
const dialogVisible = ref(false)
const batchDialogVisible = ref(false)
const importDialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const importFile = ref(null)
const searchGrade = ref('')
const searchClassId = ref('')
const searchSubjectId = ref('')
const searchTeacher = ref('')
const grades = [1, 2, 3, 4, 5, 6, 7, 8, 9]

const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  classId: '', subjectId: '', teacherId: '', weeklyHours: 4,
  weekType: 'all', classroomId: '', notes: ''
})

const batchForm = reactive({
  grade: null, subjectId: '', teacherId: '', weeklyHours: 4, classIds: []
})

const filteredBatchClasses = computed(() => {
  if (!batchForm.grade) return classOptions.value
  return classOptions.value.filter(c => c.grade === batchForm.grade)
})

const formRules = {
  classId: [{ required: true, message: '请选择班级', trigger: 'change' }],
  subjectId: [{ required: true, message: '请选择科目', trigger: 'change' }],
  teacherId: [{ required: true, message: '请输入教师工号', trigger: 'blur' }],
  weeklyHours: [{ required: true, message: '请输入周课时', trigger: 'blur' }]
}

async function loadData() {
  loading.value = true
  try {
    const res = await getTeachingAssignments({
      page: pagination.page, pageSize: pagination.pageSize,
      grade: searchGrade.value || undefined,
      classId: searchClassId.value || undefined,
      subjectId: searchSubjectId.value || undefined,
      teacher: searchTeacher.value || undefined
    })
    assignments.value = res.data?.list || res.data || []
    pagination.total = res.data?.total || 0
  } catch (e) { console.error('加载任课数据失败', e) } finally { loading.value = false }
}

async function loadOptions() {
  try {
    const [clsRes, subRes, roomRes] = await Promise.all([
      getClasses({ pageSize: 999 }),
      getSubjects({ pageSize: 999 }),
      getClassrooms({ pageSize: 999 })
    ])
    classOptions.value = clsRes.data?.list || clsRes.data || []
    subjectOptions.value = subRes.data?.list || subRes.data || []
    classroomOptions.value = roomRes.data?.list || roomRes.data || []
  } catch (e) { console.error('加载选项失败', e) }
}

function showCreateDialog() {
  isEdit.value = false; editingId.value = null
  Object.assign(form, { classId: '', subjectId: '', teacherId: '', weeklyHours: 4, weekType: 'all', classroomId: '', notes: '' })
  dialogVisible.value = true
}

function showEditDialog(row) {
  isEdit.value = true; editingId.value = row.id; Object.assign(form, row); dialogVisible.value = true
}

function showBatchDialog() { batchForm.grade = null; batchForm.subjectId = ''; batchForm.teacherId = ''; batchForm.weeklyHours = 4; batchForm.classIds = []; batchDialogVisible.value = true }

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (isEdit.value) { await updateTeachingAssignment(editingId.value, form); ElMessage.success('更新成功') }
      else { await createTeachingAssignment(form); ElMessage.success('添加成功') }
      dialogVisible.value = false; loadData()
    } catch (e) { console.error('操作失败', e) } finally { submitLoading.value = false }
  })
}

async function handleBatchSubmit() {
  if (!batchForm.grade || !batchForm.subjectId || !batchForm.teacherId || batchForm.classIds.length === 0) {
    ElMessage.warning('请填写完整信息'); return
  }
  batchLoading.value = true
  try {
    await batchCreateTeachingAssignments(batchForm)
    ElMessage.success('批量添加成功'); batchDialogVisible.value = false; loadData()
  } catch (e) { console.error('批量添加失败', e) } finally { batchLoading.value = false }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除此任课安排吗？', '警告', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    await deleteTeachingAssignment(row.id); ElMessage.success('删除成功'); loadData()
  } catch (e) { if (e !== 'cancel') console.error('删除失败', e) }
}

function handleFileChange(file) { importFile.value = file.raw }
function handleImport() { importFile.value = null; importDialogVisible.value = true }

async function confirmImport() {
  if (!importFile.value) { ElMessage.warning('请选择文件'); return }
  importLoading.value = true
  try {
    const { headers, rows } = await importFromExcel(importFile.value)
    const data = rows.map(row => { const obj = {}; headers.forEach((h, i) => { obj[h] = row[i] }); return obj })
    await importTeachingAssignments(data); ElMessage.success('导入成功'); importDialogVisible.value = false; loadData()
  } catch (e) { ElMessage.error(e.message || '导入失败') } finally { importLoading.value = false }
}

function handleExport() {
  exportToExcel(assignments.value, [
    { prop: 'className', label: '班级' }, { prop: 'grade', label: '年级' },
    { prop: 'subjectName', label: '科目' }, { prop: 'teacherName', label: '教师' },
    { prop: 'weeklyHours', label: '周课时' }, { prop: 'weekType', label: '单双周' }
  ], '任课安排')
}

onMounted(() => { loadData(); loadOptions() })
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>

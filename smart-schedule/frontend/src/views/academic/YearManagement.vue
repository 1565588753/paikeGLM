<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">学年管理</h2>
      <el-button type="primary" @click="showCreateDialog" v-if="userStore.isAdmin">
        <el-icon><Plus /></el-icon>新建学年
      </el-button>
    </div>

    <el-table :data="academicYears" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="name" label="学年名称" min-width="180" />
      <el-table-column prop="startDate" label="开始日期" width="120" />
      <el-table-column prop="endDate" label="结束日期" width="120" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.isCurrent ? 'success' : (row.status === 'archived' ? 'info' : 'warning')">
            {{ row.isCurrent ? '当前学年' : (row.status === 'archived' ? '已归档' : '未激活') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="semesterCount" label="学期数" width="80" />
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="viewSemesters(row)">
            <el-icon><Date /></el-icon>学期管理
          </el-button>
          <el-button
            v-if="userStore.isAdmin && !row.isCurrent && row.status !== 'archived'"
            size="small"
            text
            type="warning"
            @click="handleSwitchYear(row)"
          >
            <el-icon><RefreshRight /></el-icon>切换到此学年
          </el-button>
          <el-button
            v-if="userStore.isAdmin && row.status !== 'archived'"
            size="small"
            text
            type="primary"
            @click="showEditDialog(row)"
          >
            <el-icon><Edit /></el-icon>编辑
          </el-button>
          <el-button
            v-if="userStore.isAdmin && !row.isCurrent"
            size="small"
            text
            type="danger"
            @click="handleDelete(row)"
          >
            <el-icon><Delete /></el-icon>删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑学年' : '新建学年'"
      width="500px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="学年名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：2024-2025学年" />
        </el-form-item>
        <el-form-item label="开始日期" prop="startDate">
          <el-date-picker v-model="form.startDate" type="date" value-format="YYYY-MM-DD" placeholder="选择开始日期" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="结束日期" prop="endDate">
          <el-date-picker v-model="form.endDate" type="date" value-format="YYYY-MM-DD" placeholder="选择结束日期" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="switchDialogVisible"
      title="切换学年确认"
      width="560px"
    >
      <el-alert type="warning" :closable="false" show-icon style="margin-bottom: 16px;">
        <template #title>切换学年将会执行以下操作：</template>
      </el-alert>
      <div class="switch-info">
        <p>1. 当前学年将被<strong>归档</strong>，数据变为只读</p>
        <p>2. 新学年将被创建并设为当前学年</p>
        <p>3. 所有年级将<strong>自动升级</strong>（如一年级升为二年级）</p>
        <p>4. 新的一年级班级将自动创建</p>
        <p>5. 基础数据（科目、教室、作息时间等）将被复制到新学年</p>
        <p>6. 任课安排和课表数据<strong>不会</strong>被复制</p>
      </div>
      <template #footer>
        <el-button @click="switchDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="switchLoading" @click="confirmSwitchYear">确认切换</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'
import { useAcademicStore } from '../../stores/academic'
import { getAcademicYears, createAcademicYear, updateAcademicYear, deleteAcademicYear, switchYear } from '../../api/academic'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const academicStore = useAcademicStore()

const loading = ref(false)
const submitLoading = ref(false)
const switchLoading = ref(false)
const academicYears = ref([])
const dialogVisible = ref(false)
const switchDialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const switchingYear = ref(null)
const formRef = ref(null)

const form = reactive({
  name: '',
  startDate: '',
  endDate: ''
})

const formRules = {
  name: [{ required: true, message: '请输入学年名称', trigger: 'blur' }],
  startDate: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  endDate: [{ required: true, message: '请选择结束日期', trigger: 'change' }]
}

async function loadData() {
  loading.value = true
  try {
    const res = await getAcademicYears()
    academicYears.value = res.data || []
  } catch (e) {
    console.error('加载学年数据失败', e)
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, { name: '', startDate: '', endDate: '' })
  dialogVisible.value = true
}

function showEditDialog(row) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, { name: row.name, startDate: row.startDate, endDate: row.endDate })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (isEdit.value) {
        await updateAcademicYear(editingId.value, form)
        ElMessage.success('更新成功')
      } else {
        await createAcademicYear(form)
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

function handleSwitchYear(row) {
  switchingYear.value = row
  switchDialogVisible.value = true
}

async function confirmSwitchYear() {
  if (!switchingYear.value) return
  switchLoading.value = true
  try {
    await switchYear(switchingYear.value.id)
    ElMessage.success('学年切换成功')
    switchDialogVisible.value = false
    await academicStore.fetchCurrentYear()
    loadData()
  } catch (e) {
    console.error('切换学年失败', e)
  } finally {
    switchLoading.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除学年"${row.name}"吗？此操作不可恢复。`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteAcademicYear(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    if (e !== 'cancel') console.error('删除失败', e)
  }
}

function viewSemesters(row) {
  router.push({ path: '/academic/semester', query: { yearId: row.id } })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.switch-info {
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 8px;
  line-height: 2;
}

.switch-info p {
  font-size: 14px;
  color: #606266;
}

.switch-info strong {
  color: #F56C6C;
}
</style>

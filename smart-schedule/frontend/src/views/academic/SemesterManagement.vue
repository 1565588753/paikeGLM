<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">学期管理</h2>
      <div>
        <el-button @click="$router.push('/academic')">
          <el-icon><ArrowLeft /></el-icon>返回学年
        </el-button>
        <el-button type="primary" @click="showCreateDialog" v-if="userStore.isAdmin">
          <el-icon><Plus /></el-icon>新建学期
        </el-button>
      </div>
    </div>

    <el-card v-if="currentYear" shadow="never" style="margin-bottom: 20px;">
      <div style="display: flex; align-items: center; gap: 12px;">
        <el-tag type="primary" size="large">{{ currentYear.name }}</el-tag>
        <span style="color: #909399;">{{ currentYear.startDate }} ~ {{ currentYear.endDate }}</span>
      </div>
    </el-card>

    <el-table :data="semesters" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="name" label="学期名称" min-width="180" />
      <el-table-column prop="startDate" label="开始日期" width="120" />
      <el-table-column prop="endDate" label="结束日期" width="120" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="row.isCurrent ? 'success' : (row.status === 'archived' ? 'info' : 'warning')">
            {{ row.isCurrent ? '当前学期' : (row.status === 'archived' ? '已归档' : '未激活') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="weekCount" label="总周数" width="80" />
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="userStore.isAdmin && !row.isCurrent && row.status !== 'archived'"
            size="small"
            text
            type="warning"
            @click="handleSwitchSemester(row)"
          >
            <el-icon><RefreshRight /></el-icon>切换
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
      :title="isEdit ? '编辑学期' : '新建学期'"
      width="500px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="学期名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：第一学期" />
        </el-form-item>
        <el-form-item label="开始日期" prop="startDate">
          <el-date-picker v-model="form.startDate" type="date" value-format="YYYY-MM-DD" placeholder="选择开始日期" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="结束日期" prop="endDate">
          <el-date-picker v-model="form.endDate" type="date" value-format="YYYY-MM-DD" placeholder="选择结束日期" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="总周数" prop="weekCount">
          <el-input-number v-model="form.weekCount" :min="1" :max="30" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '../../stores/user'
import { useAcademicStore } from '../../stores/academic'
import { getAcademicYear, getSemesters, createSemester, updateSemester, deleteSemester, switchSemester } from '../../api/academic'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const userStore = useUserStore()
const academicStore = useAcademicStore()

const loading = ref(false)
const submitLoading = ref(false)
const semesters = ref([])
const currentYear = ref(null)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const yearId = ref(route.query.yearId)

const form = reactive({
  name: '',
  startDate: '',
  endDate: '',
  weekCount: 20
})

const formRules = {
  name: [{ required: true, message: '请输入学期名称', trigger: 'blur' }],
  startDate: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  endDate: [{ required: true, message: '请选择结束日期', trigger: 'change' }],
  weekCount: [{ required: true, message: '请输入总周数', trigger: 'blur' }]
}

async function loadData() {
  loading.value = true
  try {
    if (yearId.value) {
      const yearRes = await getAcademicYear(yearId.value)
      currentYear.value = yearRes.data
      const semRes = await getSemesters(yearId.value)
      semesters.value = semRes.data || []
    } else {
      const res = await getSemesters(academicStore.currentYear?.id)
      semesters.value = res.data || []
      currentYear.value = academicStore.currentYear
    }
  } catch (e) {
    console.error('加载学期数据失败', e)
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, { name: '', startDate: '', endDate: '', weekCount: 20 })
  dialogVisible.value = true
}

function showEditDialog(row) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, { name: row.name, startDate: row.startDate, endDate: row.endDate, weekCount: row.weekCount })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      const yid = yearId.value || academicStore.currentYear?.id
      if (isEdit.value) {
        await updateSemester(yid, editingId.value, form)
        ElMessage.success('更新成功')
      } else {
        await createSemester(yid, form)
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

async function handleSwitchSemester(row) {
  try {
    await ElMessageBox.confirm(`确定要切换到"${row.name}"吗？`, '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await switchSemester(row.id)
    ElMessage.success('学期切换成功')
    await academicStore.fetchCurrentYear()
    loadData()
  } catch (e) {
    if (e !== 'cancel') console.error('切换学期失败', e)
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除学期"${row.name}"吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const yid = yearId.value || academicStore.currentYear?.id
    await deleteSemester(yid, row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    if (e !== 'cancel') console.error('删除失败', e)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
</style>

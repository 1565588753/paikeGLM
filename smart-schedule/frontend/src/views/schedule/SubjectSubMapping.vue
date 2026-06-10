<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">语数外匹配小课设置</h2>
    </div>

    <el-alert type="info" :closable="false" show-icon style="margin-bottom: 20px;">
      <template #title>
        配置哪些小科（综合实践、劳动、校本、自习等）可以被当作主科（语文、数学、英语）来排课。
        启用后，排课引擎会考虑将这些小科课程安排在上午时段（但不会排在第一节），以满足主科教师每日课时需求。
      </template>
    </el-alert>

    <el-card shadow="hover">
      <div class="mapping-header">
        <h3>匹配规则列表</h3>
        <el-button type="primary" @click="addMapping">
          <el-icon><Plus /></el-icon>添加规则
        </el-button>
      </div>

      <el-table :data="mappings" v-loading="loading" stripe border style="width: 100%; margin-top: 16px;">
        <el-table-column prop="mainSubject" label="主科" width="150">
          <template #default="{ row }">
            <el-tag type="danger" size="large">{{ row.mainSubject }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="subSubject" label="匹配小科" width="150">
          <template #default="{ row }">
            <el-tag type="info" size="large">{{ row.subSubject }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="200" />
        <el-table-column prop="enabled" label="启用状态" width="120">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="toggleMapping(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-input-number v-model="row.priority" :min="1" :max="10" size="small" @change="updateMapping(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="danger" @click="deleteMapping(row)">
              <el-icon><Delete /></el-icon>删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="添加匹配规则" width="450px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="主科" prop="mainSubject">
          <el-select v-model="form.mainSubject" placeholder="选择主科" style="width: 100%;">
            <el-option label="语文" value="语文" />
            <el-option label="数学" value="数学" />
            <el-option label="英语" value="英语" />
          </el-select>
        </el-form-item>
        <el-form-item label="匹配小科" prop="subSubject">
          <el-select v-model="form.subSubject" placeholder="选择小科" style="width: 100%;">
            <el-option label="综合实践" value="综合实践" />
            <el-option label="劳动" value="劳动" />
            <el-option label="校本" value="校本" />
            <el-option label="自习" value="自习" />
            <el-option label="阅读" value="阅读" />
            <el-option label="班会" value="班会" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="描述此匹配规则的用途" />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-input-number v-model="form.priority" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="启用" prop="enabled">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../api/index'

const loading = ref(false)
const mappings = ref([])
const dialogVisible = ref(false)
const formRef = ref(null)

const form = reactive({
  mainSubject: '',
  subSubject: '',
  description: '',
  priority: 5,
  enabled: true
})

const formRules = {
  mainSubject: [{ required: true, message: '请选择主科', trigger: 'change' }],
  subSubject: [{ required: true, message: '请选择小科', trigger: 'change' }]
}

async function loadData() {
  loading.value = true
  try {
    const res = await request.get('/subject-sub-mappings')
    mappings.value = res.data || []
  } catch (e) { console.error('加载匹配规则失败', e) } finally { loading.value = false }
}

function addMapping() {
  Object.assign(form, { mainSubject: '', subSubject: '', description: '', priority: 5, enabled: true })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      await request.post('/subject-sub-mappings', form)
      ElMessage.success('添加成功'); dialogVisible.value = false; loadData()
    } catch (e) { console.error('添加失败', e) }
  })
}

async function toggleMapping(row) {
  try {
    await request.put(`/subject-sub-mappings/${row.id}`, { enabled: row.enabled })
    ElMessage.success(row.enabled ? '已启用' : '已禁用')
  } catch (e) { row.enabled = !row.enabled; console.error('更新失败', e) }
}

async function updateMapping(row) {
  try {
    await request.put(`/subject-sub-mappings/${row.id}`, row)
  } catch (e) { console.error('更新失败', e) }
}

async function deleteMapping(row) {
  try {
    await ElMessageBox.confirm('确定要删除此匹配规则吗？', '警告', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    await request.delete(`/subject-sub-mappings/${row.id}`)
    ElMessage.success('删除成功'); loadData()
  } catch (e) { if (e !== 'cancel') console.error('删除失败', e) }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.mapping-header { display: flex; justify-content: space-between; align-items: center; }
.mapping-header h3 { font-size: 16px; font-weight: 600; color: #303133; }
</style>

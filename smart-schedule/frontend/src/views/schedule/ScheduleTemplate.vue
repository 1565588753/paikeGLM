<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">作息时间模板</h2>
      <el-button type="primary" @click="showCreateDialog" v-if="userStore.isAdmin">
        <el-icon><Plus /></el-icon>新建模板
      </el-button>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :md="8" v-for="template in templates" :key="template.id">
        <el-card shadow="hover" class="template-card">
          <div class="template-header">
            <div>
              <h3 class="template-name">{{ template.name }}</h3>
              <el-tag v-if="template.isDefault" type="success" size="small" style="margin-left: 8px;">默认</el-tag>
            </div>
            <el-dropdown trigger="click">
              <el-button text><el-icon><MoreFilled /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="editTemplate(template)">
                    <el-icon><Edit /></el-icon>编辑
                  </el-dropdown-item>
                  <el-dropdown-item @click="viewTimeSlots(template)">
                    <el-icon><Timer /></el-icon>编辑时间段
                  </el-dropdown-item>
                  <el-dropdown-item @click="copyToGrades(template)" v-if="userStore.isAdmin">
                    <el-icon><CopyDocument /></el-icon>复制到其他年级
                  </el-dropdown-item>
                  <el-dropdown-item @click="setDefault(template)" v-if="userStore.isAdmin && !template.isDefault">
                    <el-icon><Star /></el-icon>设为默认
                  </el-dropdown-item>
                  <el-dropdown-item @click="deleteTemplate(template)" v-if="userStore.isAdmin" divided>
                    <el-icon><Delete /></el-icon>删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div class="template-info">
            <div class="info-item">
              <el-icon><Calendar /></el-icon>
              <span>适用年级：{{ template.gradeName || '全部' }}</span>
            </div>
            <div class="info-item">
              <el-icon><Clock /></el-icon>
              <span>每周天数：{{ template.daysPerWeek }}天</span>
            </div>
            <div class="info-item">
              <el-icon><Timer /></el-icon>
              <span>每天节数：{{ template.periodsPerDay }}节</span>
            </div>
          </div>
          <div class="template-preview">
            <div class="preview-label">时间段预览</div>
            <div class="preview-slots" v-if="template.timeSlots && template.timeSlots.length > 0">
              <div
                v-for="slot in template.timeSlots.slice(0, 6)"
                :key="slot.id"
                class="preview-slot"
                :class="'slot-type-' + (slot.periodType || 'class')"
              >
                <span class="slot-label">{{ slot.label || slot.periodIndex }}</span>
                <span class="slot-time">{{ slot.startTime }}-{{ slot.endTime }}</span>
              </div>
              <div v-if="template.timeSlots.length > 6" class="preview-more">
                +{{ template.timeSlots.length - 6 }} 更多
              </div>
            </div>
            <div v-else class="preview-empty">暂无时间段</div>
          </div>
          <el-button type="primary" text @click="viewTimeSlots(template)" style="width: 100%; margin-top: 12px;">
            编辑时间段 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑模板' : '新建模板'" width="500px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：初中作息时间" />
        </el-form-item>
        <el-form-item label="适用年级" prop="grade">
          <el-select v-model="form.grade" placeholder="选择年级（留空则适用所有）" clearable style="width: 100%;">
            <el-option v-for="g in grades" :key="g" :label="g + '年级'" :value="g" />
          </el-select>
        </el-form-item>
        <el-form-item label="每周天数" prop="daysPerWeek">
          <el-input-number v-model="form.daysPerWeek" :min="5" :max="7" />
        </el-form-item>
        <el-form-item label="每天节数" prop="periodsPerDay">
          <el-input-number v-model="form.periodsPerDay" :min="1" :max="15" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="copyDialogVisible" title="复制到其他年级" width="400px">
      <p style="margin-bottom: 12px; color: #606266;">选择要复制此模板到的年级：</p>
      <el-checkbox-group v-model="copyGrades">
        <el-checkbox v-for="g in grades" :key="g" :label="g" :value="g">{{ g }}年级</el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="copyDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="copyLoading" @click="confirmCopy">确认复制</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'
import { getScheduleTemplates, createScheduleTemplate, updateScheduleTemplate, deleteScheduleTemplate, copyTemplateToGrades, setDefaultTemplate } from '../../api/schedule'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const submitLoading = ref(false)
const copyLoading = ref(false)
const templates = ref([])
const dialogVisible = ref(false)
const copyDialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const copyGrades = ref([])
const copyingTemplate = ref(null)
const grades = [1, 2, 3, 4, 5, 6, 7, 8, 9]

const form = reactive({
  name: '',
  grade: null,
  daysPerWeek: 5,
  periodsPerDay: 8
})

const formRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  daysPerWeek: [{ required: true, message: '请输入每周天数', trigger: 'blur' }],
  periodsPerDay: [{ required: true, message: '请输入每天节数', trigger: 'blur' }]
}

async function loadData() {
  loading.value = true
  try {
    const res = await getScheduleTemplates()
    templates.value = res.data || []
  } catch (e) { console.error('加载模板数据失败', e) } finally { loading.value = false }
}

function showCreateDialog() {
  isEdit.value = false; editingId.value = null
  Object.assign(form, { name: '', grade: null, daysPerWeek: 5, periodsPerDay: 8 })
  dialogVisible.value = true
}

function editTemplate(row) {
  isEdit.value = true; editingId.value = row.id
  Object.assign(form, { name: row.name, grade: row.grade, daysPerWeek: row.daysPerWeek, periodsPerDay: row.periodsPerDay })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (isEdit.value) { await updateScheduleTemplate(editingId.value, form); ElMessage.success('更新成功') }
      else { await createScheduleTemplate(form); ElMessage.success('创建成功') }
      dialogVisible.value = false; loadData()
    } catch (e) { console.error('操作失败', e) } finally { submitLoading.value = false }
  })
}

function viewTimeSlots(template) {
  router.push(`/schedules/editor/${template.id}`)
}

function copyToGrades(template) {
  copyingTemplate.value = template; copyGrades.value = []; copyDialogVisible.value = true
}

async function confirmCopy() {
  if (copyGrades.value.length === 0) { ElMessage.warning('请选择至少一个年级'); return }
  copyLoading.value = true
  try {
    await copyTemplateToGrades(copyingTemplate.value.id, { grades: copyGrades.value })
    ElMessage.success('复制成功'); copyDialogVisible.value = false; loadData()
  } catch (e) { console.error('复制失败', e) } finally { copyLoading.value = false }
}

async function setDefault(template) {
  try {
    await setDefaultTemplate(template.id)
    ElMessage.success('已设为默认'); loadData()
  } catch (e) { console.error('设置失败', e) }
}

async function deleteTemplate(template) {
  try {
    await ElMessageBox.confirm(`确定要删除模板"${template.name}"吗？`, '警告', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    await deleteScheduleTemplate(template.id); ElMessage.success('删除成功'); loadData()
  } catch (e) { if (e !== 'cancel') console.error('删除失败', e) }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.template-card { margin-bottom: 20px; }
.template-header { display: flex; justify-content: space-between; align-items: center; }
.template-name { font-size: 16px; font-weight: 600; color: #303133; display: inline; }
.template-info { margin-top: 12px; display: flex; flex-direction: column; gap: 6px; }
.info-item { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #606266; }
.template-preview { margin-top: 16px; padding-top: 12px; border-top: 1px solid #f0f2f5; }
.preview-label { font-size: 12px; color: #909399; margin-bottom: 8px; }
.preview-slots { display: flex; flex-wrap: wrap; gap: 4px; }
.preview-slot { padding: 4px 8px; border-radius: 4px; font-size: 11px; display: flex; flex-direction: column; align-items: center; min-width: 50px; }
.slot-type-class { background: #ecf5ff; color: #409EFF; }
.slot-type-break { background: #f0f9eb; color: #67C23A; }
.slot-type-lunch { background: #fdf6ec; color: #E6A23C; }
.slot-type-evening { background: #f3e8ff; color: #9C27B0; }
.slot-label { font-weight: 600; }
.slot-time { font-size: 10px; opacity: 0.8; }
.preview-more { font-size: 12px; color: #909399; display: flex; align-items: center; }
.preview-empty { font-size: 13px; color: #c0c4cc; text-align: center; padding: 12px 0; }
</style>

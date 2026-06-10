<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">换课列表</h2>
      <el-button type="primary" @click="$router.push('/swap/request')">
        <el-icon><Plus /></el-icon>申请换课
      </el-button>
    </div>

    <div class="search-bar">
      <el-select v-model="searchStatus" placeholder="状态筛选" clearable @change="loadData" style="width: 130px;">
        <el-option label="待审批" value="pending" />
        <el-option label="已通过" value="approved" />
        <el-option label="已拒绝" value="rejected" />
        <el-option label="已取消" value="cancelled" />
      </el-select>
    </div>

    <el-table :data="swapList" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="id" label="编号" width="70" />
      <el-table-column label="换出课程" min-width="180">
        <template #default="{ row }">
          <div>
            <strong>{{ row.sourceSubject }}</strong>
            <span style="color: #909399; margin-left: 4px;">{{ row.sourceClassName }}</span>
          </div>
          <div style="font-size: 12px; color: #909399;">
            {{ getDayOfWeek(row.sourceDayOfWeek) }} 第{{ row.sourcePeriodIndex }}节
          </div>
        </template>
      </el-table-column>
      <el-table-column label="换入课程" min-width="180">
        <template #default="{ row }">
          <div>
            <strong>{{ row.targetSubject }}</strong>
            <span style="color: #909399; margin-left: 4px;">{{ row.targetTeacherName }}</span>
          </div>
          <div style="font-size: 12px; color: #909399;">
            {{ getDayOfWeek(row.targetDayOfWeek) }} 第{{ row.targetPeriodIndex }}节
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="reason" label="原因" min-width="140" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createdAt" label="申请时间" width="160" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'pending' && row.targetTeacherId === currentUserId">
            <el-button size="small" type="success" @click="handleApprove(row)">同意</el-button>
            <el-button size="small" type="danger" @click="handleReject(row)">拒绝</el-button>
          </template>
          <el-button
            v-if="row.status === 'pending' && row.requesterId === currentUserId"
            size="small"
            text
            type="warning"
            @click="handleCancel(row)"
          >
            取消
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useUserStore } from '../../stores/user'
import { getSwapRequests, approveSwap, rejectSwap, cancelSwap } from '../../api/swap'
import { getDayOfWeek } from '../../utils/format'
import { ElMessage, ElMessageBox } from 'element-plus'

const userStore = useUserStore()
const currentUserId = computed(() => userStore.userInfo.id)
const loading = ref(false)
const swapList = ref([])
const searchStatus = ref('')
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

function statusType(status) {
  const map = { pending: 'warning', approved: 'success', rejected: 'danger', cancelled: 'info' }
  return map[status] || 'info'
}

function statusLabel(status) {
  const map = { pending: '待审批', approved: '已通过', rejected: '已拒绝', cancelled: '已取消' }
  return map[status] || status
}

async function loadData() {
  loading.value = true
  try {
    const res = await getSwapRequests({
      page: pagination.page,
      pageSize: pagination.pageSize,
      status: searchStatus.value || undefined
    })
    swapList.value = res.data?.list || res.data || []
    pagination.total = res.data?.total || 0
  } catch (e) { console.error('加载换课列表失败', e) } finally { loading.value = false }
}

async function handleApprove(row) {
  try {
    await ElMessageBox.confirm('确定同意此换课请求吗？', '确认', { confirmButtonText: '同意', cancelButtonText: '取消', type: 'info' })
    await approveSwap(row.id)
    ElMessage.success('已同意换课'); loadData()
  } catch (e) { if (e !== 'cancel') console.error('操作失败', e) }
}

async function handleReject(row) {
  try {
    const { value } = await ElMessageBox.prompt('请输入拒绝原因', '拒绝换课', { confirmButtonText: '确定', cancelButtonText: '取消', inputPlaceholder: '拒绝原因' })
    await rejectSwap(row.id, { reason: value })
    ElMessage.success('已拒绝换课'); loadData()
  } catch (e) { if (e !== 'cancel') console.error('操作失败', e) }
}

async function handleCancel(row) {
  try {
    await ElMessageBox.confirm('确定要取消此换课请求吗？', '确认', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    await cancelSwap(row.id)
    ElMessage.success('已取消'); loadData()
  } catch (e) { if (e !== 'cancel') console.error('操作失败', e) }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">换课记录</h2>
    </div>

    <div class="search-bar">
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        @change="loadData"
        style="width: 280px;"
      />
      <el-select v-model="searchStatus" placeholder="状态" clearable @change="loadData" style="width: 120px;">
        <el-option label="已通过" value="approved" />
        <el-option label="已拒绝" value="rejected" />
        <el-option label="已取消" value="cancelled" />
      </el-select>
    </div>

    <el-table :data="historyList" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="id" label="编号" width="70" />
      <el-table-column label="申请人" width="100">
        <template #default="{ row }">{{ row.requesterName }}</template>
      </el-table-column>
      <el-table-column label="换出" min-width="160">
        <template #default="{ row }">
          <div><strong>{{ row.sourceSubject }}</strong> - {{ row.sourceClassName }}</div>
          <div style="font-size: 12px; color: #909399;">{{ getDayOfWeek(row.sourceDayOfWeek) }} 第{{ row.sourcePeriodIndex }}节</div>
        </template>
      </el-table-column>
      <el-table-column label="换入" min-width="160">
        <template #default="{ row }">
          <div><strong>{{ row.targetSubject }}</strong> - {{ row.targetTeacherName }}</div>
          <div style="font-size: 12px; color: #909399;">{{ getDayOfWeek(row.targetDayOfWeek) }} 第{{ row.targetPeriodIndex }}节</div>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="processedByName" label="处理人" width="100" />
      <el-table-column prop="processedAt" label="处理时间" width="160" />
      <el-table-column prop="rejectReason" label="拒绝原因" min-width="120" show-overflow-tooltip />
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
import { ref, reactive, onMounted } from 'vue'
import { getSwapHistory } from '../../api/swap'
import { getDayOfWeek } from '../../utils/format'

const loading = ref(false)
const historyList = ref([])
const searchStatus = ref('')
const dateRange = ref(null)
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

function statusType(status) {
  const map = { approved: 'success', rejected: 'danger', cancelled: 'info' }
  return map[status] || 'info'
}

function statusLabel(status) {
  const map = { approved: '已通过', rejected: '已拒绝', cancelled: '已取消' }
  return map[status] || status
}

async function loadData() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      pageSize: pagination.pageSize,
      status: searchStatus.value || undefined
    }
    if (dateRange.value && dateRange.value.length === 2) {
      params.startDate = dateRange.value[0]
      params.endDate = dateRange.value[1]
    }
    const res = await getSwapHistory(params)
    historyList.value = res.data?.list || res.data || []
    pagination.total = res.data?.total || 0
  } catch (e) { console.error('加载换课记录失败', e) } finally { loading.value = false }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>

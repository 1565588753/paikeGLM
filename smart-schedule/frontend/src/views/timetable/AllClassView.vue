<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">全校课表总览</h2>
      <div class="no-print">
        <el-button @click="handlePrint"><el-icon><Printer /></el-icon>打印</el-button>
        <el-button @click="handleExport"><el-icon><Download /></el-icon>导出</el-button>
      </div>
    </div>

    <div class="search-bar no-print">
      <el-select v-model="searchGrade" placeholder="筛选年级" clearable @change="loadData" style="width: 130px;">
        <el-option v-for="g in grades" :key="g" :label="g + '年级'" :value="g" />
      </el-select>
      <el-radio-group v-model="weekFilter" @change="filterData">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="odd">单周</el-radio-button>
        <el-radio-button value="even">双周</el-radio-button>
      </el-radio-group>
    </div>

    <div class="all-classes-grid" v-loading="loading">
      <el-card v-for="cls in displayClasses" :key="cls.id" shadow="hover" class="class-card">
        <template #header>
          <div class="class-card-header">
            <span class="class-name">{{ cls.name }}</span>
            <el-button text type="primary" size="small" @click="viewClassDetail(cls)">查看详情</el-button>
          </div>
        </template>
        <div class="mini-timetable">
          <div class="mini-header">
            <div class="mini-corner"></div>
            <div v-for="day in shortDays" :key="day" class="mini-day">{{ day }}</div>
          </div>
          <div v-for="p in 8" :key="p" class="mini-row">
            <div class="mini-period">{{ p }}</div>
            <div v-for="(day, dIdx) in shortDays" :key="dIdx" class="mini-cell">
              <div
                v-if="getClassCourse(cls.id, p, dIdx + 1)"
                class="mini-course"
                :style="{ background: getSubjectColorByName(getClassCourse(cls.id, p, dIdx + 1).subjectName) + '30', borderLeftColor: getSubjectColorByName(getClassCourse(cls.id, p, dIdx + 1).subjectName) }"
                :title="`${getClassCourse(cls.id, p, dIdx + 1).subjectName} - ${getClassCourse(cls.id, p, dIdx + 1).teacherName}`"
              >
                {{ getClassCourse(cls.id, p, dIdx + 1).subjectName?.charAt(0) }}
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <el-empty v-if="!loading && displayClasses.length === 0" description="暂无课表数据" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getAllClassTimetables } from '../../api/timetable'
import { getClasses } from '../../api/class'
import { getSubjectColorByName } from '../../utils/format'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const searchGrade = ref('')
const weekFilter = ref('all')
const allClasses = ref([])
const allTimetableData = ref({})
const filteredTimetableData = ref({})
const grades = [1, 2, 3, 4, 5, 6, 7, 8, 9]
const shortDays = ['一', '二', '三', '四', '五']

const displayClasses = computed(() => {
  if (!searchGrade.value) return allClasses.value
  return allClasses.value.filter(c => c.grade === searchGrade.value)
})

function getClassCourse(classId, periodIndex, dayOfWeek) {
  const data = filteredTimetableData.value[classId]
  if (!data) return null
  return data.find(c => c.periodIndex === periodIndex && c.dayOfWeek === dayOfWeek)
}

function filterData() {
  const filtered = {}
  Object.keys(allTimetableData.value).forEach(classId => {
    const data = allTimetableData.value[classId]
    if (weekFilter.value === 'all') {
      filtered[classId] = data
    } else {
      filtered[classId] = data.filter(c => c.weekType === weekFilter.value || c.weekType === 'all')
    }
  })
  filteredTimetableData.value = filtered
}

async function loadData() {
  loading.value = true
  try {
    const [clsRes, ttRes] = await Promise.all([
      getClasses({ pageSize: 999, grade: searchGrade.value || undefined }),
      getAllClassTimetables({ grade: searchGrade.value || undefined })
    ])
    allClasses.value = clsRes.data?.list || clsRes.data || []
    allTimetableData.value = ttRes.data || {}
    filterData()
  } catch (e) { console.error('加载全校课表失败', e) } finally { loading.value = false }
}

function viewClassDetail(cls) {
  router.push({ path: '/timetable/class', query: { classId: cls.id } })
}

function handlePrint() { window.print() }
function handleExport() { ElMessage.info('导出全校课表...'); window.print() }

onMounted(() => { loadData() })
</script>

<style scoped>
.all-classes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.class-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.class-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.mini-timetable {
  font-size: 11px;
}

.mini-header {
  display: grid;
  grid-template-columns: 24px repeat(5, 1fr);
  gap: 1px;
  margin-bottom: 2px;
}

.mini-corner, .mini-day {
  text-align: center;
  font-weight: 600;
  color: #909399;
  padding: 2px;
  font-size: 10px;
}

.mini-row {
  display: grid;
  grid-template-columns: 24px repeat(5, 1fr);
  gap: 1px;
  margin-bottom: 1px;
}

.mini-period {
  text-align: center;
  color: #c0c4cc;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mini-cell {
  min-height: 18px;
  background: #fafafa;
  border-radius: 2px;
}

.mini-course {
  height: 100%;
  min-height: 18px;
  border-left: 2px solid;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  color: #303133;
  cursor: default;
}

@media (max-width: 768px) {
  .all-classes-grid {
    grid-template-columns: 1fr;
  }
}
</style>

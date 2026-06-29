<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">记录查询</h2>
      <div class="page-header-actions">
        <el-switch
          v-if="authStore.isAdmin"
          v-model="showDeleted"
          inline-prompt
          active-text="显示已删"
          inactive-text="隐藏已删"
          @change="loadData"
          style="margin-right: 12px;"
        />
        <el-button v-if="authStore.isAdmin && showDeleted" @click="onBatchRestore" :disabled="!selectedIds.length" :loading="restoring">
          <el-icon><RefreshLeft /></el-icon>
          <span>恢复选中 ({{ selectedIds.length }})</span>
        </el-button>
        <el-button v-if="authStore.isAdmin && !showDeleted" type="danger" @click="onBatchDelete" :disabled="!selectedIds.length" :loading="deleting">
          <el-icon><Delete /></el-icon>
          <span>删除选中 ({{ selectedIds.length }})</span>
        </el-button>
        <el-button v-if="authStore.isSupervisor" type="primary" @click="onExport" :loading="exporting">
          <el-icon><Download /></el-icon>
          <span>导出 Excel</span>
        </el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <el-card shadow="never" style="margin-bottom: 16px;">
      <el-form :inline="true" :model="filters" @submit.prevent="loadData">
        <el-form-item label="车牌">
          <el-input v-model="filters.plate_number" placeholder="模糊匹配" clearable style="width: 140px;" />
        </el-form-item>
        <el-form-item label="岗亭">
          <el-select v-model="filters.post_id" placeholder="全部" clearable style="width: 130px;">
            <el-option v-for="p in posts" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.vehicle_type" placeholder="全部" clearable style="width: 120px;">
            <el-option v-for="item in vehicleTypes" :key="item.code" :label="item.name" :value="item.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.approval_status" placeholder="全部" clearable style="width: 120px;">
            <el-option label="待审批" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已驳回" value="rejected" />
            <el-option label="已超时" value="timeout" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            style="width: 240px;"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="onReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="never">
      <el-table
        :data="records"
        v-loading="loading"
        stripe
        @row-click="onRowClick"
        @selection-change="onSelectionChange"
        style="cursor: pointer;"
        :row-class-name="rowClass"
      >
        <el-table-column v-if="authStore.isAdmin" type="selection" width="48" :selectable="canSelect" />
        <el-table-column label="车牌" prop="plate_number" width="120">
          <template #default="{ row }">
            <strong style="font-size: 14px;">{{ row.plate_number }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="类型" prop="vehicle_type" width="90">
          <template #default="{ row }">
            <el-tag :type="typeTagType(row.vehicle_type)" size="small">{{ typeLabel(row.vehicle_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="方向" prop="direction" width="70">
          <template #default="{ row }">
            <el-tag :type="row.direction === 'in' ? 'success' : 'warning'" size="small">
              {{ row.direction === 'in' ? '进场' : '出场' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="岗亭" prop="post_id" width="100">
          <template #default="{ row }">
            {{ postName(row.post_id) }}
          </template>
        </el-table-column>
        <el-table-column label="操作人" prop="operator_name" width="100" />
        <el-table-column label="进场时间" prop="in_time" width="160">
          <template #default="{ row }">{{ formatTime(row.in_time) }}</template>
        </el-table-column>
        <el-table-column label="出场时间" prop="out_time" width="160">
          <template #default="{ row }">{{ formatTime(row.out_time) }}</template>
        </el-table-column>
        <el-table-column label="停留(分)" prop="loading_duration" width="80" />
        <el-table-column label="审批人" prop="approver_name" width="90" />
        <el-table-column label="状态" prop="approval_status" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.approval_status)" size="small">
              {{ statusLabel(row.approval_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column v-if="showDeleted" label="删除信息" width="240">
          <template #default="{ row }">
            <div style="font-size: 12px; line-height: 1.6;">
              <div><el-tag type="info" size="small">已删</el-tag></div>
              <div style="color: #909399;">{{ formatTime(row.deleted_at) }} · {{ row.deleted_by_name }}</div>
              <div style="color: #606266;">原因：{{ row.deleted_reason || '-' }}</div>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="filters.page"
        v-model:page-size="filters.page_size"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="loadData"
        @size-change="loadData"
        style="margin-top: 16px; justify-content: flex-end;"
      />
    </el-card>

    <!-- 删除确认对话框 -->
    <el-dialog v-model="deleteDialogVisible" title="删除记录" width="520px" :close-on-click-modal="false">
      <el-alert type="warning" :closable="false" show-icon style="margin-bottom: 16px;">
        <template #title>
          即将软删除 {{ selectedIds.length }} 条记录
        </template>
        <div class="alert-text">
          · 删除后记录会从默认列表隐藏，但 <b>数据不丢失</b>，可在「显示已删」里看到和恢复<br>
          · 每条记录的完整快照会写入审计日志（含原因 + 操作人）<br>
          · <b>已审批通过且已匹配出场的进记录</b>默认受保护，需勾选「强制删除」才能删<br>
          · 必填删除原因，建议尽量具体（便于后续追溯）
        </div>
      </el-alert>

      <el-form label-width="80px">
        <el-form-item label="删除原因" required>
          <el-input
            v-model="deleteReason"
            type="textarea"
            :rows="3"
            maxlength="200"
            show-word-limit
            placeholder="例如：测试数据清理 / 录入错误纠正 / 重复提交"
          />
        </el-form-item>
        <el-form-item v-if="hasLocked" label="强制删除">
          <el-switch v-model="forceDelete" />
          <span class="form-hint">包含已审批+已匹配的记录</span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="deleting" @click="confirmDelete">确认删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Delete, RefreshLeft } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { useAuthStore } from '@/stores/auth'
import { listPostsApi } from '@/api'
import { listRecordsApi, exportExcelApi, batchDeleteRecordsApi, restoreRecordApi } from '@/api/records'
import { listActiveVehicleTypesApi } from '@/api/vehicle_types'

const router = useRouter()
const authStore = useAuthStore()
const records = ref([])
const total = ref(0)
const loading = ref(false)
const exporting = ref(false)
const restoring = ref(false)
const deleting = ref(false)
const posts = ref([])
const vehicleTypes = ref([])
const dateRange = ref([])
const selectedIds = ref([])
const showDeleted = ref(false)

const filters = reactive({
  page: 1,
  page_size: 20,
  plate_number: '',
  post_id: null,
  vehicle_type: '',
  approval_status: '',
  start_date: '',
  end_date: '',
})

// 删除对话框
const deleteDialogVisible = ref(false)
const deleteReason = ref('')
const forceDelete = ref(false)

const hasLocked = computed(() =>
  records.value
    .filter((r) => selectedIds.value.includes(r.id))
    .some((r) => r.approval_status === 'approved' && r.direction === 'in' && r.companion_id)
)

function postName(id) {
  return posts.value.find(p => p.id === id)?.name || '-'
}
function typeLabel(t) {
  const found = vehicleTypes.value.find(item => item.code === t)
  return found ? found.name : t
}
function typeTagType(t) { return { internal: 'info', external: '', truck: 'warning' }[t] || '' }
function statusLabel(s) { return { pending: '待审批', approved: '已通过', rejected: '已驳回', timeout: '已超时' }[s] || s }
function statusTagType(s) { return { pending: 'warning', approved: 'success', rejected: 'danger', timeout: 'info' }[s] || '' }
function formatTime(t) { return t ? dayjs(t).format('MM-DD HH:mm:ss') : '-' }

function canSelect(row) {
  // 已删的不能再选（避免重复删）
  return !row.is_deleted
}

function rowClass({ row }) {
  return row.is_deleted ? 'is-deleted-row' : ''
}

function onRowClick(row, column, event) {
  // 复选框列点击不跳转
  if (column && column.type === 'selection') return
  router.push(`/records/${row.id}`)
}

function onSelectionChange(rows) {
  selectedIds.value = rows.map((r) => r.id)
}

async function loadData() {
  loading.value = true
  try {
    if (dateRange.value && dateRange.value.length === 2) {
      filters.start_date = dateRange.value[0]
      filters.end_date = dateRange.value[1]
    } else {
      filters.start_date = ''
      filters.end_date = ''
    }
    const res = await listRecordsApi({ ...filters, include_deleted: showDeleted.value })
    records.value = res.data.items || []
    total.value = res.data.total || 0
    selectedIds.value = []  // 切视图时清空选中
  } catch (e) {} finally {
    loading.value = false
  }
}

function onReset() {
  Object.assign(filters, { page: 1, page_size: 20, plate_number: '', post_id: null, vehicle_type: '', approval_status: '', start_date: '', end_date: '' })
  dateRange.value = []
  loadData()
}

async function onExport() {
  exporting.value = true
  try {
    const params = { ...filters, include_deleted: showDeleted.value }
    delete params.page
    delete params.page_size
    const res = await exportExcelApi(params)
    const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `车辆记录_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('已导出')
  } catch (e) {
  } finally {
    exporting.value = false
  }
}

function onBatchDelete() {
  if (!selectedIds.value.length) {
    ElMessage.warning('请先勾选要删除的记录')
    return
  }
  deleteReason.value = ''
  forceDelete.value = false
  deleteDialogVisible.value = true
}

async function confirmDelete() {
  if (!deleteReason.value.trim()) {
    ElMessage.error('请填写删除原因')
    return
  }
  deleting.value = true
  try {
    const res = await batchDeleteRecordsApi({
      record_ids: selectedIds.value,
      reason: deleteReason.value.trim(),
      force: forceDelete.value,
    })
    const data = res.data
    if (data.deleted_count > 0) {
      ElMessage.success(`删除 ${data.deleted_count} 条` + (data.skipped_count > 0 ? `，跳过 ${data.skipped_count} 条（已审批+已匹配，需强制删除）` : ''))
      // 列出被跳过的原因
      if (data.skipped && data.skipped.length > 0 && data.skipped.length <= 10) {
        console.warn('Skipped records:', data.skipped)
      }
      deleteDialogVisible.value = false
      await loadData()
    } else if (data.skipped_count > 0) {
      ElMessage.warning(`全部 ${data.skipped_count} 条都被跳过：` + (data.skipped[0]?.reason || ''))
    }
  } catch (e) {
    // request 拦截器已弹错误
  } finally {
    deleting.value = false
  }
}

async function onBatchRestore() {
  if (!selectedIds.value.length) {
    ElMessage.warning('请先勾选要恢复的记录')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认恢复选中的 ${selectedIds.value.length} 条记录？恢复后会重新出现在默认列表。`,
      '恢复记录',
      { type: 'info' }
    )
    restoring.value = true
    let ok = 0
    let fail = 0
    for (const id of selectedIds.value) {
      try {
        await restoreRecordApi(id)
        ok++
      } catch (e) {
        fail++
      }
    }
    ElMessage.success(`恢复 ${ok} 条${fail ? `，失败 ${fail} 条` : ''}`)
    await loadData()
  } catch (e) {
    // cancel
  } finally {
    restoring.value = false
  }
}

onMounted(async () => {
  const [p, vt] = await Promise.all([listPostsApi(), listActiveVehicleTypesApi()])
  posts.value = p.data || []
  vehicleTypes.value = vt.data || []
  loadData()
})
</script>

<style scoped>
.page-header-actions {
  display: flex;
  align-items: center;
  gap: 0;
}
.alert-text {
  font-size: 13px;
  line-height: 1.9;
  margin-top: 6px;
}
.form-hint {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}
:deep(.is-deleted-row) {
  background-color: #fafafa !important;
  color: #c0c4cc;
  font-style: italic;
}
</style>

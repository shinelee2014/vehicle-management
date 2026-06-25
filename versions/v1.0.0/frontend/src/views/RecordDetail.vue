<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">记录详情</h2>
      <el-button @click="$router.back()">返回</el-button>
    </div>

    <el-card v-loading="loading" shadow="never">
      <template v-if="record">
        <!-- 状态徽标 -->
        <div class="status-bar">
          <el-tag :type="statusTagType(record.approval_status)" size="large">
            {{ statusLabel(record.approval_status) }}
          </el-tag>
          <span class="record-no">业务编号：{{ record.record_no }}</span>
        </div>

        <!-- 审批操作（仅审批人） -->
        <div v-if="canApprove" class="approval-actions">
          <el-button type="success" size="large" @click="onApprove">✓ 通过</el-button>
          <el-button type="danger" size="large" @click="onReject">✗ 驳回</el-button>
        </div>

        <el-divider />

        <!-- 基础信息 -->
        <el-descriptions title="基础信息" :column="2" border>
          <el-descriptions-item label="车牌号">{{ record.plate_number }}</el-descriptions-item>
          <el-descriptions-item label="车辆类型">
            <el-tag :type="typeTagType(record.vehicle_type)">{{ typeLabel(record.vehicle_type) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="方向">
            <el-tag :type="record.direction === 'in' ? 'success' : 'warning'">
              {{ record.direction === 'in' ? '进场' : '出场' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="岗亭">岗亭 #{{ record.post_id }}</el-descriptions-item>
          <el-descriptions-item label="操作人">{{ record.operator_name }}</el-descriptions-item>
          <el-descriptions-item label="审批人">{{ record.approver_name }}</el-descriptions-item>
          <el-descriptions-item label="进场时间">{{ formatTime(record.in_time) }}</el-descriptions-item>
          <el-descriptions-item label="出场时间">{{ formatTime(record.out_time) }}</el-descriptions-item>
          <el-descriptions-item v-if="record.cargo_info" label="货物" :span="2">{{ record.cargo_info }}</el-descriptions-item>
          <el-descriptions-item v-if="record.in_remark" label="进场备注" :span="2">{{ record.in_remark }}</el-descriptions-item>
          <el-descriptions-item v-if="record.out_remark" label="出场备注" :span="2">{{ record.out_remark }}</el-descriptions-item>
          <el-descriptions-item v-if="record.loading_duration" label="停留时长">{{ record.loading_duration }} 分钟</el-descriptions-item>
          <el-descriptions-item v-if="record.approval_time" label="审批时间">{{ formatTime(record.approval_time) }}</el-descriptions-item>
          <el-descriptions-item v-if="record.approval_remark" label="审批意见" :span="2">{{ record.approval_remark }}</el-descriptions-item>
        </el-descriptions>

        <!-- 照片 -->
        <template v-if="record.in_photos && record.in_photos.length > 0">
          <h3 style="margin-top: 24px;">📸 进场照片</h3>
          <div class="photo-grid">
            <div v-for="p in record.in_photos" :key="p.url" class="photo-cell">
              <el-image :src="fullUrl(p.url)" :preview-src-list="[fullUrl(p.url)]" fit="cover" />
              <div class="photo-kind">{{ kindLabel(p.kind) }}</div>
            </div>
          </div>
        </template>

        <template v-if="record.out_photos && record.out_photos.length > 0">
          <h3 style="margin-top: 24px;">📸 出场照片</h3>
          <div class="photo-grid">
            <div v-for="p in record.out_photos" :key="p.url" class="photo-cell">
              <el-image :src="fullUrl(p.url)" :preview-src-list="[fullUrl(p.url)]" fit="cover" />
              <div class="photo-kind">{{ kindLabel(p.kind) }}</div>
            </div>
          </div>
        </template>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import { getRecordApi, approveApi, rejectApi } from '@/api/records'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const record = ref(null)
const loading = ref(false)

const canApprove = computed(() => {
  if (!record.value) return false
  return (
    record.value.approver_id === authStore.user?.id &&
    record.value.approval_status === 'pending'
  )
})

function fullUrl(url) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return url.startsWith('/') ? url : `/${url}`
}

function typeLabel(t) {
  return { internal: '内部车', external: '外部车', truck: '货车' }[t] || t
}
function typeTagType(t) {
  return { internal: 'info', external: '', truck: 'warning' }[t] || ''
}
function statusLabel(s) {
  return { pending: '待审批', approved: '已通过', rejected: '已驳回', timeout: '已超时' }[s] || s
}
function statusTagType(s) {
  return { pending: 'warning', approved: 'success', rejected: 'danger', timeout: 'info' }[s] || ''
}
function kindLabel(k) {
  return { front: '车前', plate: '车牌', side: '侧面', other: '其他' }[k] || k
}
function formatTime(t) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm:ss') : '-'
}

async function loadData() {
  loading.value = true
  try {
    const res = await getRecordApi(route.params.id)
    record.value = res.data
  } catch (e) {
    router.push('/records')
  } finally {
    loading.value = false
  }
}

async function onApprove() {
  try {
    const { value: remark } = await ElMessageBox.prompt('审批意见（可选）', '通过审批', { confirmButtonText: '确定', cancelButtonText: '取消' })
    await approveApi(record.value.id, { action: 'approve', remark })
    ElMessage.success('已通过')
    loadData()
  } catch (e) {}
}

async function onReject() {
  try {
    const { value: remark } = await ElMessageBox.prompt('驳回原因', '驳回', { confirmButtonText: '确定', cancelButtonText: '取消', inputValidator: (v) => !!v || '请填写驳回原因' })
    await rejectApi(record.value.id, { action: 'reject', remark })
    ElMessage.success('已驳回')
    loadData()
  } catch (e) {}
}

onMounted(loadData)
</script>

<style scoped>
.status-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}
.record-no {
  font-size: 13px;
  color: #909399;
}
.approval-actions {
  margin: 16px 0;
  display: flex;
  gap: 12px;
}
.photo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.photo-cell {
  text-align: center;
}
.photo-cell :deep(.el-image) {
  width: 100%;
  height: 180px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}
.photo-kind {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>

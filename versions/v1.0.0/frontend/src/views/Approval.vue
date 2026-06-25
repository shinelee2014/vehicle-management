<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">待我审批</h2>
      <el-tag size="large" type="danger" v-if="total > 0">{{ total }} 条待处理</el-tag>
    </div>

    <div v-if="loading && items.length === 0" class="empty-tip">加载中...</div>
    <div v-else-if="items.length === 0" class="empty-tip">
      <el-empty description="暂无待审批记录" />
    </div>

    <div v-else>
      <el-card v-for="r in items" :key="r.id" shadow="never" class="approval-card">
        <div class="card-head">
          <div>
            <span class="plate">{{ r.plate_number }}</span>
            <el-tag :type="typeTagType(r.vehicle_type)" size="small" style="margin-left: 8px;">{{ typeLabel(r.vehicle_type) }}</el-tag>
            <el-tag :type="r.direction === 'in' ? 'success' : 'warning'" size="small" style="margin-left: 4px;">
              {{ r.direction === 'in' ? '进场' : '出场' }}
            </el-tag>
            <span v-if="r.loading_duration" class="duration">已停留 {{ r.loading_duration }} 分钟</span>
          </div>
          <el-button text @click="$router.push(`/records/${r.id}`)">查看详情 →</el-button>
        </div>

        <el-descriptions :column="2" size="small" style="margin-top: 12px;">
          <el-descriptions-item label="操作人">{{ r.operator_name }}</el-descriptions-item>
          <el-descriptions-item label="岗亭">岗亭 #{{ r.post_id }}</el-descriptions-item>
          <el-descriptions-item label="进场时间">{{ formatTime(r.in_time) }}</el-descriptions-item>
          <el-descriptions-item label="出场时间">{{ formatTime(r.out_time) }}</el-descriptions-item>
          <el-descriptions-item v-if="r.cargo_info" label="货物" :span="2">{{ r.cargo_info }}</el-descriptions-item>
          <el-descriptions-item v-if="r.in_remark" label="进场备注" :span="2">{{ r.in_remark }}</el-descriptions-item>
          <el-descriptions-item v-if="r.out_remark" label="出场备注" :span="2">{{ r.out_remark }}</el-descriptions-item>
        </el-descriptions>

        <div class="card-photos" v-if="r.in_photos && r.in_photos.length > 0">
          <el-image
            v-for="p in r.in_photos"
            :key="p.url"
            :src="p.url"
            :preview-src-list="[p.url]"
            :initial-index="0"
            fit="cover"
            class="thumb"
          />
        </div>

        <div class="card-actions">
          <el-button type="success" @click="onApprove(r)">✓ 通过</el-button>
          <el-button type="danger" @click="onReject(r)">✗ 驳回</el-button>
        </div>
      </el-card>

      <el-pagination
        v-model:current-page="page"
        :total="total"
        :page-size="page_size"
        layout="total, prev, pager, next"
        @current-change="loadData"
        style="margin-top: 16px; justify-content: center;"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import { pendingApprovalApi, approveApi, rejectApi } from '@/api/records'

const items = ref([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const page_size = 20

function typeLabel(t) { return { internal: '内部车', external: '外部车', truck: '货车' }[t] || t }
function typeTagType(t) { return { internal: 'info', external: '', truck: 'warning' }[t] || '' }
function formatTime(t) { return t ? dayjs(t).format('MM-DD HH:mm:ss') : '-' }

async function loadData() {
  loading.value = true
  try {
    const res = await pendingApprovalApi({ page: page.value, page_size })
    items.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (e) {
  } finally {
    loading.value = false
  }
}

async function onApprove(r) {
  try {
    const { value: remark } = await ElMessageBox.prompt('审批意见（可选）', '通过审批', { confirmButtonText: '确定', cancelButtonText: '取消' })
    await approveApi(r.id, { action: 'approve', remark })
    ElMessage.success('已通过')
    loadData()
  } catch (e) {}
}

async function onReject(r) {
  try {
    const { value: remark } = await ElMessageBox.prompt('驳回原因（必填）', '驳回', { confirmButtonText: '确定', cancelButtonText: '取消', inputValidator: (v) => !!v || '请填写驳回原因' })
    await rejectApi(r.id, { action: 'reject', remark })
    ElMessage.success('已驳回')
    loadData()
  } catch (e) {}
}

onMounted(loadData)
</script>

<style scoped>
.empty-tip {
  padding: 40px 0;
  text-align: center;
}
.approval-card {
  margin-bottom: 12px;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.plate {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 1px;
}
.duration {
  margin-left: 12px;
  color: #909399;
  font-size: 13px;
}
.card-photos {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
.thumb {
  width: 100px;
  height: 75px;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}
.card-actions {
  margin-top: 16px;
  text-align: right;
  border-top: 1px solid #ebeef5;
  padding-top: 12px;
}
</style>

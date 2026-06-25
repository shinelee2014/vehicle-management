<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">消息中心</h2>
      <el-button v-if="unreadCount > 0" @click="onMarkAllRead">全部已读</el-button>
    </div>

    <el-tabs v-model="filter" @tab-change="loadData">
      <el-tab-pane :label="`全部 (${total})`" name="all" />
      <el-tab-pane :label="`未读 (${unreadCount})`" name="unread" />
    </el-tabs>

    <div v-if="loading && items.length === 0" class="empty-tip">加载中...</div>
    <div v-else-if="items.length === 0" class="empty-tip">
      <el-empty description="暂无消息" />
    </div>

    <el-card v-for="m in items" :key="m.id" shadow="never" class="msg-card" :class="{ unread: !m.is_read }">
      <div class="msg-head">
        <div>
          <el-tag size="small" :type="typeTagType(m.type)">{{ typeLabel(m.type) }}</el-tag>
          <span class="msg-title">{{ m.title }}</span>
        </div>
        <span class="msg-time">{{ formatTime(m.created_at) }}</span>
      </div>
      <div class="msg-content">{{ m.content }}</div>
      <div class="msg-actions">
        <el-button v-if="!m.is_read" size="small" @click="onMarkRead(m)">标记已读</el-button>
        <el-button v-if="m.related_record_id" size="small" type="primary" @click="$router.push(`/records/${m.related_record_id}`)">查看记录</el-button>
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
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { listMessagesApi, unreadCountApi, markReadApi, markAllReadApi } from '@/api'

const items = ref([])
const total = ref(0)
const unreadCount = ref(0)
const loading = ref(false)
const filter = ref('all')
const page = ref(1)
const page_size = 20

function typeLabel(t) {
  return { approval_request: '待审批', approval_result: '审批结果', system: '系统通知', announcement: '公告' }[t] || t
}
function typeTagType(t) {
  return { approval_request: 'warning', approval_result: 'success', system: 'info', announcement: '' }[t] || ''
}
function formatTime(t) { return t ? dayjs(t).format('YYYY-MM-DD HH:mm') : '' }

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size }
    if (filter.value === 'unread') params.is_read = false
    const [msgs, unread] = await Promise.all([
      listMessagesApi(params),
      unreadCountApi(),
    ])
    items.value = msgs.data.items || []
    total.value = msgs.data.total || 0
    unreadCount.value = unread.data.unread || 0
  } catch (e) {} finally {
    loading.value = false
  }
}

async function onMarkRead(m) {
  try {
    await markReadApi(m.id)
    m.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
    ElMessage.success('已标记已读')
  } catch (e) {}
}

async function onMarkAllRead() {
  try {
    await markAllReadApi()
    ElMessage.success('全部已读')
    page.value = 1
    loadData()
  } catch (e) {}
}

onMounted(loadData)
</script>

<style scoped>
.empty-tip { padding: 40px 0; text-align: center; }
.msg-card {
  margin-bottom: 12px;
  transition: all 0.2s;
}
.msg-card.unread {
  border-left: 3px solid #409eff;
  background: #f0f9ff;
}
.msg-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.msg-title {
  margin-left: 8px;
  font-size: 15px;
  font-weight: 500;
}
.msg-time {
  font-size: 12px;
  color: #909399;
}
.msg-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  white-space: pre-line;
}
.msg-actions {
  margin-top: 12px;
  text-align: right;
}
</style>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">审计日志</h2>
    </div>

    <el-card shadow="never">
      <el-form :inline="true" :model="filters" style="margin-bottom: 12px;">
        <el-form-item label="操作类型">
          <el-select v-model="filters.action" placeholder="全部" clearable style="width: 160px;">
            <el-option label="登录" value="login" />
            <el-option label="登出" value="logout" />
            <el-option label="进场登记" value="create_in_record" />
            <el-option label="出场登记" value="create_out_record" />
            <el-option label="审批通过" value="approve" />
            <el-option label="审批驳回" value="reject" />
            <el-option label="导出" value="export" />
          </el-select>
        </el-form-item>
        <el-form-item label="结果">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 120px;">
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="onReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户" width="100" />
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-tag size="small">{{ actionLabel(row.action) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="对象" width="120">
          <template #default="{ row }">
            <span v-if="row.target_type">{{ row.target_type }} #{{ row.target_id }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="结果" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP" width="120" />
        <el-table-column label="详情" min-width="200">
          <template #default="{ row }">
            <span v-if="row.error_message" style="color: #f56c6c;">{{ row.error_message }}</span>
            <span v-else-if="row.details" style="color: #606266; font-family: monospace; font-size: 12px;">{{ JSON.stringify(row.details) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="160">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="filters.page"
        v-model:page-size="filters.page_size"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadData"
        @size-change="loadData"
        style="margin-top: 16px; justify-content: flex-end;"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import dayjs from 'dayjs'
import request from '@/api/request'

const items = ref([])
const total = ref(0)
const loading = ref(false)
const filters = reactive({ page: 1, page_size: 20, action: '', status: '' })

function actionLabel(a) {
  const m = {
    login: '登录', logout: '登出',
    create_in_record: '进场登记', create_out_record: '出场登记',
    approve: '审批通过', reject: '审批驳回',
    export: '导出', create_user: '新建用户', update_user: '更新用户',
    delete_user: '删除用户', reset_password: '重置密码',
    change_password: '修改密码', create_post: '新建岗亭',
  }
  return m[a] || a
}
function formatTime(t) { return t ? dayjs(t).format('YYYY-MM-DD HH:mm:ss') : '-' }

async function loadData() {
  loading.value = true
  try {
    const res = await request.get('/audit-logs', { params: filters })
    items.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (e) {} finally { loading.value = false }
}

function onReset() {
  Object.assign(filters, { page: 1, page_size: 20, action: '', status: '' })
  loadData()
}

onMounted(loadData)
</script>

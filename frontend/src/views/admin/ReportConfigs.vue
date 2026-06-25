<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">推送配置</h2>
      <el-button type="primary" @click="onAdd">
        <el-icon><Plus /></el-icon>
        <span>新建配置</span>
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" width="120" />
        <el-table-column label="频率" width="100">
          <template #default="{ row }">
            <el-tag :type="row.frequency === 'daily' ? 'success' : row.frequency === 'weekly' ? 'warning' : 'info'" size="small">
              {{ freqLabel(row.frequency) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="120">
          <template #default="{ row }">{{ row.run_time }}<span v-if="row.run_weekday"> · 周{{ row.run_weekday }}</span></template>
        </el-table-column>
        <el-table-column label="收件人" min-width="200">
          <template #default="{ row }">
            <el-tag v-for="uid in row.recipients" :key="uid" size="small" style="margin-right: 4px;">{{ userName(uid) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="onToggle(row)" />
          </template>
        </el-table-column>
        <el-table-column label="最后运行" width="160">
          <template #default="{ row }">{{ formatTime(row.last_run_at) || '尚未运行' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="onEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑配置' : '新建配置'" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="如：每日日报" />
        </el-form-item>
        <el-form-item label="频率" prop="frequency">
          <el-radio-group v-model="form.frequency">
            <el-radio value="daily">每日</el-radio>
            <el-radio value="weekly">每周</el-radio>
            <el-radio value="monthly">每月</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="时间" prop="run_time">
          <el-time-picker v-model="form.run_time" format="HH:mm" value-format="HH:mm:ss" placeholder="选择时间" />
        </el-form-item>
        <el-form-item v-if="form.frequency === 'weekly'" label="星期几" prop="run_weekday">
          <el-select v-model="form.run_weekday" placeholder="选择星期" style="width: 200px;">
            <el-option v-for="i in 7" :key="i" :label="`周${['一','二','三','四','五','六','日'][i-1]}`" :value="i" />
          </el-select>
        </el-form-item>
        <el-form-item label="收件人" prop="recipients">
          <el-select v-model="form.recipients" multiple filterable placeholder="选择收件人" style="width: 100%;">
            <el-option v-for="u in approverUsers" :key="u.id" :label="`${u.real_name}（${u.role}）`" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import request from '@/api/request'
import { listApproversApi, listUsersApi } from '@/api'

const items = ref([])
const users = ref([])
const approverUsers = ref([])
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const formRef = ref()
const form = reactive({
  name: '', frequency: 'daily', run_time: '18:00:00',
  run_weekday: null, recipients: [], enabled: true,
})
const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  frequency: [{ required: true, message: '请选择频率', trigger: 'change' }],
  run_time: [{ required: true, message: '请选择时间', trigger: 'change' }],
  recipients: [{ type: 'array', required: true, min: 1, message: '至少选一个收件人', trigger: 'change' }],
}

function freqLabel(f) { return { daily: '每日', weekly: '每周', monthly: '每月' }[f] || f }
function userName(id) {
  const u = users.value.find(x => x.id === id)
  return u ? u.real_name : `#${id}`
}
function formatTime(t) { return t ? dayjs(t).format('YYYY-MM-DD HH:mm') : '' }

async function loadData() {
  loading.value = true
  try {
    const [r1, r2, r3] = await Promise.all([
      request.get('/report-configs'),
      listUsersApi({ page: 1, page_size: 200 }),
      listApproversApi(),
    ])
    items.value = r1.data || []
    users.value = r2.data?.items || []
    approverUsers.value = r3.data || []
  } catch (e) {} finally { loading.value = false }
}

function onAdd() {
  editing.value = null
  Object.assign(form, { name: '', frequency: 'daily', run_time: '18:00:00', run_weekday: null, recipients: [], enabled: true })
  dialogVisible.value = true
}

function onEdit(row) {
  editing.value = row
  Object.assign(form, {
    name: row.name, frequency: row.frequency, run_time: row.run_time,
    run_weekday: row.run_weekday, recipients: row.recipients, enabled: row.enabled,
  })
  dialogVisible.value = true
}

async function onSubmit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    const payload = {
      name: form.name,
      frequency: form.frequency,
      run_time: typeof form.run_time === 'string' ? form.run_time : `${String(form.run_time.getHours()).padStart(2,'0')}:${String(form.run_time.getMinutes()).padStart(2,'0')}:00`,
      run_weekday: form.run_weekday,
      recipients: form.recipients,
      enabled: form.enabled,
    }
    if (editing.value) {
      await request.put(`/report-configs/${editing.value.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await request.post('/report-configs', payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {} finally { submitting.value = false }
}

async function onToggle(row) {
  try {
    await request.put(`/report-configs/${row.id}`, { enabled: row.enabled })
    ElMessage.success(row.enabled ? '已启用' : '已停用')
  } catch (e) {
    row.enabled = !row.enabled
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除「${row.name}」？`, '提示', { type: 'warning' })
    await request.delete(`/report-configs/${row.id}`)
    ElMessage.success('已删除')
    loadData()
  } catch (e) {}
}

onMounted(loadData)
</script>

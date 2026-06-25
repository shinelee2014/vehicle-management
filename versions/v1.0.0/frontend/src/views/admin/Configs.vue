<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">系统配置</h2>
      <el-button @click="loadData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        <span>刷新</span>
      </el-button>
    </div>

    <el-card shadow="never" v-loading="loading">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px;">
        系统配置项影响全局行为，修改前请确认含义
      </el-alert>

      <el-form :model="items" label-width="200px">
        <el-form-item v-for="cfg in items" :key="cfg.config_key" :label="cfg.description || cfg.config_key">
          <el-input
            v-if="!isSelectType(cfg.config_key)"
            v-model="cfg.config_value"
            :type="isLongText(cfg.config_key) ? 'textarea' : 'text'"
            :autosize="{ minRows: 2, maxRows: 4 }"
          />
          <el-select v-else v-model="cfg.config_value" style="width: 300px;">
            <el-option
              v-for="opt in getSelectOptions(cfg.config_key)"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
          <el-button type="primary" @click="onSave(cfg)" :loading="saving === cfg.config_key" style="margin-left: 12px;">保存</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import request from '@/api/request'

const items = ref([])
const loading = ref(false)
const saving = ref(null)

// 不同 config_key 的类型映射
const selectOptionsMap = {
  approval_timeout_action: [
    { value: 'auto_approve', label: '自动通过' },
    { value: 'auto_reject', label: '自动驳回' },
  ],
  watermark_position: [
    { value: 'bottom_right', label: '右下角' },
    { value: 'bottom_left', label: '左下角' },
  ],
}

function isSelectType(key) {
  return key in selectOptionsMap
}
function isLongText(key) {
  return key === 'watermark_format' || key.endsWith('_format')
}
function getSelectOptions(key) {
  return selectOptionsMap[key] || []
}

async function loadData() {
  loading.value = true
  try {
    const res = await request.get('/system/configs')
    items.value = res.data || []
  } catch (e) {} finally { loading.value = false }
}

async function onSave(cfg) {
  saving.value = cfg.config_key
  try {
    await request.put(`/system/configs/${cfg.config_key}`, { config_value: cfg.config_value })
    ElMessage.success(`已保存：${cfg.config_key}`)
  } catch (e) {} finally { saving.value = null }
}

onMounted(loadData)
</script>

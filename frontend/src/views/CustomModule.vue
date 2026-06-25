<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">{{ module?.name || '自定义模块' }}</h2>
      <el-button @click="$router.back()">返回</el-button>
    </div>

    <el-card shadow="never">
      <el-empty v-if="!module" description="该模块未配置或您没有访问权限">
        <el-button type="primary" @click="$router.push('/dashboard')">返回首页</el-button>
      </el-empty>

      <div v-else class="custom-module">
        <el-alert type="info" :closable="false" style="margin-bottom: 16px;">
          <template #title>
            <el-icon><InfoFilled /></el-icon>
            <span>这是一个自定义模块占位页</span>
          </template>
          <div class="alert-content">
            <p>管理员在「管理后台 → 角色权限 → 模块管理」里新建了这个模块，当前还没有专属页面。</p>
            <p>如果你想给这个模块实现具体功能，<b>让开发者编辑 <code>{{ module.path }}</code> 这个路由对应的页面组件</b>。</p>
          </div>
        </el-alert>

        <el-descriptions :column="1" border>
          <el-descriptions-item label="模块名称">{{ module.name }}</el-descriptions-item>
          <el-descriptions-item label="模块编码">{{ module.code }}</el-descriptions-item>
          <el-descriptions-item label="访问路径">{{ module.path }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ module.category }}</el-descriptions-item>
          <el-descriptions-item v-if="module.description" label="描述">{{ module.description }}</el-descriptions-item>
          <el-descriptions-item label="是否内置">
            <el-tag :type="module.is_builtin ? 'warning' : 'info'" size="small">
              {{ module.is_builtin ? '是' : '否（自定义）' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { InfoFilled } from '@element-plus/icons-vue'

const route = useRoute()
const authStore = useAuthStore()

const module = computed(() => {
  return (authStore.visibleModules || []).find((m) => m.path === route.path) || null
})
</script>

<style scoped>
.custom-module {
  max-width: 800px;
}
.alert-content {
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.8;
}
.alert-content code {
  background: #f0f9ff;
  color: #1890ff;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
}
</style>

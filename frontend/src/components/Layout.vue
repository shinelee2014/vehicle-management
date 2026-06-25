<template>
  <el-container class="layout-container">
    <!-- 侧边栏（移动端自动隐藏） -->
    <el-aside :width="sidebarWidth" class="sidebar" v-if="!isMobile">
      <div class="logo">
        <el-icon size="20" color="#fff"><Van /></el-icon>
        <span v-if="!collapsed">车辆管理</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        background-color="#001529"
        text-color="rgba(255,255,255,0.85)"
        active-text-color="#fff"
        router
      >
        <!-- 业务 + 基础模块：扁平菜单 -->
        <el-menu-item
          v-for="m in normalModules"
          :key="m.code"
          :index="m.path"
        >
          <el-icon><component :is="iconMap[m.icon] || iconMap.Menu" /></el-icon>
          <template #title>
            {{ m.name }}
            <el-badge
              v-if="getBadge(m.code) > 0"
              :value="getBadge(m.code)"
              class="menu-badge"
            />
          </template>
        </el-menu-item>

        <!-- 管理后台：子菜单分组 -->
        <el-sub-menu v-if="adminModules.length > 0" index="/admin">
          <template #title>
            <el-icon><component :is="iconMap.Setting" /></el-icon>
            <span>管理后台</span>
          </template>
          <el-menu-item
            v-for="m in adminModules"
            :key="m.code"
            :index="m.path"
          >
            <el-icon><component :is="iconMap[m.icon] || iconMap.Menu" /></el-icon>
            <template #title>{{ m.name }}</template>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-button text @click="toggleSidebar" v-if="!isMobile">
            <el-icon size="20"><Expand v-if="collapsed" /><Fold v-else /></el-icon>
          </el-button>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" :style="{ background: '#409eff' }">{{ user?.real_name?.[0] }}</el-avatar>
              <span class="username">{{ user?.real_name }}（{{ roleLabel }}）</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="password">修改密码</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as ElIcons from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { unreadCountApi } from '@/api'
import { pendingApprovalApi } from '@/api/records'
import { ElMessageBox, ElMessage } from 'element-plus'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

// 把所有 Element Plus 图标注册成 map，模板里 <component :is="iconMap[name]" />
const iconMap = ElIcons

const user = computed(() => authStore.user)
const roleLabel = computed(() => {
  const r = user.value?.role
  return r === 'admin' ? '管理员' : r === 'supervisor' ? '主管' : r === 'approver' ? '审批人' : '保安'
})
const activeMenu = computed(() => route.path)

const collapsed = ref(false)
const isMobile = ref(window.innerWidth < 768)
const sidebarWidth = computed(() => {
  if (isMobile.value) return '0'
  return collapsed.value ? '64px' : '220px'
})

// 当前用户可见模块（已按 sort_order 排序）
const visibleModules = computed(() => authStore.visibleModules || [])

// 业务 + 基础：扁平菜单项
const normalModules = computed(() =>
  visibleModules.value.filter((m) => m.category !== '管理')
)

// 管理后台子菜单
const adminModules = computed(() =>
  visibleModules.value.filter((m) => m.category === '管理')
)

// 角标
const unreadCount = ref(0)
const pendingBadge = ref(0)
let pollTimer = null

function getBadge(code) {
  if (code === 'messages') return unreadCount.value
  if (code === 'approval') return pendingBadge.value
  return 0
}

function toggleSidebar() {
  collapsed.value = !collapsed.value
}

async function refreshBadges() {
  if (!authStore.token) return
  try {
    const [u, p] = await Promise.all([
      unreadCountApi(),
      user.value?.is_approver || user.value?.role !== 'security'
        ? pendingApprovalApi({ page: 1, page_size: 1 })
        : Promise.resolve({ data: { total: 0 } }),
    ])
    unreadCount.value = u.data?.unread || 0
    pendingBadge.value = p.data?.total || 0
  } catch (e) {}
}

async function handleCommand(cmd) {
  if (cmd === 'logout') {
    await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
    authStore.logout()
    router.push('/login')
  } else if (cmd === 'profile') {
    router.push('/profile')
  } else if (cmd === 'password') {
    router.push('/profile?tab=password')
  }
}

function onResize() {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  // 每次进 Layout 都主动拉一次 /auth/me，刷新可见模块（避免 localStorage 缓存过期数据）
  authStore.fetchMe().catch(() => {})
  refreshBadges()
  pollTimer = setInterval(refreshBadges, 30000)
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
}
.sidebar {
  background: #001529;
  transition: width 0.3s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.logo {
  height: 60px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  color: #fff;
  font-weight: 600;
  font-size: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.sidebar :deep(.el-menu) {
  flex: 1;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.2) transparent;
}
.sidebar :deep(.el-menu::-webkit-scrollbar) {
  width: 6px;
}
.sidebar :deep(.el-menu::-webkit-scrollbar-thumb) {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}
.sidebar :deep(.el-menu::-webkit-scrollbar-track) {
  background: transparent;
}
.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  z-index: 10;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}
.user-info:hover {
  background: #f5f7fa;
}
.username {
  font-size: 14px;
  color: #303133;
}
.main {
  background: #f5f7fa;
  padding: 0;
  overflow-y: auto;
}
.menu-badge {
  margin-left: 8px;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>

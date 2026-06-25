import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true, title: '登录' },
  },
  {
    path: '/',
    component: () => import('@/components/Layout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '首页', module: 'dashboard' } },
      { path: 'records/in', name: 'RecordIn', component: () => import('@/views/RecordIn.vue'), meta: { title: '进场登记', module: 'records_in' } },
      { path: 'records/out', name: 'RecordOut', component: () => import('@/views/RecordOut.vue'), meta: { title: '出场登记', module: 'records_out' } },
      { path: 'records', name: 'RecordList', component: () => import('@/views/RecordList.vue'), meta: { title: '记录查询', module: 'records_query' } },
      { path: 'records/:id', name: 'RecordDetail', component: () => import('@/views/RecordDetail.vue'), meta: { title: '记录详情' } },
      { path: 'approval', name: 'Approval', component: () => import('@/views/Approval.vue'), meta: { title: '待我审批', module: 'approval' } },
      { path: 'reports', name: 'Reports', component: () => import('@/views/Reports.vue'), meta: { title: '报表中心', module: 'reports' } },
      { path: 'messages', name: 'Messages', component: () => import('@/views/Messages.vue'), meta: { title: '消息中心', module: 'messages' } },
      { path: 'profile', name: 'Profile', component: () => import('@/views/Profile.vue'), meta: { title: '个人中心', module: 'profile' } },
      { path: 'admin/users', name: 'AdminUsers', component: () => import('@/views/admin/Users.vue'), meta: { title: '用户管理', module: 'admin_users', roles: ['admin'] } },
      { path: 'admin/posts', name: 'AdminPosts', component: () => import('@/views/admin/Posts.vue'), meta: { title: '岗亭管理', module: 'admin_posts', roles: ['admin'] } },
      { path: 'admin/configs', name: 'AdminConfigs', component: () => import('@/views/admin/Configs.vue'), meta: { title: '系统配置', module: 'admin_configs', roles: ['admin'] } },
      { path: 'admin/role-modules', name: 'AdminRoleModules', component: () => import('@/views/admin/RoleModules.vue'), meta: { title: '角色权限', module: 'admin_role_modules', roles: ['admin'] } },
      // 自定义模块 catch-all：所有未精确匹配的路径都进这里（在 Layout 下渲染）
      { path: ':pathMatch(.*)*', name: 'CustomModule', component: () => import('@/views/CustomModule.vue'), meta: { title: '自定义模块', module: '__custom__' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  document.title = to.meta.title ? `${to.meta.title} · 车辆管理系统` : '车辆管理系统'

  if (to.meta.public) {
    return next()
  }
  if (!authStore.token) {
    return next('/login')
  }
  // 角色检查（顶层角色守卫，给 admin 路由用）
  if (to.meta.roles && !to.meta.roles.includes(authStore.user?.role)) {
    return next('/dashboard')
  }
  // 模块检查：内置模块按 meta.module 查；自定义模块按 path 匹配
  if (to.meta.module && to.meta.module !== '__custom__' && !authStore.hasModule(to.meta.module)) {
    return next('/dashboard')
  }
  // 自定义模块（catch-all）：看当前路径是不是在用户可见模块的 path 列表里
  if (to.meta.module === '__custom__') {
    const matched = (authStore.visibleModules || []).find((m) => m.path === to.path)
    if (!matched) {
      return next('/dashboard')
    }
  }
  next()
})

export default router

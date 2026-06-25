<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">个人中心</h2>
    </div>

    <el-tabs v-model="activeTab">
      <!-- 个人信息 -->
      <el-tab-pane label="个人信息" name="info">
        <el-card shadow="never">
          <div class="profile-header">
            <el-avatar :size="80" :style="{ background: '#409eff' }">{{ user?.real_name?.[0] }}</el-avatar>
            <div>
              <h2>{{ user?.real_name }}</h2>
              <p class="role-tag">{{ roleLabel }} · {{ user?.post?.name || '无岗亭' }}</p>
            </div>
          </div>

          <el-descriptions :column="2" border style="margin-top: 24px;">
            <el-descriptions-item label="账号">{{ user?.username }}</el-descriptions-item>
            <el-descriptions-item label="姓名">{{ user?.real_name }}</el-descriptions-item>
            <el-descriptions-item label="角色">{{ roleLabel }}</el-descriptions-item>
            <el-descriptions-item label="所属岗亭">{{ user?.post?.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ user?.phone || '-' }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ user?.email || '-' }}</el-descriptions-item>
            <el-descriptions-item label="最后登录">{{ formatTime(user?.last_login_at) }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatTime(user?.created_at) }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>

      <!-- 修改密码 -->
      <el-tab-pane label="修改密码" name="password">
        <el-card shadow="never">
          <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" style="max-width: 480px;">
            <el-form-item label="旧密码" prop="old_password">
              <el-input v-model="form.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="form.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirm">
              <el-input v-model="form.confirm" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="onChange" :loading="loading">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { useAuthStore } from '@/stores/auth'
import { changePasswordApi } from '@/api/auth'

const route = useRoute()
const authStore = useAuthStore()
const user = computed(() => authStore.user)
const roleLabel = computed(() => {
  const r = user.value?.role
  return r === 'admin' ? '管理员' : r === 'supervisor' ? '主管' : '保安'
})

const activeTab = ref(route.query.tab || 'info')
const formRef = ref()
const loading = ref(false)
const form = reactive({ old_password: '', new_password: '', confirm: '' })

const rules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirm: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, cb) => {
        if (value !== form.new_password) cb(new Error('两次密码不一致'))
        else cb()
      },
      trigger: 'blur',
    },
  ],
}

function formatTime(t) { return t ? dayjs(t).format('YYYY-MM-DD HH:mm') : '-' }

async function onChange() {
  await formRef.value.validate()
  loading.value = true
  try {
    await changePasswordApi({ old_password: form.old_password, new_password: form.new_password })
    ElMessage.success('密码修改成功，请重新登录')
    setTimeout(() => {
      authStore.logout()
      window.location.href = '/login'
    }, 1500)
  } catch (e) {} finally {
    loading.value = false
  }
}

onMounted(() => {
  if (!user.value) authStore.fetchMe()
})
</script>

<style scoped>
.profile-header {
  display: flex;
  align-items: center;
  gap: 20px;
}
.profile-header h2 {
  margin: 0;
  font-size: 24px;
}
.role-tag {
  margin: 4px 0 0;
  color: #909399;
  font-size: 14px;
}
</style>

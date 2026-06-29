<template>
  <div class="login-page">
    <div class="login-box">
      <div class="login-header">
        <el-icon size="36" color="#409eff"><Van /></el-icon>
        <h1>车辆进出管理系统</h1>
        <p>厂区智能登记 · 多级审批 · 数据可追溯</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" @keyup.enter="onLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="账号" size="large" :prefix-icon="User" clearable />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" placeholder="密码" size="large" type="password" :prefix-icon="Lock" show-password clearable />
        </el-form-item>
        <el-button type="primary" size="large" :loading="loading" @click="onLogin" style="width: 100%;">
          登 录
        </el-button>
      </el-form>
      <div class="login-footer">
        <p class="version">v1.0.0</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (e) {
    // request 拦截器已弹错误
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px;
}

.login-box {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin: 12px 0 4px;
}

.login-header p {
  font-size: 13px;
  color: #909399;
  margin: 0;
}

.login-footer {
  margin-top: 24px;
  text-align: center;
}

.hint {
  font-size: 12px;
  color: #909399;
  margin: 4px 0;
}

.hint code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: Consolas, monospace;
  color: #409eff;
}

.version {
  margin-top: 12px;
  font-size: 11px;
  color: #c0c4cc;
}
</style>

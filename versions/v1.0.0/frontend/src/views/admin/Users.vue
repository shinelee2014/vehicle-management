<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
      <el-button type="primary" @click="onAdd">
        <el-icon><Plus /></el-icon>
        <span>新建用户</span>
      </el-button>
    </div>

    <el-card shadow="never">
      <el-form :inline="true" :model="filters" style="margin-bottom: 12px;">
        <el-form-item>
          <el-input v-model="filters.keyword" placeholder="搜索账号/姓名" clearable style="width: 200px;" @keyup.enter="loadData" />
        </el-form-item>
        <el-form-item>
          <el-select v-model="filters.role" placeholder="角色" clearable style="width: 150px;" @change="loadData">
            <el-option label="保安" value="security" />
            <el-option label="审批人" value="approver" />
            <el-option label="主管" value="supervisor" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="账号" width="120" />
        <el-table-column prop="real_name" label="姓名" width="100" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" size="small">
              {{ roleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="岗亭" width="120">
          <template #default="{ row }">
            {{ row.post?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="审批人" width="80" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.is_approver" color="#67c23a" size="18"><Check /></el-icon>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="onEdit(row)">编辑</el-button>
            <el-button size="small" @click="onResetPwd(row)">重置密码</el-button>
            <el-button size="small" type="danger" :disabled="row.id === user?.id" @click="onDelete(row)">删除</el-button>
          </template>
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

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑用户' : '新建用户'" width="540px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" :disabled="!!editing" />
        </el-form-item>
        <el-form-item v-if="!editing" label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="form.real_name" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="form.role">
            <el-radio value="security">保安</el-radio>
            <el-radio value="approver">审批人</el-radio>
            <el-radio value="supervisor">主管</el-radio>
            <el-radio value="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="所属岗亭">
          <el-select v-model="form.post_id" clearable placeholder="选择岗亭" style="width: 100%;">
            <el-option v-for="p in posts" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="可作为审批人">
          <el-switch v-model="form.is_approver" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item v-if="editing" label="启用">
          <el-switch v-model="form.is_active" />
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
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Check } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { listPostsApi } from '@/api'
import { listUsersApi, createUserApi, updateUserApi, deleteUserApi, resetPasswordApi } from '@/api/users'

const authStore = useAuthStore()
const user = computed(() => authStore.user)
const items = ref([])
const total = ref(0)
const loading = ref(false)
const submitting = ref(false)
const posts = ref([])

const filters = reactive({ page: 1, page_size: 20, keyword: '', role: '' })
const dialogVisible = ref(false)
const editing = ref(null)
const formRef = ref()
const form = reactive({
  username: '', password: '', real_name: '', role: 'security',
  post_id: null, is_approver: false, phone: '', email: '', is_active: true,
})

const rules = {
  username: [{ required: true, min: 3, max: 50, message: '账号 3-50 位', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

function roleLabel(r) { return { admin: '管理员', supervisor: '主管', approver: '审批人', security: '保安' }[r] || r }
function roleTagType(r) {
  return { admin: 'danger', supervisor: 'success', approver: 'warning', security: 'info' }[r] || ''
}

async function loadData() {
  loading.value = true
  try {
    const res = await listUsersApi(filters)
    items.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (e) {} finally {
    loading.value = false
  }
}

function onAdd() {
  editing.value = null
  Object.assign(form, { username: '', password: '', real_name: '', role: 'security', post_id: null, is_approver: false, phone: '', email: '', is_active: true })
  dialogVisible.value = true
}

function onEdit(row) {
  editing.value = row
  Object.assign(form, {
    username: row.username, real_name: row.real_name, role: row.role,
    post_id: row.post_id, is_approver: row.is_approver,
    phone: row.phone, email: row.email, is_active: row.is_active,
  })
  dialogVisible.value = true
}

async function onSubmit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    if (editing.value) {
      await updateUserApi(editing.value.id, {
        real_name: form.real_name, role: form.role, post_id: form.post_id,
        is_approver: form.is_approver, phone: form.phone, email: form.email, is_active: form.is_active,
      })
      ElMessage.success('更新成功')
    } else {
      await createUserApi({
        username: form.username, password: form.password, real_name: form.real_name,
        role: form.role, post_id: form.post_id, is_approver: form.is_approver,
        phone: form.phone, email: form.email,
      })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {} finally {
    submitting.value = false
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除用户「${row.real_name}」？`, '提示', { type: 'warning' })
    await deleteUserApi(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch (e) {}
}

async function onResetPwd(row) {
  try {
    const { value: pwd } = await ElMessageBox.prompt('请输入新密码（至少 6 位）', '重置密码', { inputPattern: /.{6,}/, inputErrorMessage: '密码至少 6 位' })
    await resetPasswordApi(row.id, { new_password: pwd })
    ElMessage.success('密码已重置')
  } catch (e) {}
}

onMounted(async () => {
  posts.value = (await listPostsApi()).data || []
  loadData()
})
</script>

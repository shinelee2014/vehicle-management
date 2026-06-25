<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">岗亭管理</h2>
      <el-button type="primary" @click="onAdd">
        <el-icon><Plus /></el-icon>
        <span>新建岗亭</span>
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="岗亭名称" />
        <el-table-column prop="location" label="位置" />
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="onEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑岗亭' : '新建岗亭'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="岗亭名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="位置描述">
          <el-input v-model="form.location" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { listPostsApi, createPostApi, updatePostApi, deletePostApi } from '@/api/posts'

const items = ref([])
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const formRef = ref()
const form = reactive({ name: '', location: '', sort_order: 0, is_active: true })
const rules = { name: [{ required: true, message: '请输入岗亭名称', trigger: 'blur' }] }

async function loadData() {
  loading.value = true
  try {
    const res = await listPostsApi()
    items.value = res.data || []
  } catch (e) {} finally { loading.value = false }
}

function onAdd() {
  editing.value = null
  Object.assign(form, { name: '', location: '', sort_order: 0, is_active: true })
  dialogVisible.value = true
}

function onEdit(row) {
  editing.value = row
  Object.assign(form, { name: row.name, location: row.location || '', sort_order: row.sort_order, is_active: row.is_active })
  dialogVisible.value = true
}

async function onSubmit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    if (editing.value) {
      await updatePostApi(editing.value.id, form)
      ElMessage.success('更新成功')
    } else {
      await createPostApi(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {} finally { submitting.value = false }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除岗亭「${row.name}」？`, '提示', { type: 'warning' })
    await deletePostApi(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch (e) {}
}

onMounted(loadData)
</script>

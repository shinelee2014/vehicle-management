<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">车辆类型</h2>
      <el-button type="primary" @click="onAdd">
        <el-icon><Plus /></el-icon>
        <span>新建类型</span>
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="code" label="车型代号" width="150" />
        <el-table-column prop="name" label="类型名称" width="180" />
        <el-table-column prop="description" label="描述备注" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="车型属性" width="120">
          <template #default="{ row }">
            <el-tag v-if="isCoreType(row.code)" type="warning" size="small">核心内置</el-tag>
            <el-tag v-else type="primary" size="small">自定义</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="onEdit(row)">编辑</el-button>
            <el-button 
              size="small" 
              type="danger" 
              :disabled="isCoreType(row.code)"
              @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑车辆类型' : '新建车辆类型'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="车型代号" prop="code">
          <el-input 
            v-model="form.code" 
            :disabled="!!editing" 
            placeholder="如 customer (仅数字字母)"
          />
        </el-form-item>
        <el-form-item label="类型名称" prop="name">
          <el-input v-model="form.name" placeholder="如 客户来访车" />
        </el-form-item>
        <el-form-item label="描述描述">
          <el-input v-model="form.description" type="textarea" placeholder="填写车型的备注和说明" />
        </el-form-item>
        <el-form-item v-if="editing" label="状态">
          <el-switch 
            v-model="form.is_active" 
            :disabled="isCoreType(editing.code)" 
            active-text="启用"
            inactive-text="禁用"
          />
          <div v-if="isCoreType(editing.code)" class="core-tip">
            系统内置核心车型，不允许禁用
          </div>
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
import { 
  listVehicleTypesApi, 
  createVehicleTypeApi, 
  updateVehicleTypeApi, 
  deleteVehicleTypeApi 
} from '@/api/vehicle_types'

const items = ref([])
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const formRef = ref()

const form = reactive({ 
  code: '', 
  name: '', 
  description: '', 
  is_active: true 
})

const rules = { 
  code: [
    { required: true, message: '请输入车型代号', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_\-]+$/, message: '代号仅支持字母、数字、下划线及横杠', trigger: 'blur' }
  ], 
  name: [
    { required: true, message: '请输入类型名称', trigger: 'blur' }
  ] 
}

const CORE_VEHICLE_CODES = ['internal', 'external', 'truck']

function isCoreType(code) {
  return CORE_VEHICLE_CODES.includes(code)
}

async function loadData() {
  loading.value = true
  try {
    const res = await listVehicleTypesApi()
    if (res.code === 0) {
      items.value = res.data || []
    }
  } catch (e) {
    console.error('加载车辆类型失败:', e)
  } finally { 
    loading.value = false 
  }
}

function onAdd() {
  editing.value = null
  Object.assign(form, { code: '', name: '', description: '', is_active: true })
  dialogVisible.value = true
}

function onEdit(row) {
  editing.value = row
  Object.assign(form, { 
    code: row.code, 
    name: row.name, 
    description: row.description || '', 
    is_active: row.is_active 
  })
  dialogVisible.value = true
}

async function onSubmit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    if (editing.value) {
      const res = await updateVehicleTypeApi(editing.value.id, {
        name: form.name,
        description: form.description,
        is_active: form.is_active
      })
      if (res.code === 0) {
        ElMessage.success('更新成功')
        dialogVisible.value = false
        loadData()
      }
    } else {
      const res = await createVehicleTypeApi({
        code: form.code,
        name: form.name,
        description: form.description
      })
      if (res.code === 0) {
        ElMessage.success('创建成功')
        dialogVisible.value = false
        loadData()
      }
    }
  } catch (e) {
    console.error('保存车辆类型失败:', e)
  } finally { 
    submitting.value = false 
  }
}

function onDelete(row) {
  if (isCoreType(row.code)) {
    ElMessage.error('系统内置核心车型，不允许删除')
    return
  }
  ElMessageBox.confirm(
    `确定要删除车型“${row.name}”吗？此操作不可逆！`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      const res = await deleteVehicleTypeApi(row.id)
      if (res.code === 0) {
        ElMessage.success('删除成功')
        loadData()
      }
    } catch (e) {
      console.error('删除车型失败:', e)
    }
  }).catch(() => {})
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.core-tip {
  font-size: 12px;
  color: #e6a23c;
  margin-top: 4px;
  line-height: 1.2;
}
</style>

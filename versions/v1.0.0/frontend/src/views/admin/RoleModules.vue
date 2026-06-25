<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">🔐 角色权限</h2>
      <span class="page-hint">配置每个角色可访问的功能模块，并可自定义新增模块。修改后立即生效。</span>
    </div>

    <el-tabs v-model="mainTab" type="border-card">
      <!-- ============ Tab 1：角色-模块分配 ============ -->
      <el-tab-pane label="权限分配" name="assign">
        <div v-loading="loading">
          <el-tabs v-model="activeRole" type="card" class="role-tabs">
            <el-tab-pane v-for="r in roleOptions" :key="r.value" :name="r.value">
              <template #label>
                <span class="role-tab-label">
                  <el-tag :type="roleTagType(r.value)" size="small" effect="dark">{{ r.label }}</el-tag>
                </span>
              </template>

              <div class="role-pane">
                <div class="role-summary">
                  <el-icon><InfoFilled /></el-icon>
                  <span>当前角色「{{ r.label }}」可访问 <b>{{ (forms[r.value] || []).length }}</b> 个模块（共 {{ modules.length }} 个）</span>
                </div>

                <div v-for="(group, cat) in groupedModules" :key="cat" class="module-group">
                  <div class="module-group-title">
                    <span>{{ cat }}</span>
                    <el-button text type="primary" size="small" @click="toggleGroup(r.value, group)">
                      {{ isAllChecked(r.value, group) ? '清空本组' : '全选本组' }}
                    </el-button>
                  </div>
                  <el-checkbox-group v-model="forms[r.value]">
                    <el-checkbox
                      v-for="m in group"
                      :key="m.code"
                      :value="m.code"
                      class="module-checkbox"
                    >
                      <div class="module-label">
                        <span class="module-name">{{ m.name }}</span>
                        <span class="module-desc">{{ m.description || '无描述' }}</span>
                      </div>
                    </el-checkbox>
                  </el-checkbox-group>
                </div>

                <div class="role-actions">
                  <el-button @click="resetToDefault(r.value)">恢复默认</el-button>
                  <el-button type="primary" :loading="saving === r.value" @click="save(r.value)">
                    保存
                  </el-button>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </el-tab-pane>

      <!-- ============ Tab 2：自定义模块管理 ============ -->
      <el-tab-pane label="模块管理" name="modules">
        <div v-loading="modulesLoading">
          <div class="modules-toolbar">
            <el-input
              v-model="moduleFilter"
              placeholder="搜索名称 / 编码 / 路径"
              clearable
              style="width: 280px;"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button type="primary" @click="openCreateDialog">
              <el-icon><Plus /></el-icon>
              <span>新建自定义模块</span>
            </el-button>
          </div>

          <el-table :data="filteredModules" stripe>
            <el-table-column prop="code" label="编码" width="160">
              <template #default="{ row }">
                <code>{{ row.code }}</code>
              </template>
            </el-table-column>
            <el-table-column prop="name" label="名称" width="140" />
            <el-table-column label="分类" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="categoryTag(row.category)">{{ row.category }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="path" label="路径" width="160">
              <template #default="{ row }">
                <code class="path-code">{{ row.path }}</code>
              </template>
            </el-table-column>
            <el-table-column prop="icon" label="图标" width="100">
              <template #default="{ row }">
                <el-icon v-if="iconMap[row.icon]" size="18"><component :is="iconMap[row.icon]" /></el-icon>
                <span v-else class="muted">{{ row.icon }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" />
            <el-table-column label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                  {{ row.is_active ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="来源" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.is_builtin ? 'warning' : 'info'" size="small" effect="plain">
                  {{ row.is_builtin ? '内置' : '自定义' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
                <el-button
                  size="small"
                  type="danger"
                  :disabled="row.is_builtin"
                  @click="onDeleteModule(row)"
                >删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- ============ 模块编辑/新建对话框 ============ -->
    <el-dialog
      v-model="moduleDialogVisible"
      :title="editingModule ? '编辑模块' : '新建自定义模块'"
      width="560px"
    >
      <el-form ref="moduleFormRef" :model="moduleForm" :rules="moduleRules" label-width="100px">
        <el-form-item label="编码" prop="code">
          <el-input
            v-model="moduleForm.code"
            :disabled="!!editingModule && editingModule.is_builtin"
            placeholder="英文/数字/下划线（如 black_list）"
          />
          <div class="form-hint">
            <span v-if="editingModule && editingModule.is_builtin">内置模块编码不可修改</span>
            <span v-else>用于内部唯一标识，创建后修改会同步到所有角色</span>
          </div>
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="moduleForm.name" placeholder="显示在菜单和角色权限里" />
        </el-form-item>
        <el-form-item label="路径" prop="path">
          <el-input
            v-model="moduleForm.path"
            placeholder="/your-module"
          />
          <div class="form-hint">
            <span>前端路由路径（如 /admin/blacklist）。若没有对应页面，进入会显示占位。</span>
          </div>
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="moduleForm.category" style="width: 100%;">
            <el-option label="业务" value="业务" />
            <el-option label="管理" value="管理" />
            <el-option label="基础" value="基础" />
            <el-option label="自定义" value="自定义" />
          </el-select>
        </el-form-item>
        <el-form-item label="图标">
          <el-select
            v-model="moduleForm.icon"
            filterable
            placeholder="选择图标"
            style="width: 100%;"
          >
            <el-option
              v-for="(comp, name) in iconMap"
              :key="name"
              :label="name"
              :value="name"
            >
              <el-icon style="margin-right: 8px;"><component :is="comp" /></el-icon>
              <span>{{ name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="moduleForm.sort_order" :min="0" :max="9999" />
          <span class="form-hint">数字小，排得靠前</span>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="moduleForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="moduleForm.is_active" />
          <span class="form-hint">停用后菜单不显示，但已分配的权限保留</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="moduleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="moduleSaving" @click="onSaveModule">
          {{ editingModule ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { InfoFilled, Search, Plus } from '@element-plus/icons-vue'
import * as ElIcons from '@element-plus/icons-vue'
import {
  getModuleCatalogApi,
  listRoleModulesApi,
  updateRoleModulesApi,
  listModulesApi,
  createModuleApi,
  updateModuleApi,
  deleteModuleApi,
} from '@/api/auth'

const iconMap = ElIcons

// ====== 角色-模块分配 ======
const ROLE_META = {
  security: { label: '保安', tag: 'info' },
  approver: { label: '审批人', tag: 'warning' },
  supervisor: { label: '主管', tag: 'success' },
  admin: { label: '管理员', tag: 'danger' },
}
const roleOptions = Object.entries(ROLE_META).map(([value, v]) => ({ value, ...v }))
const roleTagType = (r) => ROLE_META[r]?.tag || ''

const mainTab = ref('assign')
const loading = ref(true)
const saving = ref('')
const activeRole = ref('security')
const modules = ref([])
const forms = reactive({})

// 前端默认（仅在数据库没配置时用）
const DEFAULT = {
  security: ['dashboard', 'records_in', 'records_out', 'records_query', 'messages', 'profile'],
  approver: ['dashboard', 'approval', 'records_query', 'messages', 'profile'],
  supervisor: ['dashboard', 'records_in', 'records_out', 'records_query', 'approval', 'reports', 'messages', 'profile', 'admin_posts'],
  admin: [],  // 动态算
}

const groupedModules = computed(() => {
  const groups = {}
  for (const m of modules.value) {
    if (!groups[m.category]) groups[m.category] = []
    groups[m.category].push(m)
  }
  return groups
})

async function loadAssignData() {
  loading.value = true
  try {
    const [cat, list] = await Promise.all([getModuleCatalogApi(), listRoleModulesApi()])
    modules.value = cat.data.modules || []
    DEFAULT.admin = modules.value.map((m) => m.code)

    const stored = {}
    for (const r of list.data.items) stored[r.role] = [...(r.modules || [])]
    for (const r of roleOptions) {
      if (!forms[r.value]) forms[r.value] = stored[r.value] || [...DEFAULT[r.value]]
    }
  } catch (e) {
    // ignore
  } finally {
    loading.value = false
  }
}

function isAllChecked(role, group) {
  const form = forms[role] || []
  return group.every((m) => form.includes(m.code))
}

function toggleGroup(role, group) {
  const form = forms[role] || []
  if (isAllChecked(role, group)) {
    forms[role] = form.filter((c) => !group.some((m) => m.code === c))
  } else {
    const merged = new Set(form)
    group.forEach((m) => merged.add(m.code))
    forms[role] = [...merged]
  }
}

function resetToDefault(role) {
  forms[role] = [...DEFAULT[role]]
}

async function save(role) {
  saving.value = role
  try {
    await updateRoleModulesApi(role, forms[role])
    ElMessage.success(`${ROLE_META[role].label}的权限已保存`)
  } catch (e) {
    // ignore
  } finally {
    saving.value = ''
  }
}

// ====== 自定义模块管理 ======
const modulesLoading = ref(false)
const allModules = ref([])
const moduleFilter = ref('')
const moduleDialogVisible = ref(false)
const editingModule = ref(null)
const moduleFormRef = ref()
const moduleSaving = ref(false)
const moduleForm = reactive({
  code: '', name: '', path: '/', category: '自定义',
  icon: 'Menu', sort_order: 999, description: '', is_active: true,
})

const moduleRules = {
  code: [
    { required: true, message: '请输入编码', trigger: 'blur' },
    { pattern: /^[a-z][a-z0-9_]*$/, message: '编码只能是小写字母/数字/下划线，且以字母开头', trigger: 'blur' },
  ],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  path: [
    { required: true, message: '请输入路径', trigger: 'blur' },
    { pattern: /^\//, message: '路径必须以 / 开头', trigger: 'blur' },
  ],
}

const filteredModules = computed(() => {
  const kw = moduleFilter.value.trim().toLowerCase()
  if (!kw) return allModules.value
  return allModules.value.filter((m) =>
    [m.code, m.name, m.path, m.description].some((v) => (v || '').toLowerCase().includes(kw))
  )
})

const categoryTag = (cat) => ({
  '业务': '',
  '管理': 'warning',
  '基础': 'info',
  '自定义': 'success',
}[cat] || '')

async function loadModules() {
  modulesLoading.value = true
  try {
    const res = await listModulesApi()
    allModules.value = res.data.items || []
  } catch (e) {
    // ignore
  } finally {
    modulesLoading.value = false
  }
}

function openCreateDialog() {
  editingModule.value = null
  Object.assign(moduleForm, {
    code: '', name: '', path: '/', category: '自定义',
    icon: 'Menu', sort_order: 999, description: '', is_active: true,
  })
  moduleDialogVisible.value = true
}

function openEditDialog(row) {
  editingModule.value = row
  Object.assign(moduleForm, {
    code: row.code,
    name: row.name,
    path: row.path,
    category: row.category,
    icon: row.icon || 'Menu',
    sort_order: row.sort_order,
    description: row.description || '',
    is_active: row.is_active,
  })
  moduleDialogVisible.value = true
}

async function onSaveModule() {
  await moduleFormRef.value.validate()
  moduleSaving.value = true
  try {
    if (editingModule.value) {
      await updateModuleApi(editingModule.value.id, { ...moduleForm })
      ElMessage.success('已保存')
    } else {
      await createModuleApi({ ...moduleForm })
      ElMessage.success('已创建')
    }
    moduleDialogVisible.value = false
    await loadModules()
    await loadAssignData()  // 同步刷新权限分配页
  } catch (e) {
    // ignore
  } finally {
    moduleSaving.value = false
  }
}

async function onDeleteModule(row) {
  try {
    await ElMessageBox.confirm(
      `确认删除自定义模块「${row.name}」？\n所有角色的该模块权限会被一并移除。`,
      '删除模块',
      { type: 'warning' }
    )
    await deleteModuleApi(row.id)
    ElMessage.success('已删除')
    await loadModules()
    await loadAssignData()
  } catch (e) {
    // 用户取消也走这里，忽略
  }
}

onMounted(() => {
  loadAssignData()
  loadModules()
})
</script>

<style scoped>
.page-hint {
  font-size: 13px;
  color: #909399;
  margin-left: 12px;
}
.role-tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.role-tabs {
  margin-top: -8px;
}
.role-pane {
  padding: 16px 4px;
}
.role-summary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  background: #f5f7fa;
  border-radius: 6px;
  color: #606266;
  font-size: 14px;
  margin-bottom: 18px;
}
.module-group {
  margin-bottom: 20px;
}
.module-group-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: #303133;
  padding: 6px 0;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 12px;
}
.module-checkbox {
  width: 280px;
  margin-right: 16px !important;
  margin-bottom: 8px !important;
  height: auto !important;
}
.module-label {
  display: flex;
  flex-direction: column;
  line-height: 1.4;
}
.module-name {
  font-weight: 500;
  color: #303133;
}
.module-desc {
  font-size: 12px;
  color: #909399;
}
.role-actions {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
.modules-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  gap: 12px;
}
.muted {
  color: #c0c4cc;
}
.path-code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
  color: #606266;
}
.form-hint {
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
  margin-top: 2px;
}
</style>

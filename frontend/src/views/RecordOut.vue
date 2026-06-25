<template>
  <div class="page-container record-form">
    <div class="page-header">
      <h2 class="page-title">🚙 出场登记</h2>
      <el-button @click="$router.back()">返回</el-button>
    </div>

    <el-card shadow="never">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <!-- 搜索车牌 -->
        <el-form-item label="搜索车牌" prop="plate_keyword">
          <el-input
            v-model="form.plate_keyword"
            placeholder="输入车牌号（至少 2 位）"
            size="large"
            @input="onSearchPlate"
            clearable
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-form-item>

        <!-- 候选记录 -->
        <el-form-item v-if="candidates.length > 0" label="选择待出场的记录">
          <div class="candidate-list">
            <div
              v-for="r in candidates"
              :key="r.id"
              class="candidate-item"
              :class="{ active: form.related_record_id === r.id }"
              @click="onSelectCandidate(r)"
            >
              <div class="candidate-head">
                <span class="plate">{{ r.plate_number }}</span>
                <el-tag :type="typeTagType(r.vehicle_type)" size="small">{{ typeLabel(r.vehicle_type) }}</el-tag>
                <el-tag v-if="r.loading_duration" type="info" size="small">已停留 {{ formatDuration(r.loading_duration) }}</el-tag>
              </div>
              <div class="candidate-info">
                <span>岗亭：岗亭 #{{ r.post_id }}</span>
                <span>进场：{{ formatTime(r.in_time) }}</span>
                <span>事由：{{ r.in_remark || '无' }}</span>
                <span v-if="r.cargo_info">货物：{{ r.cargo_info }}</span>
              </div>
            </div>
          </div>
        </el-form-item>

        <!-- 已选择 -->
        <el-alert v-if="related" type="success" :closable="false" show-icon style="margin: 16px 0;">
          <template #title>
            已选择：<strong>{{ related.plate_number }}</strong>（{{ typeLabel(related.vehicle_type) }}） · 进场 {{ formatTime(related.in_time) }}
          </template>
          <div v-if="related.cargo_info" style="margin-top: 4px;">货物：{{ related.cargo_info }}</div>
        </el-alert>

        <el-form-item label="岗亭" prop="post_id">
          <el-select v-model="form.post_id" placeholder="选择岗亭" style="width: 100%;">
            <el-option v-for="p in posts" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="审批人" prop="approver_id">
          <el-select v-model="form.approver_id" placeholder="选择审批人" style="width: 100%;" filterable>
            <el-option v-for="a in approvers" :key="a.id" :label="`${a.real_name}（${roleLabel(a.role)}）`" :value="a.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="出场备注">
          <el-input v-model="form.out_remark" placeholder="可填写装卸货情况等" />
        </el-form-item>

        <el-divider>📸 拍照取证（必填 2 张）</el-divider>

        <div class="photo-grid">
          <div class="photo-cell">
            <div class="photo-label">车前照片</div>
            <!-- Android App：直接按钮调原生相机 -->
            <div v-if="isAndroid" class="photo-tile" @click="captureAndUpload('front')">
              <img v-if="form.photos.find(p => p.kind === 'front')" :src="form.photos.find(p => p.kind === 'front').url" class="photo-preview" />
              <div v-else class="photo-placeholder">
                <el-icon size="36"><Camera /></el-icon>
                <span>点击拍照</span>
              </div>
            </div>
            <!-- 浏览器：el-upload -->
            <el-upload
              v-else
              v-model:file-list="frontFiles"
              :http-request="uploadFront"
              :show-file-list="false"
              :before-upload="beforePhotoUpload"
              accept="image/*"
              capture="environment"
            >
              <div v-if="!form.photos.find(p => p.kind === 'front')" class="photo-placeholder">
                <el-icon size="36"><Camera /></el-icon>
                <span>点击拍照</span>
              </div>
              <img v-else :src="form.photos.find(p => p.kind === 'front').url" class="photo-preview" />
            </el-upload>
          </div>

          <div class="photo-cell">
            <div class="photo-label">车牌照片</div>
            <!-- Android App：直接按钮调原生相机 -->
            <div v-if="isAndroid" class="photo-tile" @click="captureAndUpload('plate')">
              <img v-if="form.photos.find(p => p.kind === 'plate')" :src="form.photos.find(p => p.kind === 'plate').url" class="photo-preview" />
              <div v-else class="photo-placeholder">
                <el-icon size="36"><Camera /></el-icon>
                <span>点击拍照</span>
              </div>
            </div>
            <!-- 浏览器：el-upload -->
            <el-upload
              v-else
              v-model:file-list="plateFiles"
              :http-request="uploadPlate"
              :show-file-list="false"
              :before-upload="beforePhotoUpload"
              accept="image/*"
              capture="environment"
            >
              <div v-if="!form.photos.find(p => p.kind === 'plate')" class="photo-placeholder">
                <el-icon size="36"><Camera /></el-icon>
                <span>点击拍照</span>
              </div>
              <img v-else :src="form.photos.find(p => p.kind === 'plate').url" class="photo-preview" />
            </el-upload>
          </div>
        </div>

        <el-alert type="info" :closable="false" show-icon style="margin: 16px 0;">
          提交后将自动加水印并通知审批人
        </el-alert>

        <el-button type="warning" size="large" :loading="submitting" @click="onSubmit" style="width: 100%; height: 50px; font-size: 16px;">
          提 交 出 场 申 请
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Camera, Search } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { listPostsApi, listApproversApi, uploadPhotoApi, unbilledListApi } from '@/api'
import { isAndroidApp, takePhotoNative, uploadPhotoNative } from '@/utils/nativeCamera'

const isAndroid = isAndroidApp()
import { createOutApi } from '@/api/records'

const router = useRouter()
const formRef = ref()
const submitting = ref(false)
const posts = ref([])
const approvers = ref([])
const candidates = ref([])
const related = ref(null)
const frontFiles = ref([])
const plateFiles = ref([])
let searchTimer = null

const form = reactive({
  plate_keyword: '',
  related_record_id: null,
  post_id: null,
  approver_id: null,
  out_remark: '',
  photos: [],
})

const rules = {
  post_id: [{ required: true, message: '请选择岗亭', trigger: 'change' }],
  approver_id: [{ required: true, message: '请选择审批人', trigger: 'change' }],
}

function roleLabel(role) {
  return { admin: '管理员', supervisor: '主管', security: '保安' }[role] || role
}
function typeLabel(t) {
  return { internal: '内部车', external: '外部车', truck: '货车' }[t] || t
}
function typeTagType(t) {
  return { internal: 'info', external: '', truck: 'warning' }[t] || ''
}
function formatTime(t) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm:ss') : '-'
}
function formatDuration(min) {
  if (min < 60) return `${min} 分钟`
  return `${Math.floor(min / 60)} 小时 ${min % 60} 分`
}

function onSearchPlate() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    if (form.plate_keyword.length < 1) {
      candidates.value = []
      return
    }
    try {
      const res = await unbilledListApi(form.plate_keyword)
      candidates.value = res.data || []
    } catch (e) {
      candidates.value = []
    }
  }, 300)
}

function onSelectCandidate(r) {
  related.value = r
  form.related_record_id = r.id
  form.plate_keyword = r.plate_number
  candidates.value = []
}

function beforePhotoUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isImage) ElMessage.error('只能上传图片')
  if (!isLt10M) ElMessage.error('图片不能超过 10MB')
  return isImage && isLt10M
}

async function uploadFront(option) { await doUpload(option, 'front') }
async function uploadPlate(option) { await doUpload(option, 'plate') }

async function doUpload(option, kind) {
  // Android App 内用原生相机
  if (isAndroidApp()) {
    try {
      const photo = await takePhotoNative()
      if (!photo.success) {
        ElMessage.warning('拍照已取消')
        return
      }
      const res = await uploadPhotoNative(kind, form.post_id)
      const parsed = typeof res === 'string' ? JSON.parse(res) : res
      if (parsed.code !== 0) {
        ElMessage.error(parsed.message || '上传失败')
        return
      }
      const idx = form.photos.findIndex(p => p.kind === kind)
      if (idx >= 0) form.photos[idx] = { kind, url: parsed.data.url }
      else form.photos.push({ kind, url: parsed.data.url })
      ElMessage.success('已上传')
    } catch (e) {
      ElMessage.error('拍照失败：' + (e.message || e))
    }
    return
  }

  // 浏览器：el-upload
  const fd = new FormData()
  fd.append('file', option.file)
  if (form.post_id) fd.append('post_id', form.post_id)
  try {
    const res = await uploadPhotoApi(fd)
    const idx = form.photos.findIndex(p => p.kind === kind)
    if (idx >= 0) form.photos[idx] = { kind, url: res.data.url }
    else form.photos.push({ kind, url: res.data.url })
    ElMessage.success('已上传')
  } catch (e) {
    option.onError(e)
  }
}

/** Android App 内：直接按钮点击调原生相机 + 上传 */
async function captureAndUpload(kind) {
  try {
    const photo = await takePhotoNative()
    if (!photo.success) {
      ElMessage.warning('拍照已取消')
      return
    }
    const res = await uploadPhotoNative(kind, form.post_id)
    const parsed = typeof res === 'string' ? JSON.parse(res) : res
    if (parsed.code !== 0) {
      ElMessage.error(parsed.message || '上传失败')
      return
    }
    const idx = form.photos.findIndex(p => p.kind === kind)
    if (idx >= 0) form.photos[idx] = { kind, url: parsed.data.url }
    else form.photos.push({ kind, url: parsed.data.url })
    ElMessage.success('已上传')
  } catch (e) {
    ElMessage.error('拍照失败：' + (e.message || e))
  }
}

async function onSubmit() {
  if (!form.related_record_id) {
    ElMessage.warning('请先选择待出场的记录')
    return
  }
  await formRef.value.validate()
  if (form.photos.length < 2) {
    ElMessage.warning('请拍 2 张照片（车前 + 车牌）')
    return
  }
  try {
    await ElMessageBox.confirm('提交后系统会通知审批人，确认提交？', '提示', { type: 'info' })
  } catch (e) { return }

  submitting.value = true
  try {
    const data = {
      related_record_id: form.related_record_id,
      plate_number: related.value.plate_number,
      post_id: form.post_id,
      approver_id: form.approver_id,
      out_remark: form.out_remark,
      photos: form.photos,
    }
    const res = await createOutApi(data)
    ElMessage.success(res.message || '提交成功')
    router.push('/records')
  } catch (e) {
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  const [p, a] = await Promise.all([listPostsApi(), listApproversApi()])
  posts.value = p.data || []
  approvers.value = a.data || []
  if (posts.value.length > 0) form.post_id = posts.value[0].id
})
</script>

<style scoped>
.candidate-list {
  max-height: 320px;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}
.candidate-item {
  padding: 12px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
}
.candidate-item:last-child { border-bottom: none; }
.candidate-item:hover { background: #f5f7fa; }
.candidate-item.active { background: #ecf5ff; }
.candidate-head {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 6px;
}
.candidate-head .plate {
  font-size: 16px;
  font-weight: 600;
}
.candidate-info {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 13px;
  color: #606266;
}
.photo-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.photo-cell { text-align: center; }
.photo-label { font-size: 14px; color: #606266; margin-bottom: 8px; }
.photo-placeholder {
  height: 160px;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #909399;
  cursor: pointer;
  background: #fafafa;
}
.photo-placeholder:hover { border-color: #e6a23c; color: #e6a23c; }
.photo-preview {
  width: 100%;
  height: 160px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}
@media (max-width: 768px) {
  .photo-grid { grid-template-columns: 1fr; }
}
</style>

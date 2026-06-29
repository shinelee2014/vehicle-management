<template>
  <div class="page-container record-form">
    <div class="page-header">
      <h2 class="page-title">🚗 进场登记</h2>
      <el-button @click="$router.back()">返回</el-button>
    </div>

    <el-card shadow="never">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="岗亭" prop="post_id">
          <el-select v-model="form.post_id" placeholder="选择岗亭" style="width: 100%;">
            <el-option v-for="p in posts" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="车牌号" prop="plate_number">
          <el-input v-model="form.plate_number" placeholder="如：粤B12345" size="large" style="text-transform: uppercase; font-size: 18px; font-weight: 600;" maxlength="20" />
        </el-form-item>

        <el-form-item label="车辆类型" prop="vehicle_type">
          <el-radio-group v-model="form.vehicle_type" size="large">
            <el-radio-button v-for="item in vehicleTypes" :key="item.code" :value="item.code">
              {{ item.name }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="form.vehicle_type === 'truck'" label="货物描述" prop="cargo_info">
          <el-input v-model="form.cargo_info" placeholder="如：模具钢 2 吨" />
        </el-form-item>

        <el-form-item label="事由 / 被访人" prop="in_remark">
          <el-input v-model="form.in_remark" placeholder="如：送至生产部 / 拜访张三" />
        </el-form-item>

        <el-form-item label="审批人" prop="approver_id">
          <el-select v-model="form.approver_id" placeholder="选择审批人" style="width: 100%;" filterable>
            <el-option v-for="a in approvers" :key="a.id" :label="`${a.real_name}（${roleLabel(a.role)}）`" :value="a.id" />
          </el-select>
        </el-form-item>

        <el-divider>📸 拍照取证（必填 2 张）</el-divider>

        <div class="photo-grid">
          <div class="photo-cell">
            <div class="photo-label">车前照片</div>
            <!-- Android App 内：直接按钮调原生相机 -->
            <div v-if="isAndroid" class="photo-tile" @click="captureAndUpload('front')">
              <img v-if="getPhotoUrl('front')" :src="getPhotoUrl('front')" class="photo-preview" />
              <div v-else class="photo-placeholder">
                <el-icon size="36"><Camera /></el-icon>
                <span>点击拍照</span>
              </div>
            </div>
            <!-- 浏览器：原 el-upload -->
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
              <img v-else :src="getPhotoUrl('front')" class="photo-preview" />
            </el-upload>
          </div>

          <div class="photo-cell">
            <div class="photo-label">车牌照片</div>
            <!-- Android App 内：直接按钮调原生相机 -->
            <div v-if="isAndroid" class="photo-tile" @click="captureAndUpload('plate')">
              <img v-if="getPhotoUrl('plate')" :src="getPhotoUrl('plate')" class="photo-preview" />
              <div v-else class="photo-placeholder">
                <el-icon size="36"><Camera /></el-icon>
                <span>点击拍照</span>
              </div>
            </div>
            <!-- 浏览器：原 el-upload -->
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
              <img v-else :src="getPhotoUrl('plate')" class="photo-preview" />
            </el-upload>
          </div>
        </div>

        <el-alert type="info" :closable="false" show-icon style="margin: 16px 0;">
          提交后将自动加水印（时间 / 岗亭 / 操作人）并通知审批人
        </el-alert>

        <el-button type="primary" size="large" :loading="submitting" @click="onSubmit" style="width: 100%; height: 50px; font-size: 16px;">
          提 交 进 场 申 请
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Camera } from '@element-plus/icons-vue'
import { listPostsApi, listApproversApi, uploadPhotoApi } from '@/api'
import { createInApi } from '@/api/records'
import { listActiveVehicleTypesApi } from '@/api/vehicle_types'
import { isAndroidApp, takePhotoNative, uploadPhotoNative } from '@/utils/nativeCamera'

const isAndroid = isAndroidApp()

const router = useRouter()
const formRef = ref()
const submitting = ref(false)
const posts = ref([])
const approvers = ref([])
const vehicleTypes = ref([])
const frontFiles = ref([])
const plateFiles = ref([])

const form = reactive({
  post_id: null,
  plate_number: '',
  vehicle_type: 'external',
  cargo_info: '',
  in_remark: '',
  approver_id: null,
  photos: [],  // {kind, url}
})

const rules = {
  post_id: [{ required: true, message: '请选择岗亭', trigger: 'change' }],
  plate_number: [{ required: true, message: '请输入车牌号', trigger: 'blur' }],
  vehicle_type: [{ required: true, message: '请选择车辆类型', trigger: 'change' }],
  approver_id: [{ required: true, message: '请选择审批人', trigger: 'change' }],
  cargo_info: [{ required: true, message: '货车请填写货物描述', trigger: 'blur' }],
}

function roleLabel(role) {
  return { admin: '管理员', supervisor: '主管', security: '保安' }[role] || role
}

function beforePhotoUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isImage) ElMessage.error('只能上传图片')
  if (!isLt10M) ElMessage.error('图片不能超过 10MB')
  return isImage && isLt10M
}

async function uploadFront(option) {
  await doUpload(option, 'front')
}
async function uploadPlate(option) {
  await doUpload(option, 'plate')
}

async function doUpload(option, kind) {
  // 在 Android App 内用原生相机 + JS bridge
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
      ElMessage.success(`${kind === 'front' ? '车前' : '车牌'}照片已上传`)
    } catch (e) {
      ElMessage.error('拍照失败：' + (e.message || e))
    }
    return
  }

  // 浏览器环境用 el-upload
  const fd = new FormData()
  fd.append('file', option.file)
  if (form.post_id) fd.append('post_id', form.post_id)
  try {
    const res = await uploadPhotoApi(fd)
    const idx = form.photos.findIndex(p => p.kind === kind)
    if (idx >= 0) form.photos[idx] = { kind, url: res.data.url }
    else form.photos.push({ kind, url: res.data.url })
    ElMessage.success(`${kind === 'front' ? '车前' : '车牌'}照片已上传`)
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
    // Android 端拿到文件后直接走 OkHttp 上传，不经 JS bridge 传 base64
    const res = await uploadPhotoNative(kind, form.post_id)
    const parsed = typeof res === 'string' ? JSON.parse(res) : res
    if (parsed.code !== 0) {
      ElMessage.error(parsed.message || '上传失败')
      return
    }
    const idx = form.photos.findIndex(p => p.kind === kind)
    if (idx >= 0) form.photos[idx] = { kind, url: parsed.data.url }
    else form.photos.push({ kind, url: parsed.data.url })
    ElMessage.success(`${kind === 'front' ? '车前' : '车牌'}照片已上传`)
  } catch (e) {
    ElMessage.error('拍照失败：' + (e.message || e))
  }
}

function getPhotoUrl(kind) {
  const p = form.photos.find(x => x.kind === kind)
  if (!p) return ''
  return p.url.startsWith('http') ? p.url : p.url
}

async function onSubmit() {
  await formRef.value.validate()
  if (form.photos.length < 2) {
    ElMessage.warning('请拍 2 张照片（车前 + 车牌）')
    return
  }
  try {
    await ElMessageBox.confirm('提交后系统会通知审批人，确认提交？', '提示', { type: 'info' })
  } catch (e) {
    return
  }

  submitting.value = true
  try {
    const data = {
      plate_number: form.plate_number.toUpperCase(),
      vehicle_type: form.vehicle_type,
      post_id: form.post_id,
      approver_id: form.approver_id,
      in_remark: form.in_remark,
      cargo_info: form.vehicle_type === 'truck' ? form.cargo_info : undefined,
      photos: form.photos,
    }
    const res = await createInApi(data)
    ElMessage.success(res.message || '提交成功')
    router.push('/records')
  } catch (e) {
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  const [p, a, vt] = await Promise.all([
    listPostsApi(),
    listApproversApi(),
    listActiveVehicleTypesApi()
  ])
  posts.value = p.data || []
  approvers.value = a.data || []
  vehicleTypes.value = vt.data || []
  
  // 按照货车排在第一个的规则进行重新排序
  const truckIndex = vehicleTypes.value.findIndex(item => item.code === 'truck')
  if (truckIndex > -1) {
    const truckItem = vehicleTypes.value.splice(truckIndex, 1)[0]
    vehicleTypes.value.unshift(truckItem)
  }
  
  // 默认选中第一个岗亭
  if (posts.value.length > 0) form.post_id = posts.value[0].id
  
  // 默认选中“货车”
  if (vehicleTypes.value.length > 0) {
    const truckItem = vehicleTypes.value.find(item => item.code === 'truck')
    form.vehicle_type = truckItem ? 'truck' : vehicleTypes.value[0].code
  }
})
</script>

<style scoped>
.photo-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.photo-cell {
  text-align: center;
}

.photo-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

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

/* Android 端用普通 div 替代 el-upload，触发原生相机 */
.photo-tile {
  cursor: pointer;
}

.photo-placeholder:hover {
  border-color: #409eff;
  color: #409eff;
}

.photo-preview {
  width: 100%;
  height: 160px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

@media (max-width: 768px) {
  .photo-grid {
    grid-template-columns: 1fr;
  }
}
</style>

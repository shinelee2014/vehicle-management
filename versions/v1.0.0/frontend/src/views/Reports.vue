<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">报表中心</h2>
      <el-button type="primary" @click="onExport" :loading="exporting">
        <el-icon><Download /></el-icon>
        <span>导出 Excel</span>
      </el-button>
    </div>

    <!-- 时间选择 -->
    <el-card shadow="never" style="margin-bottom: 16px;">
      <el-radio-group v-model="frequency" @change="loadData" size="large">
        <el-radio-button value="daily">日报</el-radio-button>
        <el-radio-button value="weekly">周报</el-radio-button>
        <el-radio-button value="monthly">月报</el-radio-button>
      </el-radio-group>
      <el-date-picker
        v-if="frequency === 'daily'"
        v-model="date"
        type="date"
        value-format="YYYY-MM-DD"
        placeholder="选择日期"
        style="margin-left: 16px;"
        @change="loadData"
      />
      <el-date-picker
        v-if="frequency === 'monthly'"
        v-model="month"
        type="month"
        value-format="YYYY-MM"
        placeholder="选择月份"
        style="margin-left: 16px;"
        @change="loadData"
      />
    </el-card>

    <div v-loading="loading">
      <!-- 统计卡片 -->
      <div class="stat-cards">
        <div class="stat-card">
          <div class="icon" style="background: #409eff"><el-icon><TopRight /></el-icon></div>
          <div>
            <div class="value">{{ data.totals?.in_count || 0 }}</div>
            <div class="label">总进场</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="icon" style="background: #67c23a"><el-icon><BottomRight /></el-icon></div>
          <div>
            <div class="value">{{ data.totals?.out_count || 0 }}</div>
            <div class="label">总出场</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="icon" style="background: #e6a23c"><el-icon><Van /></el-icon></div>
          <div>
            <div class="value">{{ data.totals?.truck_count || 0 }}</div>
            <div class="label">货车</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="icon" style="background: #909399"><el-icon><Clock /></el-icon></div>
          <div>
            <div class="value">{{ data.totals?.avg_duration || 0 }}</div>
            <div class="label">平均停留(分)</div>
          </div>
        </div>
      </div>

      <!-- 趋势图 -->
      <el-card shadow="never" style="margin-bottom: 16px;">
        <template #header><span style="font-weight: 600">每日进场趋势</span></template>
        <div ref="trendRef" style="height: 320px;"></div>
      </el-card>

      <el-row :gutter="16">
        <el-col :xs="24" :md="12">
          <el-card shadow="never">
            <template #header><span style="font-weight: 600">车辆类型分布</span></template>
            <div ref="typeRef" style="height: 320px;"></div>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="12">
          <el-card shadow="never">
            <template #header><span style="font-weight: 600">各岗亭统计</span></template>
            <div ref="postRef" style="height: 320px;"></div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 按岗亭明细表 -->
      <el-card shadow="never" style="margin-top: 16px;">
        <template #header><span style="font-weight: 600">按岗亭明细</span></template>
        <el-table :data="data.by_post || []" stripe>
          <el-table-column prop="post_name" label="岗亭" />
          <el-table-column prop="count" label="进场次数" align="right" />
        </el-table>
      </el-card>

      <!-- 按审批人明细表 -->
      <el-card shadow="never" style="margin-top: 16px;">
        <template #header><span style="font-weight: 600">按审批人明细</span></template>
        <el-table :data="data.by_approver || []" stripe>
          <el-table-column prop="approver_name" label="审批人" />
          <el-table-column prop="count" label="审批次数" align="right" />
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { dailyReportApi, weeklyReportApi, monthlyReportApi } from '@/api/reports'
import { exportExcelApi } from '@/api/records'

const frequency = ref('daily')
const date = ref(dayjs().format('YYYY-MM-DD'))
const month = ref(dayjs().format('YYYY-MM'))
const loading = ref(false)
const exporting = ref(false)
const data = reactive({})
const trendRef = ref()
const typeRef = ref()
const postRef = ref()
let trendChart = null, typeChart = null, postChart = null

async function loadData() {
  loading.value = true
  try {
    let res
    if (frequency.value === 'daily') {
      res = await dailyReportApi(date.value)
    } else if (frequency.value === 'weekly') {
      res = await weeklyReportApi()
    } else {
      const [y, m] = (month.value || dayjs().format('YYYY-MM')).split('-')
      res = await monthlyReportApi(parseInt(y), parseInt(m))
    }
    Object.assign(data, res.data || {})
    await nextTick()
    renderCharts()
  } catch (e) {
  } finally {
    loading.value = false
  }
}

function renderCharts() {
  renderTrend()
  renderType()
  renderPost()
}

function renderTrend() {
  if (!trendRef.value) return
  if (!trendChart) trendChart = echarts.init(trendRef.value)
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: (data.trend || []).map(t => t.date.slice(5)),
    },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{
      type: 'line',
      smooth: true,
      data: (data.trend || []).map(t => t.count),
      itemStyle: { color: '#409eff' },
      areaStyle: { color: 'rgba(64, 158, 255, 0.1)' },
    }],
  })
}

function renderType() {
  if (!typeRef.value) return
  if (!typeChart) typeChart = echarts.init(typeRef.value)
  const byType = data.by_type || []
  typeChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: byType.map(t => ({ name: t.name, value: t.count })),
      label: { formatter: '{b}: {c} ({d}%)' },
    }],
  })
}

function renderPost() {
  if (!postRef.value) return
  if (!postChart) postChart = echarts.init(postRef.value)
  const byPost = data.by_post || []
  postChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: byPost.map(p => p.post_name) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{
      type: 'bar',
      data: byPost.map(p => p.count),
      itemStyle: { color: '#67c23a', borderRadius: [4, 4, 0, 0] },
    }],
  })
}

async function onExport() {
  exporting.value = true
  try {
    const params = { start_date: data.period?.start, end_date: data.period?.end }
    const res = await exportExcelApi(params)
    const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `车辆记录_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('已导出')
  } catch (e) {} finally {
    exporting.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}
.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.stat-card .icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
}
.stat-card .value { font-size: 24px; font-weight: 600; color: #303133; }
.stat-card .label { font-size: 13px; color: #909399; margin-top: 4px; }
</style>

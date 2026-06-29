<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">首页</h2>
      <span class="greeting">您好，{{ user?.real_name }}！今天是 {{ today }}</span>
    </div>

    <!-- 统计卡片 -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="icon" style="background: #67c23a"><el-icon><TopRight /></el-icon></div>
        <div>
          <div class="value">{{ stats.today_in }}</div>
          <div class="label">今日进场</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="icon" style="background: #e6a23c"><el-icon><BottomRight /></el-icon></div>
        <div>
          <div class="value">{{ stats.today_out }}</div>
          <div class="label">今日出场</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="icon" style="background: #409eff"><el-icon><Van /></el-icon></div>
        <div>
          <div class="value">{{ stats.today_truck }}</div>
          <div class="label">今日货车</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="icon" style="background: #909399"><el-icon><Location /></el-icon></div>
        <div>
          <div class="value">{{ stats.in_vehicle }}</div>
          <div class="label">在场车辆</div>
        </div>
      </div>
      <div class="stat-card" v-if="user?.is_approver || user?.role !== 'security'">
        <div class="icon" style="background: #f56c6c"><el-icon><Bell /></el-icon></div>
        <div>
          <div class="value" style="color: #f56c6c">{{ stats.pending_me }}</div>
          <div class="label">待我审批</div>
        </div>
      </div>
    </div>

    <!-- 快捷入口 -->
    <el-card shadow="never" style="margin-bottom: 20px;">
      <template #header><span style="font-weight: 600">快捷操作</span></template>
      <div class="quick-actions">
        <el-button type="success" size="large" @click="$router.push('/records/in')">
          <el-icon><TopRight /></el-icon>
          <span>进场登记</span>
        </el-button>
        <el-button type="warning" size="large" @click="$router.push('/records/out')">
          <el-icon><BottomRight /></el-icon>
          <span>出场登记</span>
        </el-button>
        <el-button size="large" @click="$router.push('/records')">
          <el-icon><Document /></el-icon>
          <span>记录查询</span>
        </el-button>
        <el-button v-if="stats.pending_me > 0" type="danger" size="large" @click="$router.push('/approval')">
          <el-icon><CircleCheck /></el-icon>
          <span>待我审批 ({{ stats.pending_me }})</span>
        </el-button>
      </div>
    </el-card>

    <!-- 7 日趋势 -->
    <el-card shadow="never">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: 600">近 7 日进场趋势</span>
        </div>
      </template>
      <div ref="chartRef" style="height: 280px;"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import dayjs from 'dayjs'
import * as echarts from 'echarts'
import { useAuthStore } from '@/stores/auth'
import { getDashboardStatsApi } from '@/api'

const authStore = useAuthStore()
const user = computed(() => authStore.user)
const today = dayjs().format('YYYY 年 M 月 D 日 dddd')

const stats = reactive({
  today_in: 0, today_out: 0, today_truck: 0,
  in_vehicle: 0, pending_me: 0, trend: [],
})

const chartRef = ref()
let chart = null

async function loadData() {
  try {
    const res = await getDashboardStatsApi()
    Object.assign(stats, res.data)
    await nextTick()
    renderChart()
  } catch (e) {}
}

function renderChart() {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 30, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: stats.trend.map(t => t.date.slice(5)),
    },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{
      type: 'bar',
      data: stats.trend.map(t => t.count),
      itemStyle: { color: '#409eff', borderRadius: [4, 4, 0, 0] },
      barWidth: '40%',
    }],
  })
}

onMounted(loadData)
</script>

<style scoped>
.greeting {
  color: #909399;
  font-size: 14px;
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.quick-actions .el-button {
  flex: 1;
  min-width: 140px;
  height: 56px;
  font-size: 15px;
}

.quick-actions .el-button span {
  margin-left: 8px;
}
</style>

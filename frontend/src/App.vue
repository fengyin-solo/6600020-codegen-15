<template>
  <div class="h-screen flex flex-col bg-gray-950">
    <header class="bg-gray-900 border-b border-gray-800 px-5 py-3 flex items-center justify-between flex-shrink-0">
      <div class="flex items-center gap-4">
        <h1 class="text-lg font-bold text-orange-400">Modbus 工业监控系统</h1>
        <nav class="flex gap-1">
          <button @click="activeTab = 'dashboard'"
            class="px-4 py-1.5 rounded text-sm transition-all"
            :class="activeTab === 'dashboard' ? 'bg-orange-600 text-white' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'">
            📊 监控面板
          </button>
          <button @click="activeTab = 'policies'"
            class="px-4 py-1.5 rounded text-sm transition-all"
            :class="activeTab === 'policies' ? 'bg-orange-600 text-white' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'">
            ⚙ 阈值策略库
          </button>
        </nav>
      </div>
      <div class="flex items-center gap-3 text-xs">
        <div v-if="activeTab === 'dashboard'" class="flex gap-2">
          <button @click="startPoll" :disabled="store.isPolling"
            class="bg-green-700 py-1.5 px-3 rounded hover:bg-green-600 disabled:opacity-50 transition-colors">
            {{ store.isPolling ? '采集中...' : '▶ 开始采集' }}
          </button>
          <button @click="stopPoll" :disabled="!store.isPolling"
            class="bg-red-700 py-1.5 px-3 rounded hover:bg-red-600 disabled:opacity-50 transition-colors">
            停止
          </button>
        </div>
        <span class="text-gray-500">
          在线: <span class="text-green-400">{{ store.onlineDevices.length }}</span>/{{ store.devices.length }}
        </span>
        <span v-if="store.criticalAlarms.length" class="text-red-400 font-medium">
          ⚠ 严重告警 {{ store.criticalAlarms.length }}
        </span>
      </div>
    </header>

    <div v-if="activeTab === 'dashboard'" class="flex-1 flex overflow-hidden">
      <aside class="w-64 bg-gray-900 p-4 flex flex-col gap-3 border-r border-gray-800 overflow-y-auto flex-shrink-0">
        <div v-if="store.isPolling" class="flex flex-col gap-1">
          <label class="text-gray-400 text-xs">轮询间隔: {{ store.pollInterval }}ms</label>
          <input type="range" v-model.number="store.pollInterval" min="200" max="5000" step="100" class="w-full accent-orange-500" />
        </div>

        <h3 class="text-gray-400 text-xs font-medium mt-2">设备列表</h3>
        <div v-for="d in store.devices" :key="d.id" @click="store.selectedDevice = d"
          class="bg-gray-800 rounded-lg p-2.5 cursor-pointer text-sm transition-all"
          :class="store.selectedDevice?.id === d.id ? 'ring-1 ring-orange-500 bg-gray-800/80' : 'hover:bg-gray-800/80'">
          <div class="flex justify-between items-start">
            <span class="text-gray-200">{{ d.name }}</span>
            <span class="w-2 h-2 rounded-full mt-1.5 flex-shrink-0" :class="d.online ? 'bg-green-500' : 'bg-red-500'"></span>
          </div>
          <div class="text-xs text-gray-500 mt-1">{{ d.ip }}:{{ d.port }} [{{ d.slaveId }}]</div>
          <div class="text-[10px] mt-1.5 flex flex-wrap gap-1">
            <span v-if="store.deviceRulesMap[d.id]?.policyName"
              class="bg-orange-600/20 text-orange-400 px-1.5 py-0.5 rounded">
              ✓ {{ store.deviceRulesMap[d.id].policyName }}
            </span>
            <span v-else class="bg-gray-700 text-gray-500 px-1.5 py-0.5 rounded">无策略</span>
          </div>
        </div>

        <div v-if="store.criticalAlarms.length" class="bg-red-900/40 rounded-lg p-2.5 mt-2 border border-red-900/50">
          <h4 class="text-red-400 text-xs font-bold mb-1.5">⚠ 严重告警 ({{ store.criticalAlarms.length }})</h4>
          <div v-for="a in store.criticalAlarms.slice(0, 3)" :key="a.id" class="text-[11px] text-red-300 mt-1 leading-relaxed">
            {{ a.message }}
          </div>
        </div>
      </aside>

      <main class="flex-1 flex flex-col gap-3 p-4 overflow-y-auto">
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          <template v-for="d in store.devices" :key="d.id">
            <div v-for="r in d.registers" :key="`${d.id}-${r.address}`"
              class="bg-gray-900 rounded-xl p-3.5 border border-gray-800 transition-all hover:border-gray-700">
              <div class="text-[11px] text-gray-500 truncate mb-1">{{ d.name }}</div>
              <div class="text-2xl font-bold tracking-tight" :class="d.online ? 'text-orange-400' : 'text-gray-600'">
                <template v-if="typeof r.value === 'number'">
                  {{ r.value.toFixed(r.value > 100 ? 0 : r.value > 10 ? 1 : 2) }}
                </template>
                <template v-else>{{ r.value ? 'ON' : 'OFF' }}</template>
              </div>
              <div class="text-xs text-gray-500 mt-0.5 flex items-center gap-1">
                <span>{{ r.name }}</span>
                <span v-if="r.unit" class="text-gray-600">{{ r.unit }}</span>
              </div>
              <div v-if="d.online && typeof r.value === 'number' && hasRuleAlert(d, r)"
                class="mt-2 text-[10px] bg-red-900/40 text-red-400 rounded px-2 py-0.5">
                ⚠ 已配置阈值
              </div>
            </div>
          </template>
        </div>

        <div class="bg-gray-900 rounded-xl p-4 flex-1 min-h-[280px] border border-gray-800">
          <h3 class="text-sm text-gray-400 mb-3 flex items-center justify-between">
            <span>📈 实时趋势 — {{ store.selectedDevice?.name || '请选择设备' }}</span>
            <span v-if="store.deviceRulesMap[store.selectedDevice?.id || '']?.policyName"
              class="text-[11px] bg-orange-600/20 text-orange-400 px-2 py-0.5 rounded">
              策略: {{ store.deviceRulesMap[store.selectedDevice?.id || '']?.policyName }}
            </span>
          </h3>
          <TrendChart />
        </div>

        <div class="bg-gray-900 rounded-xl p-4 max-h-52 overflow-y-auto border border-gray-800">
          <h3 class="text-sm text-gray-400 mb-3 sticky top-0 bg-gray-900 pb-2 z-10">
            🔔 告警记录
            <span class="ml-2 text-[11px] text-gray-600">(共 {{ store.alarms.length }} 条)</span>
          </h3>
          <div v-if="!store.alarms.length" class="text-center text-gray-600 py-6 text-sm">
            暂无告警，开始采集后将根据阈值策略自动触发
          </div>
          <div v-for="a in store.alarms.slice(0, 20)" :key="a.id"
            class="flex justify-between items-start text-xs bg-gray-800/50 rounded-lg p-2.5 mb-1.5"
            :class="{ 'border-l-4 border-red-500': a.level === 'critical', 'border-l-4 border-yellow-500': a.level === 'warning', 'border-l-4 border-blue-500': a.level === 'info', 'opacity-50': a.acknowledged }">
            <div class="flex-1 min-w-0">
              <span class="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium mr-2 mb-1"
                :class="{
                  'bg-red-900/50 text-red-400': a.level === 'critical',
                  'bg-yellow-900/50 text-yellow-400': a.level === 'warning',
                  'bg-blue-900/50 text-blue-400': a.level === 'info'
                }">
                {{ { info: '提示', warning: '告警', critical: '严重' }[a.level] }}
              </span>
              <span class="text-gray-300">{{ a.message }}</span>
            </div>
            <div class="flex items-center gap-2 ml-3 flex-shrink-0">
              <span class="text-gray-500 text-[11px]">{{ new Date(a.timestamp).toLocaleTimeString() }}</span>
              <button v-if="!a.acknowledged" @click="store.acknowledgeAlarm(a.id)"
                class="text-blue-400 hover:underline text-[11px] hover:text-blue-300">确认</button>
            </div>
          </div>
        </div>
      </main>
    </div>

    <div v-else class="flex-1 p-4 overflow-hidden bg-gray-950">
      <ThresholdPolicyManager />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useModbusStore } from './store/modbus'
import TrendChart from './components/TrendChart.vue'
import ThresholdPolicyManager from './components/ThresholdPolicyManager.vue'
import type { Device, ModbusRegister } from './types'

const store = useModbusStore()
const activeTab = ref<'dashboard' | 'policies'>('dashboard')
let timer: number | null = null

function startPoll() {
  store.isPolling = true
  timer = window.setInterval(() => store.simulatePoll(), store.pollInterval)
}

function stopPoll() {
  store.isPolling = false
  if (timer) { clearInterval(timer); timer = null }
}

function hasRuleAlert(d: Device, r: ModbusRegister): boolean {
  const applied = store.deviceRulesMap[d.id]
  if (!applied) return false
  return applied.rules.some(rule =>
    rule.enabled && (rule.registerAddress === r.address || rule.registerName === r.name)
  )
}

onMounted(async () => {
  store.initMockDevices()
  try {
    await Promise.all([
      store.loadDeviceTypes(),
      store.loadPolicies(),
      store.loadApplications(),
      store.loadAllDeviceRules()
    ])
  } catch (e) {
    console.warn('阈值策略API初始化跳过（后端未启动时可正常运行前端模拟逻辑）')
  }
})
onUnmounted(() => stopPoll())
</script>

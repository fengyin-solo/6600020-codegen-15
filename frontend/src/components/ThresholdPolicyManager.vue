<template>
  <div class="h-full flex flex-col gap-4 text-sm text-gray-200">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-bold text-orange-400">阈值策略库</h2>
      <div class="flex gap-2">
        <select v-model="filterDeviceTypeId" class="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-xs">
          <option value="">全部设备类型</option>
          <option v-for="dt in store.deviceTypes" :key="dt.id" :value="dt.id">{{ dt.name }}</option>
        </select>
        <button @click="openCreatePolicy" class="bg-orange-600 hover:bg-orange-500 px-4 py-1.5 rounded text-xs font-medium">
          + 新建策略
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 overflow-hidden">
      <div class="flex flex-col gap-3 overflow-hidden">
        <h3 class="text-gray-400 text-xs font-medium">策略列表</h3>
        <div class="flex-1 overflow-y-auto space-y-3 pr-1">
          <div v-for="p in filteredPolicies" :key="p.id"
            @click="selectedPolicy = p"
            class="bg-gray-900 rounded-lg p-4 cursor-pointer transition-all border"
            :class="selectedPolicy?.id === p.id ? 'border-orange-500 ring-1 ring-orange-500/50' : 'border-gray-800 hover:border-gray-700'">
            <div class="flex items-start justify-between mb-2">
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-semibold text-gray-100">{{ p.name }}</span>
                  <span v-if="p.isDefault" class="bg-blue-600/30 text-blue-400 px-2 py-0.5 rounded text-[10px]">默认</span>
                </div>
                <div class="text-xs text-gray-500 mt-1">{{ p.description || '暂无描述' }}</div>
              </div>
              <span class="bg-gray-800 text-gray-400 px-2 py-0.5 rounded text-[10px]">
                {{ store.deviceTypeMap[p.deviceTypeId]?.name || '未知类型' }}
              </span>
            </div>
            <div class="flex items-center gap-4 text-xs">
              <span class="text-gray-500">
                规则: <span class="text-orange-400 font-medium">{{ p.rules.length }}</span> 条
              </span>
              <span class="text-gray-500">
                已应用: <span class="text-green-400 font-medium">{{ policyAppliedCount(p.id) }}</span> 台
              </span>
            </div>
          </div>
          <div v-if="!filteredPolicies.length" class="text-center text-gray-600 py-12">
            暂无策略，点击"新建策略"创建
          </div>
        </div>
      </div>

      <div class="flex flex-col gap-3 overflow-hidden">
        <div v-if="selectedPolicy" class="flex flex-col overflow-hidden">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-gray-400 text-xs font-medium">策略详情</h3>
            <div class="flex gap-2">
              <button @click="openApplyDialog(selectedPolicy)" class="bg-green-700 hover:bg-green-600 px-3 py-1 rounded text-xs">
                批量应用
              </button>
              <button @click="openEditPolicy(selectedPolicy)" class="bg-blue-700 hover:bg-blue-600 px-3 py-1 rounded text-xs">
                编辑
              </button>
              <button @click="handleDeletePolicy(selectedPolicy.id)" class="bg-red-700 hover:bg-red-600 px-3 py-1 rounded text-xs">
                删除
              </button>
            </div>
          </div>

          <div class="bg-gray-900 rounded-lg p-4 mb-3 flex-shrink-0">
            <div class="text-base font-semibold text-gray-100 mb-1">{{ selectedPolicy.name }}</div>
            <div class="text-xs text-gray-500 mb-2">{{ selectedPolicy.description || '暂无描述' }}</div>
            <div class="flex flex-wrap gap-2 text-xs">
              <span class="bg-gray-800 px-2 py-1 rounded text-gray-400">
                设备类型: {{ store.deviceTypeMap[selectedPolicy.deviceTypeId]?.name }}
              </span>
              <span v-if="selectedPolicy.isDefault" class="bg-blue-600/20 px-2 py-1 rounded text-blue-400">默认策略</span>
              <span class="bg-gray-800 px-2 py-1 rounded text-gray-400">
                创建: {{ formatDate(selectedPolicy.createdAt) }}
              </span>
            </div>
          </div>

          <div class="flex-1 overflow-y-auto pr-1">
            <h4 class="text-gray-400 text-xs font-medium mb-2">阈值规则 ({{ selectedPolicy.rules.length }})</h4>
            <div v-if="!selectedPolicy.rules.length" class="text-gray-600 text-center py-8 bg-gray-900/50 rounded-lg">
              暂无规则
            </div>
            <div v-for="rule in selectedPolicy.rules" :key="rule.id"
              class="bg-gray-900 rounded-lg p-3 mb-2 border border-gray-800">
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <span class="px-2 py-0.5 rounded text-[10px] font-medium"
                    :class="{
                      'bg-red-600/30 text-red-400': rule.level === 'critical',
                      'bg-yellow-600/30 text-yellow-400': rule.level === 'warning',
                      'bg-blue-600/30 text-blue-400': rule.level === 'info'
                    }">
                    {{ levelText(rule.level) }}
                  </span>
                  <span class="font-medium text-gray-200">{{ rule.registerName }}</span>
                  <span class="text-gray-600 text-[10px]">#{{ rule.registerAddress }}</span>
                </div>
                <span v-if="!rule.enabled" class="text-gray-600 text-[10px]">已禁用</span>
              </div>
              <div class="text-xs text-gray-400 mb-2">
                <span class="text-orange-400 font-mono">{{ rule.registerName }}</span>
                <span class="mx-2 text-gray-500">{{ rule.operator }}</span>
                <span class="text-green-400 font-mono">{{ rule.threshold }}</span>
              </div>
              <div class="text-[11px] text-gray-500 bg-gray-800/50 rounded px-2 py-1.5 font-mono">
                {{ rule.messageTemplate }}
              </div>
            </div>
          </div>
        </div>

        <div v-else class="flex items-center justify-center h-full text-gray-600">
          <div class="text-center">
            <div class="text-4xl mb-3">📋</div>
            <div>选择左侧策略查看详情</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showPolicyDialog" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div class="bg-gray-900 rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col border border-gray-800">
        <div class="flex items-center justify-between p-4 border-b border-gray-800">
          <h3 class="text-lg font-semibold text-orange-400">
            {{ editingPolicy ? '编辑策略' : '新建策略' }}
          </h3>
          <button @click="showPolicyDialog = false" class="text-gray-500 hover:text-gray-300 text-xl">&times;</button>
        </div>
        <div class="p-4 overflow-y-auto flex-1 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs text-gray-400 mb-1">策略名称 *</label>
              <input v-model="policyForm.name" class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm" />
            </div>
            <div>
              <label class="block text-xs text-gray-400 mb-1">设备类型 *</label>
              <select v-model="policyForm.deviceTypeId" @change="handleDeviceTypeChange"
                class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm">
                <option value="">请选择</option>
                <option v-for="dt in store.deviceTypes" :key="dt.id" :value="dt.id">{{ dt.name }}</option>
              </select>
            </div>
            <div class="col-span-2">
              <label class="block text-xs text-gray-400 mb-1">描述</label>
              <textarea v-model="policyForm.description" rows="2"
                class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm resize-none"></textarea>
            </div>
            <div class="flex items-center gap-2">
              <input type="checkbox" v-model="policyForm.isDefault" id="isDefault" class="rounded" />
              <label for="isDefault" class="text-xs text-gray-300">设为该设备类型的默认策略</label>
            </div>
          </div>

          <div class="border-t border-gray-800 pt-4">
            <div class="flex items-center justify-between mb-3">
              <h4 class="text-sm font-medium text-gray-300">阈值规则</h4>
              <button @click="addRule" :disabled="!policyForm.deviceTypeId"
                class="bg-orange-600/80 hover:bg-orange-500 disabled:opacity-40 disabled:cursor-not-allowed px-3 py-1 rounded text-xs">
                + 添加规则
              </button>
            </div>
            <div v-if="!policyForm.rules.length" class="text-gray-600 text-center py-6 bg-gray-800/30 rounded-lg text-xs">
              {{ policyForm.deviceTypeId ? '点击上方"添加规则"按钮' : '请先选择设备类型' }}
            </div>
            <div v-for="(rule, idx) in policyForm.rules" :key="idx"
              class="bg-gray-800/50 rounded-lg p-3 mb-2 border border-gray-700/50">
              <div class="grid grid-cols-12 gap-2 mb-2">
                <div class="col-span-3">
                  <label class="block text-[10px] text-gray-500 mb-1">寄存器</label>
                  <select v-model="rule.registerName" @change="handleRegisterChange(idx)"
                    class="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-xs">
                    <option value="">选择</option>
                    <option v-for="r in currentTypeRegisters" :key="r.name" :value="r.name">{{ r.name }} (#{{ r.address }})</option>
                  </select>
                </div>
                <div class="col-span-2">
                  <label class="block text-[10px] text-gray-500 mb-1">条件</label>
                  <select v-model="rule.operator" class="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-xs font-mono">
                    <option value=">">大于 &gt;</option>
                    <option value=">=">大于等于 &gt;=</option>
                    <option value="<">小于 &lt;</option>
                    <option value="<=">小于等于 &lt;=</option>
                    <option value="==">等于 ==</option>
                    <option value="!=">不等于 !=</option>
                  </select>
                </div>
                <div class="col-span-2">
                  <label class="block text-[10px] text-gray-500 mb-1">阈值</label>
                  <input type="number" step="any" v-model.number="rule.threshold"
                    class="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-xs font-mono" />
                </div>
                <div class="col-span-2">
                  <label class="block text-[10px] text-gray-500 mb-1">级别</label>
                  <select v-model="rule.level" class="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-xs">
                    <option value="info">提示</option>
                    <option value="warning">告警</option>
                    <option value="critical">严重</option>
                  </select>
                </div>
                <div class="col-span-2 flex items-end justify-end gap-1">
                  <label class="flex items-center gap-1 text-[10px] text-gray-400">
                    <input type="checkbox" v-model="rule.enabled" class="rounded" /> 启用
                  </label>
                  <button @click="removeRule(idx)" class="text-red-400 hover:text-red-300 p-1" title="删除">
                    ✕
                  </button>
                </div>
              </div>
              <div>
                <label class="block text-[10px] text-gray-500 mb-1">告警消息模板</label>
                <input type="text" v-model="rule.messageTemplate"
                  class="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-xs font-mono"
                  placeholder="{device_name} 温度过高: {value}{unit}，阈值 {threshold}{unit}" />
                <div class="text-[10px] text-gray-600 mt-1">
                  可用变量: {device_name}, {value}, {unit}, {threshold}
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-2 p-4 border-t border-gray-800">
          <button @click="showPolicyDialog = false" class="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded text-sm">
            取消
          </button>
          <button @click="savePolicy" :disabled="!canSavePolicy"
            class="bg-orange-600 hover:bg-orange-500 disabled:opacity-50 px-4 py-2 rounded text-sm">
            {{ editingPolicy ? '保存修改' : '创建策略' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showApplyDialog" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div class="bg-gray-900 rounded-xl w-full max-w-2xl max-h-[85vh] flex flex-col border border-gray-800">
        <div class="flex items-center justify-between p-4 border-b border-gray-800">
          <h3 class="text-lg font-semibold text-orange-400">批量应用策略</h3>
          <button @click="showApplyDialog = false" class="text-gray-500 hover:text-gray-300 text-xl">&times;</button>
        </div>
        <div class="p-4 overflow-y-auto flex-1">
          <div v-if="applyingPolicy" class="bg-gray-800/50 rounded-lg p-3 mb-4">
            <div class="font-medium text-gray-200">{{ applyingPolicy.name }}</div>
            <div class="text-xs text-gray-500 mt-1">{{ applyingPolicy.description || '暂无描述' }}</div>
            <div class="text-xs text-gray-400 mt-2">
              规则数: {{ applyingPolicy.rules?.length || 0 }} |
              设备类型: {{ store.deviceTypeMap[applyingPolicy.deviceTypeId]?.name }}
            </div>
          </div>
          <h4 class="text-sm font-medium text-gray-300 mb-3">选择要应用的设备</h4>
          <div class="flex items-center justify-between mb-2 text-xs">
            <span class="text-gray-500">
              已选 {{ selectedDeviceIds.length }} / {{ compatibleDevices.length }} 台设备
            </span>
            <div class="flex gap-2">
              <button @click="selectAllCompatible" class="text-orange-400 hover:underline">全选兼容</button>
              <button @click="selectedDeviceIds = []" class="text-gray-500 hover:underline">清空</button>
            </div>
          </div>
          <div class="space-y-2">
            <div v-for="d in compatibleDevices" :key="d.id"
              @click="toggleDeviceSelect(d.id)"
              class="bg-gray-800 rounded-lg p-3 cursor-pointer border transition-all"
              :class="selectedDeviceIds.includes(d.id) ? 'border-orange-500 bg-gray-800/80' : 'border-gray-700 hover:border-gray-600'">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <div class="w-4 h-4 rounded border-2 flex items-center justify-center"
                    :class="selectedDeviceIds.includes(d.id) ? 'bg-orange-500 border-orange-500' : 'border-gray-600'">
                    <span v-if="selectedDeviceIds.includes(d.id)" class="text-[10px] text-white">✓</span>
                  </div>
                  <div>
                    <div class="flex items-center gap-2">
                      <span class="font-medium text-gray-200">{{ d.name }}</span>
                      <span class="w-2 h-2 rounded-full" :class="d.online ? 'bg-green-500' : 'bg-red-500'"></span>
                    </div>
                    <div class="text-xs text-gray-500 mt-0.5">{{ d.ip }}:{{ d.port }} · {{ d.registers.length }} 个寄存器</div>
                  </div>
                </div>
                <div class="text-right">
                  <div v-if="store.deviceRulesMap[d.id]?.policyName" class="text-xs text-orange-400">
                    → 将替换: {{ store.deviceRulesMap[d.id].policyName }}
                  </div>
                  <div v-else class="text-xs text-gray-600">未应用任何策略</div>
                </div>
              </div>
            </div>
            <div v-if="incompatibleDevices.length" class="mt-4 pt-4 border-t border-gray-800">
              <h5 class="text-xs text-gray-500 mb-2">不兼容的设备 (寄存器不匹配)</h5>
              <div v-for="d in incompatibleDevices" :key="d.id"
                class="bg-gray-800/30 rounded-lg p-2 opacity-60 mb-1 flex items-center justify-between text-xs">
                <div class="flex items-center gap-2">
                  <span class="w-4 h-4 rounded border-2 border-gray-700"></span>
                  <span class="text-gray-500">{{ d.name }}</span>
                </div>
                <span class="text-gray-600">设备类型不匹配</span>
              </div>
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-2 p-4 border-t border-gray-800">
          <button @click="showApplyDialog = false" class="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded text-sm">
            取消
          </button>
          <button @click="confirmApply" :disabled="!selectedDeviceIds.length"
            class="bg-green-600 hover:bg-green-500 disabled:opacity-50 px-4 py-2 rounded text-sm">
            应用到 {{ selectedDeviceIds.length }} 台设备
          </button>
        </div>
      </div>
    </div>

    <div v-if="showApplyResult" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div class="bg-gray-900 rounded-xl w-full max-w-md border border-gray-800">
        <div class="p-4 border-b border-gray-800">
          <h3 class="text-lg font-semibold" :class="applyResult?.failed === 0 ? 'text-green-400' : 'text-orange-400'">
            应用结果
          </h3>
        </div>
        <div class="p-4 space-y-3">
          <div class="flex gap-4">
            <div class="flex-1 bg-green-900/30 rounded-lg p-3 text-center">
              <div class="text-2xl font-bold text-green-400">{{ applyResult?.success || 0 }}</div>
              <div class="text-xs text-green-500 mt-1">成功</div>
            </div>
            <div class="flex-1 bg-red-900/30 rounded-lg p-3 text-center">
              <div class="text-2xl font-bold text-red-400">{{ applyResult?.failed || 0 }}</div>
              <div class="text-xs text-red-500 mt-1">失败</div>
            </div>
          </div>
          <div v-if="applyResult?.failed" class="max-h-40 overflow-y-auto space-y-1">
            <div v-for="(r, i) in applyResult.results.filter(x => !x.success)" :key="i"
              class="text-xs bg-red-900/20 rounded p-2 text-red-400">
              {{ r.deviceId }}: {{ r.reason }}
            </div>
          </div>
        </div>
        <div class="flex justify-end p-4 border-t border-gray-800">
          <button @click="showApplyResult = false" class="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded text-sm">
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useModbusStore } from '../store/modbus'
import type {
  ThresholdPolicy, ThresholdPolicyCreate, ThresholdPolicyUpdate,
  ThresholdRuleCreate, Device, BatchApplyResponse
} from '../types'

const store = useModbusStore()

const filterDeviceTypeId = ref('')
const selectedPolicy = ref<ThresholdPolicy | null>(null)

const showPolicyDialog = ref(false)
const editingPolicy = ref<ThresholdPolicy | null>(null)
const policyForm = ref<ThresholdPolicyCreate>({
  name: '',
  description: '',
  deviceTypeId: '',
  isDefault: false,
  rules: []
})

const showApplyDialog = ref(false)
const applyingPolicy = ref<ThresholdPolicy | null>(null)
const selectedDeviceIds = ref<string[]>([])

const showApplyResult = ref(false)
const applyResult = ref<BatchApplyResponse | null>(null)

const filteredPolicies = computed(() => {
  if (!filterDeviceTypeId.value) return store.policies
  return store.policies.filter(p => p.deviceTypeId === filterDeviceTypeId.value)
})

const currentTypeRegisters = computed(() => {
  const dt = store.deviceTypeMap[policyForm.value.deviceTypeId]
  return dt?.registerTemplates || []
})

const compatibleDevices = computed(() => {
  if (!applyingPolicy.value) return store.devices
  const targetDtId = applyingPolicy.value.deviceTypeId
  return store.devices.filter(d => {
    const applied = store.deviceRulesMap[d.id]
    if (applied?.policyId) {
      const policy = store.policies.find(p => p.id === applied.policyId)
      if (policy?.deviceTypeId === targetDtId) return true
    }
    return store.guessDeviceTypeId(d) === targetDtId
  })
})

const incompatibleDevices = computed(() => {
  return store.devices.filter(d => !compatibleDevices.value.includes(d))
})

const canSavePolicy = computed(() => {
  return policyForm.value.name.trim() && policyForm.value.deviceTypeId
})

function policyAppliedCount(policyId: string): number {
  return store.applications.filter(a => a.policyId === policyId).length
}

function levelText(level: string): string {
  return { info: '提示', warning: '告警', critical: '严重' }[level] || level
}

function formatDate(s: string): string {
  try { return new Date(s).toLocaleString('zh-CN', { hour12: false }) } catch { return s }
}

function openCreatePolicy() {
  editingPolicy.value = null
  policyForm.value = {
    name: '',
    description: '',
    deviceTypeId: filterDeviceTypeId.value || '',
    isDefault: false,
    rules: []
  }
  showPolicyDialog.value = true
}

function openEditPolicy(p: ThresholdPolicy) {
  editingPolicy.value = p
  policyForm.value = {
    name: p.name,
    description: p.description || '',
    deviceTypeId: p.deviceTypeId,
    isDefault: p.isDefault,
    rules: p.rules.map(r => ({
      registerName: r.registerName,
      registerAddress: r.registerAddress,
      operator: r.operator,
      threshold: r.threshold,
      level: r.level,
      messageTemplate: r.messageTemplate,
      enabled: r.enabled
    }))
  }
  showPolicyDialog.value = true
}

function handleDeviceTypeChange() {
  policyForm.value.rules = []
}

function handleRegisterChange(idx: number) {
  const name = policyForm.value.rules[idx].registerName
  const reg = currentTypeRegisters.value.find(r => r.name === name)
  if (reg) {
    policyForm.value.rules[idx].registerAddress = reg.address
  }
}

function addRule() {
  const reg0 = currentTypeRegisters.value[0]
  if (!reg0) return
  policyForm.value.rules.push({
    registerName: reg0.name,
    registerAddress: reg0.address,
    operator: '>',
    threshold: 0,
    level: 'warning',
    messageTemplate: `{device_name} ${reg0.name}异常: {value}{unit}，阈值 {threshold}{unit}`,
    enabled: true
  })
}

function removeRule(idx: number) {
  policyForm.value.rules.splice(idx, 1)
}

async function savePolicy() {
  try {
    if (editingPolicy.value) {
      const update: ThresholdPolicyUpdate = { ...policyForm.value }
      await store.updatePolicy(editingPolicy.value.id, update)
    } else {
      await store.createPolicy(policyForm.value)
    }
    showPolicyDialog.value = false
  } catch (e: any) {
    alert('保存失败: ' + (e.message || e))
  }
}

async function handleDeletePolicy(id: string) {
  if (!confirm('确定删除该策略？已应用的设备将被解绑。')) return
  try {
    await store.deletePolicy(id)
    if (selectedPolicy.value?.id === id) selectedPolicy.value = null
  } catch (e: any) {
    alert('删除失败: ' + (e.message || e))
  }
}

function openApplyDialog(p: ThresholdPolicy) {
  applyingPolicy.value = p
  selectedDeviceIds.value = compatibleDevices.value.map(d => d.id)
  showApplyDialog.value = true
}

function toggleDeviceSelect(id: string) {
  const idx = selectedDeviceIds.value.indexOf(id)
  if (idx >= 0) selectedDeviceIds.value.splice(idx, 1)
  else selectedDeviceIds.value.push(id)
}

function selectAllCompatible() {
  selectedDeviceIds.value = compatibleDevices.value.map(d => d.id)
}

async function confirmApply() {
  if (!applyingPolicy.value || !selectedDeviceIds.value.length) return
  try {
    applyResult.value = await store.batchApplyPolicy(applyingPolicy.value.id, selectedDeviceIds.value)
    showApplyDialog.value = false
    showApplyResult.value = true
  } catch (e: any) {
    alert('应用失败: ' + (e.message || e))
  }
}

onMounted(async () => {
  try {
    await Promise.all([
      store.loadDeviceTypes(),
      store.loadPolicies(),
      store.loadApplications(),
      store.loadAllDeviceRules()
    ])
  } catch (e) {
    console.warn('后端阈值策略API不可用，使用前端默认逻辑', e)
  }
})
</script>

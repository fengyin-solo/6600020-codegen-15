import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type {
  Device, Alarm, ModbusRegister,
  DeviceType, ThresholdPolicy, ThresholdPolicyCreate, ThresholdPolicyUpdate,
  PolicyApplication, DeviceAppliedRules, BatchApplyResponse,
  ThresholdRuleCreate, ConditionOperator, AlarmLevel
} from '../types'

const API_BASE = '/api/threshold'

function snakeToCamel(obj: any): any {
  if (Array.isArray(obj)) return obj.map(snakeToCamel)
  if (obj !== null && typeof obj === 'object') {
    const result: any = {}
    for (const key in obj) {
      const camelKey = key.replace(/_([a-z])/g, (_, c) => c.toUpperCase())
      result[camelKey] = snakeToCamel(obj[key])
    }
    return result
  }
  return obj
}

function camelToSnake(obj: any): any {
  if (Array.isArray(obj)) return obj.map(camelToSnake)
  if (obj !== null && typeof obj === 'object') {
    const result: any = {}
    for (const key in obj) {
      const snakeKey = key.replace(/([A-Z])/g, (_, c) => '_' + c.toLowerCase())
      result[snakeKey] = camelToSnake(obj[key])
    }
    return result
  }
  return obj
}

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(API_BASE + path)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return snakeToCamel(await res.json()) as T
}

async function apiPost<T>(path: string, body: any): Promise<T> {
  const res = await fetch(API_BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(camelToSnake(body))
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return snakeToCamel(await res.json()) as T
}

async function apiPut<T>(path: string, body: any): Promise<T> {
  const res = await fetch(API_BASE + path, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(camelToSnake(body))
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return snakeToCamel(await res.json()) as T
}

async function apiDelete<T>(path: string): Promise<T> {
  const res = await fetch(API_BASE + path, { method: 'DELETE' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return snakeToCamel(await res.json()) as T
}

function evaluateCondition(value: number, operator: ConditionOperator, threshold: number): boolean {
  switch (operator) {
    case '>': return value > threshold
    case '>=': return value >= threshold
    case '<': return value < threshold
    case '<=': return value <= threshold
    case '==': return value === threshold
    case '!=': return value !== threshold
  }
}

function formatMessage(template: string, deviceName: string, value: number, unit: string, threshold: number): string {
  return template
    .replace('{device_name}', deviceName)
    .replace('{value}', String(value))
    .replace('{unit}', unit)
    .replace('{threshold}', String(threshold))
}

export const useModbusStore = defineStore('modbus', () => {
  const devices = ref<Device[]>([])
  const alarms = ref<Alarm[]>([])
  const historyData = ref<Record<string, { time: number[]; values: number[] }>>({})
  const isPolling = ref(false)
  const pollInterval = ref(1000)
  const selectedDevice = ref<Device | null>(null)

  const deviceTypes = ref<DeviceType[]>([])
  const policies = ref<ThresholdPolicy[]>([])
  const applications = ref<PolicyApplication[]>([])
  const deviceRulesMap = ref<Record<string, DeviceAppliedRules>>({})

  const criticalAlarms = computed(() => alarms.value.filter(a => a.level === 'critical' && !a.acknowledged))
  const onlineDevices = computed(() => devices.value.filter(d => d.online))
  const devicePoliciesMap = computed(() => {
    const map: Record<string, ThresholdPolicy> = {}
    for (const p of policies.value) map[p.id] = p
    return map
  })
  const deviceTypeMap = computed(() => {
    const map: Record<string, DeviceType> = {}
    for (const dt of deviceTypes.value) map[dt.id] = dt
    return map
  })

  function initMockDevices() {
    devices.value = [
      {
        id: 'dev1', name: '温湿度传感器-A区', ip: '192.168.1.101', port: 502, slaveId: 1, online: true,
        registers: [
          { address: 0, name: '温度', type: 'holding', value: 25.6, unit: '°C', updatedAt: Date.now() },
          { address: 1, name: '湿度', type: 'holding', value: 62.3, unit: '%RH', updatedAt: Date.now() },
          { address: 2, name: '露点', type: 'holding', value: 17.8, unit: '°C', updatedAt: Date.now() },
        ]
      },
      {
        id: 'dev2', name: '压力变送器-B区', ip: '192.168.1.102', port: 502, slaveId: 2, online: true,
        registers: [
          { address: 0, name: '管道压力', type: 'holding', value: 3.45, unit: 'MPa', updatedAt: Date.now() },
          { address: 1, name: '差压', type: 'holding', value: 0.12, unit: 'kPa', updatedAt: Date.now() },
        ]
      },
      {
        id: 'dev3', name: '电机控制器-C区', ip: '192.168.1.103', port: 502, slaveId: 3, online: false,
        registers: [
          { address: 0, name: '转速', type: 'holding', value: 1480, unit: 'RPM', updatedAt: Date.now() },
          { address: 1, name: '电流', type: 'holding', value: 12.5, unit: 'A', updatedAt: Date.now() },
          { address: 2, name: '运行状态', type: 'coil', value: true, unit: '', updatedAt: Date.now() },
        ]
      },
      {
        id: 'dev4', name: '流量计-D区', ip: '192.168.1.104', port: 502, slaveId: 4, online: true,
        registers: [
          { address: 0, name: '瞬时流量', type: 'holding', value: 156.7, unit: 'L/min', updatedAt: Date.now() },
          { address: 1, name: '累计流量', type: 'holding', value: 98234, unit: 'L', updatedAt: Date.now() },
        ]
      },
    ]
    selectedDevice.value = devices.value[0]
  }

  function checkDeviceThresholds(dev: Device) {
    const applied = deviceRulesMap.value[dev.id]
    if (!applied || !applied.rules.length) return

    for (const reg of dev.registers) {
      if (typeof reg.value !== 'number') continue
      for (const rule of applied.rules) {
        if (!rule.enabled) continue
        if (rule.registerAddress !== reg.address && rule.registerName !== reg.name) continue
        if (evaluateCondition(reg.value, rule.operator, rule.threshold)) {
          const recentAlarm = alarms.value.find(a =>
            a.deviceId === dev.id && a.register === reg.name &&
            a.level === rule.level && !a.acknowledged &&
            Date.now() - a.timestamp < 30000
          )
          if (!recentAlarm) {
            alarms.value.unshift({
              id: `a_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
              deviceId: dev.id,
              register: reg.name,
              message: formatMessage(rule.messageTemplate, dev.name, reg.value, reg.unit, rule.threshold),
              level: rule.level as AlarmLevel,
              timestamp: Date.now(),
              acknowledged: false
            })
          }
        }
      }
    }
  }

  function simulatePoll() {
    for (const dev of devices.value) {
      if (!dev.online) continue
      for (const reg of dev.registers) {
        if (typeof reg.value === 'number') {
          const noise = (Math.random() - 0.5) * reg.value * 0.05
          reg.value = Math.round((reg.value + noise) * 100) / 100
          reg.updatedAt = Date.now()
          const key = `${dev.id}_${reg.address}`
          if (!historyData.value[key]) historyData.value[key] = { time: [], values: [] }
          historyData.value[key].time.push(Date.now())
          historyData.value[key].values.push(reg.value)
          if (historyData.value[key].time.length > 100) {
            historyData.value[key].time.shift()
            historyData.value[key].values.shift()
          }
        }
      }
      checkDeviceThresholds(dev)
    }
    if (alarms.value.length > 100) alarms.value = alarms.value.slice(0, 100)
  }

  function acknowledgeAlarm(id: string) {
    const a = alarms.value.find(a => a.id === id)
    if (a) a.acknowledged = true
  }

  function toggleDevice(id: string) {
    const d = devices.value.find(d => d.id === id)
    if (d) d.online = !d.online
  }

  async function loadDeviceTypes() {
    deviceTypes.value = await apiGet<DeviceType[]>('/device-types')
  }

  async function loadPolicies(deviceTypeId?: string) {
    const qs = deviceTypeId ? `?device_type_id=${deviceTypeId}` : ''
    policies.value = await apiGet<ThresholdPolicy[]>(`/policies${qs}`)
  }

  async function loadApplications(policyId?: string, deviceId?: string) {
    const params = new URLSearchParams()
    if (policyId) params.set('policy_id', policyId)
    if (deviceId) params.set('device_id', deviceId)
    const qs = params.toString() ? `?${params.toString()}` : ''
    applications.value = await apiGet<PolicyApplication[]>(`/applications${qs}`)
  }

  async function loadDeviceAppliedRules(deviceId: string) {
    const rules = await apiGet<DeviceAppliedRules>(`/devices/${deviceId}/applied-rules`)
    deviceRulesMap.value[deviceId] = rules
    return rules
  }

  async function loadAllDeviceRules() {
    for (const d of devices.value) {
      await loadDeviceAppliedRules(d.id)
    }
  }

  async function createPolicy(data: ThresholdPolicyCreate) {
    const created = await apiPost<ThresholdPolicy>('/policies', data)
    await loadPolicies()
    return created
  }

  async function updatePolicy(id: string, data: ThresholdPolicyUpdate) {
    const updated = await apiPut<ThresholdPolicy>(`/policies/${id}`, data)
    await loadPolicies()
    return updated
  }

  async function deletePolicy(id: string) {
    await apiDelete(`/policies/${id}`)
    await loadPolicies()
    await loadApplications()
  }

  async function batchApplyPolicy(policyId: string, deviceIds: string[]) {
    const result = await apiPost<BatchApplyResponse>('/policies/batch-apply', { policyId, deviceIds })
    await loadApplications()
    await loadAllDeviceRules()
    return result
  }

  async function unapplyPolicyFromDevice(deviceId: string) {
    await apiDelete(`/devices/${deviceId}/applied-policy`)
    await loadApplications()
    if (deviceRulesMap.value[deviceId]) {
      deviceRulesMap.value[deviceId] = { deviceId, policyId: null, policyName: null, rules: [] }
    }
  }

  async function registerDevicesToBackend() {
    const devicesToRegister = devices.value.map(d => ({
      deviceId: d.id,
      deviceTypeId: guessDeviceTypeId(d)
    })).filter(d => d.deviceTypeId)

    if (!devicesToRegister.length) return

    try {
      await apiPost('/devices/batch-register', { devices: devicesToRegister })
    } catch (e) {
      console.warn('设备注册跳过', e)
    }
  }

  function guessDeviceTypeId(device: Device): string | null {
    const registerNames = device.registers.map(r => r.name).sort().join(',')
    const patterns: Record<string, string> = {
      '温度,露点,湿度': 'dt_temp',
      '差压,管道压力': 'dt_pressure',
      '电流,转速,运行状态': 'dt_motor',
      '瞬时流量,累计流量': 'dt_flow',
    }
    return patterns[registerNames] || null
  }

  return {
    devices, alarms, historyData, isPolling, pollInterval, selectedDevice,
    deviceTypes, policies, applications, deviceRulesMap,
    criticalAlarms, onlineDevices, devicePoliciesMap, deviceTypeMap,
    initMockDevices, simulatePoll, acknowledgeAlarm, toggleDevice,
    loadDeviceTypes, loadPolicies, loadApplications, loadDeviceAppliedRules, loadAllDeviceRules,
    createPolicy, updatePolicy, deletePolicy, batchApplyPolicy, unapplyPolicyFromDevice,
    registerDevicesToBackend, guessDeviceTypeId
  }
})

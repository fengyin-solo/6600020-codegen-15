export interface ModbusRegister {
  address: number
  name: string
  type: 'coil' | 'discrete' | 'holding' | 'input'
  value: number | boolean
  unit: string
  updatedAt: number
}

export interface Device {
  id: string
  name: string
  ip: string
  port: number
  slaveId: number
  online: boolean
  registers: ModbusRegister[]
}

export interface Alarm {
  id: string
  deviceId: string
  register: string
  message: string
  level: 'info' | 'warning' | 'critical'
  timestamp: number
  acknowledged: boolean
}

export type AlarmLevel = 'info' | 'warning' | 'critical'
export type ConditionOperator = '>' | '>=' | '<' | '<=' | '==' | '!='

export interface DeviceType {
  id: string
  name: string
  description: string | null
  registerTemplates: ModbusRegister[]
  createdAt: string
  updatedAt: string
}

export interface ThresholdRule {
  id: string
  policyId: string
  registerName: string
  registerAddress: number
  operator: ConditionOperator
  threshold: number
  level: AlarmLevel
  messageTemplate: string
  enabled: boolean
  createdAt: string
  updatedAt: string
}

export interface ThresholdRuleCreate {
  registerName: string
  registerAddress: number
  operator: ConditionOperator
  threshold: number
  level: AlarmLevel
  messageTemplate: string
  enabled: boolean
}

export interface ThresholdPolicy {
  id: string
  name: string
  description: string | null
  deviceTypeId: string
  isDefault: boolean
  rules: ThresholdRule[]
  createdAt: string
  updatedAt: string
}

export interface ThresholdPolicyCreate {
  name: string
  description?: string | null
  deviceTypeId: string
  isDefault: boolean
  rules: ThresholdRuleCreate[]
}

export interface ThresholdPolicyUpdate {
  name?: string | null
  description?: string | null
  isDefault?: boolean | null
  rules?: ThresholdRuleCreate[] | null
}

export interface PolicyApplication {
  id: string
  policyId: string
  deviceId: string
  appliedAt: string
  appliedBy: string | null
}

export interface BatchApplyRequest {
  policyId: string
  deviceIds: string[]
}

export interface BatchApplyResponse {
  success: number
  failed: number
  results: Array<{
    deviceId: string
    success: boolean
    policyId?: string
    policyName?: string
    reason?: string
  }>
}

export interface DeviceAppliedRules {
  deviceId: string
  policyId: string | null
  policyName: string | null
  rules: ThresholdRule[]
}

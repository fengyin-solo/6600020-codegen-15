from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class ModbusRegister(BaseModel):
    address: int
    name: str
    type: str
    value: float
    unit: str

class Device(BaseModel):
    id: str
    name: str
    ip: str
    port: int
    slave_id: int
    online: bool
    registers: List[ModbusRegister] = []

class AlarmLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class ConditionOperator(str, Enum):
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "=="
    NEQ = "!="

class DeviceTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    register_templates: List[ModbusRegister] = []

class DeviceTypeCreate(DeviceTypeBase):
    pass

class DeviceType(DeviceTypeBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ThresholdRuleBase(BaseModel):
    register_name: str
    register_address: int
    operator: ConditionOperator
    threshold: float
    level: AlarmLevel
    message_template: str
    enabled: bool = True

class ThresholdRuleCreate(ThresholdRuleBase):
    pass

class ThresholdRule(ThresholdRuleBase):
    id: str
    policy_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ThresholdPolicyBase(BaseModel):
    name: str
    description: Optional[str] = None
    device_type_id: str
    is_default: bool = False

class ThresholdPolicyCreate(ThresholdPolicyBase):
    rules: List[ThresholdRuleCreate] = []

class ThresholdPolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    rules: Optional[List[ThresholdRuleCreate]] = None

class ThresholdPolicy(ThresholdPolicyBase):
    id: str
    rules: List[ThresholdRule] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PolicyApplicationBase(BaseModel):
    policy_id: str
    device_id: str

class PolicyApplicationCreate(BaseModel):
    policy_id: str
    device_ids: List[str]

class PolicyApplication(PolicyApplicationBase):
    id: str
    applied_at: datetime
    applied_by: Optional[str] = None

    class Config:
        from_attributes = True

class BatchApplyRequest(BaseModel):
    policy_id: str
    device_ids: List[str]

class BatchApplyResponse(BaseModel):
    success: int
    failed: int
    results: List[dict]

class DeviceAppliedRules(BaseModel):
    device_id: str
    policy_id: Optional[str] = None
    policy_name: Optional[str] = None
    rules: List[ThresholdRule] = []

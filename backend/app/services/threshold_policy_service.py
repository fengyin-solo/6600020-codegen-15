"""Threshold Policy Service with JSON file persistence and device type validation."""
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.models.schemas import (
    DeviceType, DeviceTypeCreate,
    ThresholdPolicy, ThresholdPolicyCreate, ThresholdPolicyUpdate,
    ThresholdRule, ThresholdRuleCreate,
    PolicyApplication,
    BatchApplyResponse, DeviceAppliedRules,
    AlarmLevel, ConditionOperator
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
APPLICATIONS_FILE = os.path.join(DATA_DIR, "applications.json")

DEVICE_TYPES: Dict[str, DeviceType] = {}
POLICIES: Dict[str, ThresholdPolicy] = {}
RULES: Dict[str, ThresholdRule] = {}
APPLICATIONS: Dict[str, PolicyApplication] = {}
DEVICE_TYPE_MAP: Dict[str, str] = {}


def _gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _now() -> datetime:
    return datetime.now()


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _save_applications():
    _ensure_data_dir()
    data = []
    for a in APPLICATIONS.values():
        data.append({
            "id": a.id,
            "policy_id": a.policy_id,
            "device_id": a.device_id,
            "applied_at": a.applied_at.isoformat() if isinstance(a.applied_at, datetime) else str(a.applied_at),
            "applied_by": a.applied_by
        })
    with open(APPLICATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_applications():
    if not os.path.exists(APPLICATIONS_FILE):
        return
    try:
        with open(APPLICATIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            parsed_at = item.get("applied_at", datetime.now().isoformat())
            if isinstance(parsed_at, str):
                try:
                    parsed_at = datetime.fromisoformat(parsed_at)
                except (ValueError, TypeError):
                    parsed_at = _now()
            app = PolicyApplication(
                id=item["id"],
                policy_id=item["policy_id"],
                device_id=item["device_id"],
                applied_at=parsed_at,
                applied_by=item.get("applied_by")
            )
            APPLICATIONS[app.id] = app
    except (json.JSONDecodeError, KeyError, TypeError):
        pass


def register_device(device_id: str, device_type_id: str):
    DEVICE_TYPE_MAP[device_id] = device_type_id


def get_device_type_id(device_id: str) -> Optional[str]:
    return DEVICE_TYPE_MAP.get(device_id)


def init_mock_data():
    DEVICE_TYPES.clear()
    POLICIES.clear()
    RULES.clear()
    APPLICATIONS.clear()
    DEVICE_TYPE_MAP.clear()

    temp_sensor = DeviceType(
        id="dt_temp",
        name="温湿度传感器",
        description="用于监测环境温湿度的传感器设备",
        register_templates=[
            {"address": 0, "name": "温度", "type": "holding", "value": 0, "unit": "°C"},
            {"address": 1, "name": "湿度", "type": "holding", "value": 0, "unit": "%RH"},
            {"address": 2, "name": "露点", "type": "holding", "value": 0, "unit": "°C"},
        ],
        created_at=_now(),
        updated_at=_now()
    )
    DEVICE_TYPES[temp_sensor.id] = temp_sensor

    pressure = DeviceType(
        id="dt_pressure",
        name="压力变送器",
        description="用于监测管道压力的变送器",
        register_templates=[
            {"address": 0, "name": "管道压力", "type": "holding", "value": 0, "unit": "MPa"},
            {"address": 1, "name": "差压", "type": "holding", "value": 0, "unit": "kPa"},
        ],
        created_at=_now(),
        updated_at=_now()
    )
    DEVICE_TYPES[pressure.id] = pressure

    motor = DeviceType(
        id="dt_motor",
        name="电机控制器",
        description="用于控制和监测电机运行状态的控制器",
        register_templates=[
            {"address": 0, "name": "转速", "type": "holding", "value": 0, "unit": "RPM"},
            {"address": 1, "name": "电流", "type": "holding", "value": 0, "unit": "A"},
            {"address": 2, "name": "运行状态", "type": "coil", "value": 0, "unit": ""},
        ],
        created_at=_now(),
        updated_at=_now()
    )
    DEVICE_TYPES[motor.id] = motor

    flow = DeviceType(
        id="dt_flow",
        name="流量计",
        description="用于测量流体流量的仪表",
        register_templates=[
            {"address": 0, "name": "瞬时流量", "type": "holding", "value": 0, "unit": "L/min"},
            {"address": 1, "name": "累计流量", "type": "holding", "value": 0, "unit": "L"},
        ],
        created_at=_now(),
        updated_at=_now()
    )
    DEVICE_TYPES[flow.id] = flow

    register_device("dev1", "dt_temp")
    register_device("dev2", "dt_pressure")
    register_device("dev3", "dt_motor")
    register_device("dev4", "dt_flow")

    policy1 = ThresholdPolicy(
        id="pol_temp_standard",
        name="温湿度传感器-标准告警策略",
        description="适用于常规环境的温湿度告警规则",
        device_type_id="dt_temp",
        is_default=True,
        rules=[],
        created_at=_now(),
        updated_at=_now()
    )
    POLICIES[policy1.id] = policy1

    rule1_1 = ThresholdRule(
        id=_gen_id("rule"),
        policy_id=policy1.id,
        register_name="温度",
        register_address=0,
        operator=ConditionOperator.GT,
        threshold=28.0,
        level=AlarmLevel.WARNING,
        message_template="{device_name} 温度过高: {value}{unit}，阈值 {threshold}{unit}",
        enabled=True,
        created_at=_now(),
        updated_at=_now()
    )
    RULES[rule1_1.id] = rule1_1

    rule1_2 = ThresholdRule(
        id=_gen_id("rule"),
        policy_id=policy1.id,
        register_name="温度",
        register_address=0,
        operator=ConditionOperator.GT,
        threshold=32.0,
        level=AlarmLevel.CRITICAL,
        message_template="{device_name} 温度严重超限: {value}{unit}，阈值 {threshold}{unit}",
        enabled=True,
        created_at=_now(),
        updated_at=_now()
    )
    RULES[rule1_2.id] = rule1_2

    rule1_3 = ThresholdRule(
        id=_gen_id("rule"),
        policy_id=policy1.id,
        register_name="湿度",
        register_address=1,
        operator=ConditionOperator.GT,
        threshold=80.0,
        level=AlarmLevel.WARNING,
        message_template="{device_name} 湿度过高: {value}{unit}，阈值 {threshold}{unit}",
        enabled=True,
        created_at=_now(),
        updated_at=_now()
    )
    RULES[rule1_3.id] = rule1_3

    rule1_4 = ThresholdRule(
        id=_gen_id("rule"),
        policy_id=policy1.id,
        register_name="温度",
        register_address=0,
        operator=ConditionOperator.LT,
        threshold=5.0,
        level=AlarmLevel.WARNING,
        message_template="{device_name} 温度过低: {value}{unit}，阈值 {threshold}{unit}",
        enabled=True,
        created_at=_now(),
        updated_at=_now()
    )
    RULES[rule1_4.id] = rule1_4

    policy2 = ThresholdPolicy(
        id="pol_pressure_standard",
        name="压力变送器-标准告警策略",
        description="常规压力监测告警策略",
        device_type_id="dt_pressure",
        is_default=True,
        rules=[],
        created_at=_now(),
        updated_at=_now()
    )
    POLICIES[policy2.id] = policy2

    rule2_1 = ThresholdRule(
        id=_gen_id("rule"),
        policy_id=policy2.id,
        register_name="管道压力",
        register_address=0,
        operator=ConditionOperator.GT,
        threshold=5.0,
        level=AlarmLevel.WARNING,
        message_template="{device_name} 压力过高: {value}{unit}，阈值 {threshold}{unit}",
        enabled=True,
        created_at=_now(),
        updated_at=_now()
    )
    RULES[rule2_1.id] = rule2_1

    rule2_2 = ThresholdRule(
        id=_gen_id("rule"),
        policy_id=policy2.id,
        register_name="管道压力",
        register_address=0,
        operator=ConditionOperator.LT,
        threshold=0.5,
        level=AlarmLevel.WARNING,
        message_template="{device_name} 压力过低: {value}{unit}，阈值 {threshold}{unit}",
        enabled=True,
        created_at=_now(),
        updated_at=_now()
    )
    RULES[rule2_2.id] = rule2_2

    policy3 = ThresholdPolicy(
        id="pol_motor_standard",
        name="电机控制器-标准告警策略",
        description="电机运行状态监控策略",
        device_type_id="dt_motor",
        is_default=True,
        rules=[],
        created_at=_now(),
        updated_at=_now()
    )
    POLICIES[policy3.id] = policy3

    rule3_1 = ThresholdRule(
        id=_gen_id("rule"),
        policy_id=policy3.id,
        register_name="电流",
        register_address=1,
        operator=ConditionOperator.GT,
        threshold=15.0,
        level=AlarmLevel.WARNING,
        message_template="{device_name} 电流过高: {value}{unit}，阈值 {threshold}{unit}",
        enabled=True,
        created_at=_now(),
        updated_at=_now()
    )
    RULES[rule3_1.id] = rule3_1

    rule3_2 = ThresholdRule(
        id=_gen_id("rule"),
        policy_id=policy3.id,
        register_name="转速",
        register_address=0,
        operator=ConditionOperator.GT,
        threshold=1800.0,
        level=AlarmLevel.CRITICAL,
        message_template="{device_name} 转速严重超限: {value}{unit}，阈值 {threshold}{unit}",
        enabled=True,
        created_at=_now(),
        updated_at=_now()
    )
    RULES[rule3_2.id] = rule3_2

    policy4 = ThresholdPolicy(
        id="pol_flow_standard",
        name="流量计-标准告警策略",
        description="流量监测告警策略",
        device_type_id="dt_flow",
        is_default=True,
        rules=[],
        created_at=_now(),
        updated_at=_now()
    )
    POLICIES[policy4.id] = policy4

    rule4_1 = ThresholdRule(
        id=_gen_id("rule"),
        policy_id=policy4.id,
        register_name="瞬时流量",
        register_address=0,
        operator=ConditionOperator.GT,
        threshold=200.0,
        level=AlarmLevel.WARNING,
        message_template="{device_name} 瞬时流量过大: {value}{unit}，阈值 {threshold}{unit}",
        enabled=True,
        created_at=_now(),
        updated_at=_now()
    )
    RULES[rule4_1.id] = rule4_1

    rule4_2 = ThresholdRule(
        id=_gen_id("rule"),
        policy_id=policy4.id,
        register_name="瞬时流量",
        register_address=0,
        operator=ConditionOperator.LT,
        threshold=10.0,
        level=AlarmLevel.INFO,
        message_template="{device_name} 瞬时流量过低: {value}{unit}，阈值 {threshold}{unit}",
        enabled=True,
        created_at=_now(),
        updated_at=_now()
    )
    RULES[rule4_2.id] = rule4_2

    _load_applications()

    _auto_apply_defaults()


def _auto_apply_defaults():
    for dt_id, dt in DEVICE_TYPES.items():
        default_policy = None
        for p in POLICIES.values():
            if p.device_type_id == dt_id and p.is_default:
                default_policy = p
                break
        if not default_policy:
            continue
        for device_id, dev_dt_id in DEVICE_TYPE_MAP.items():
            if dev_dt_id != dt_id:
                continue
            already_has = False
            for a in APPLICATIONS.values():
                if a.device_id == device_id:
                    already_has = True
                    break
            if not already_has:
                app = PolicyApplication(
                    id=_gen_id("app"),
                    policy_id=default_policy.id,
                    device_id=device_id,
                    applied_at=_now(),
                    applied_by="auto_default"
                )
                APPLICATIONS[app.id] = app
    _save_applications()


def _populate_rules(policy: ThresholdPolicy) -> ThresholdPolicy:
    policy.rules = [r for r in RULES.values() if r.policy_id == policy.id]
    return policy


def list_device_types() -> List[DeviceType]:
    return list(DEVICE_TYPES.values())


def get_device_type(dt_id: str) -> Optional[DeviceType]:
    return DEVICE_TYPES.get(dt_id)


def create_device_type(data: DeviceTypeCreate) -> DeviceType:
    dt = DeviceType(
        id=_gen_id("dt"),
        name=data.name,
        description=data.description,
        register_templates=data.register_templates,
        created_at=_now(),
        updated_at=_now()
    )
    DEVICE_TYPES[dt.id] = dt
    return dt


def update_device_type(dt_id: str, data: DeviceTypeCreate) -> Optional[DeviceType]:
    dt = DEVICE_TYPES.get(dt_id)
    if not dt:
        return None
    dt.name = data.name
    dt.description = data.description
    dt.register_templates = data.register_templates
    dt.updated_at = _now()
    return dt


def delete_device_type(dt_id: str) -> bool:
    if dt_id in DEVICE_TYPES:
        del DEVICE_TYPES[dt_id]
        for pid in list(POLICIES.keys()):
            if POLICIES[pid].device_type_id == dt_id:
                delete_policy(pid)
        for did in list(DEVICE_TYPE_MAP.keys()):
            if DEVICE_TYPE_MAP[did] == dt_id:
                del DEVICE_TYPE_MAP[did]
        return True
    return False


def list_policies(device_type_id: Optional[str] = None) -> List[ThresholdPolicy]:
    result = []
    for p in POLICIES.values():
        if device_type_id and p.device_type_id != device_type_id:
            continue
        result.append(_populate_rules(p))
    return result


def get_policy(policy_id: str) -> Optional[ThresholdPolicy]:
    p = POLICIES.get(policy_id)
    if p:
        return _populate_rules(p)
    return None


def create_policy(data: ThresholdPolicyCreate) -> ThresholdPolicy:
    now = _now()
    policy = ThresholdPolicy(
        id=_gen_id("pol"),
        name=data.name,
        description=data.description,
        device_type_id=data.device_type_id,
        is_default=data.is_default,
        rules=[],
        created_at=now,
        updated_at=now
    )
    POLICIES[policy.id] = policy

    if data.is_default:
        for other in POLICIES.values():
            if other.device_type_id == policy.device_type_id and other.id != policy.id:
                other.is_default = False

    for rule_data in data.rules:
        rule = ThresholdRule(
            id=_gen_id("rule"),
            policy_id=policy.id,
            register_name=rule_data.register_name,
            register_address=rule_data.register_address,
            operator=rule_data.operator,
            threshold=rule_data.threshold,
            level=rule_data.level,
            message_template=rule_data.message_template,
            enabled=rule_data.enabled,
            created_at=now,
            updated_at=now
        )
        RULES[rule.id] = rule

    return _populate_rules(policy)


def update_policy(policy_id: str, data: ThresholdPolicyUpdate) -> Optional[ThresholdPolicy]:
    policy = POLICIES.get(policy_id)
    if not policy:
        return None

    now = _now()
    if data.name is not None:
        policy.name = data.name
    if data.description is not None:
        policy.description = data.description
    if data.is_default is not None:
        policy.is_default = data.is_default
        if data.is_default:
            for other in POLICIES.values():
                if other.device_type_id == policy.device_type_id and other.id != policy.id:
                    other.is_default = False
    policy.updated_at = now

    if data.rules is not None:
        for rid in list(RULES.keys()):
            if RULES[rid].policy_id == policy_id:
                del RULES[rid]
        for rule_data in data.rules:
            rule = ThresholdRule(
                id=_gen_id("rule"),
                policy_id=policy.id,
                register_name=rule_data.register_name,
                register_address=rule_data.register_address,
                operator=rule_data.operator,
                threshold=rule_data.threshold,
                level=rule_data.level,
                message_template=rule_data.message_template,
                enabled=rule_data.enabled,
                created_at=now,
                updated_at=now
            )
            RULES[rule.id] = rule

    return _populate_rules(policy)


def delete_policy(policy_id: str) -> bool:
    if policy_id in POLICIES:
        del POLICIES[policy_id]
        for rid in list(RULES.keys()):
            if RULES[rid].policy_id == policy_id:
                del RULES[rid]
        changed = False
        for aid in list(APPLICATIONS.keys()):
            if APPLICATIONS[aid].policy_id == policy_id:
                del APPLICATIONS[aid]
                changed = True
        if changed:
            _save_applications()
        return True
    return False


def batch_apply_policy(policy_id: str, device_ids: List[str]) -> BatchApplyResponse:
    policy = POLICIES.get(policy_id)
    if not policy:
        return BatchApplyResponse(success=0, failed=len(device_ids),
                                  results=[{"device_id": d, "success": False, "reason": "策略不存在"} for d in device_ids])

    results = []
    success_count = 0
    failed_count = 0

    for did in device_ids:
        dev_dt_id = DEVICE_TYPE_MAP.get(did)
        if dev_dt_id is None:
            results.append({"device_id": did, "success": False, "reason": "设备未注册，无法确定设备类型"})
            failed_count += 1
            continue

        if dev_dt_id != policy.device_type_id:
            dt_name = DEVICE_TYPES.get(dev_dt_id, DeviceType(id="", name="未知", description=None, register_templates=[], created_at=_now(), updated_at=_now())).name
            policy_dt_name = DEVICE_TYPES.get(policy.device_type_id, DeviceType(id="", name="未知", description=None, register_templates=[], created_at=_now(), updated_at=_now())).name
            results.append({
                "device_id": did,
                "success": False,
                "reason": f"设备类型不匹配: 设备属于「{dt_name}」，策略要求「{policy_dt_name}」"
            })
            failed_count += 1
            continue

        try:
            existing = None
            for a in APPLICATIONS.values():
                if a.device_id == did:
                    existing = a
                    break
            if existing:
                del APPLICATIONS[existing.id]

            app = PolicyApplication(
                id=_gen_id("app"),
                policy_id=policy_id,
                device_id=did,
                applied_at=_now(),
                applied_by="system"
            )
            APPLICATIONS[app.id] = app
            results.append({"device_id": did, "success": True, "policy_id": policy_id, "policy_name": policy.name})
            success_count += 1
        except Exception as e:
            results.append({"device_id": did, "success": False, "reason": str(e)})
            failed_count += 1

    _save_applications()
    return BatchApplyResponse(success=success_count, failed=failed_count, results=results)


def list_applications(policy_id: Optional[str] = None, device_id: Optional[str] = None) -> List[PolicyApplication]:
    result = []
    for a in APPLICATIONS.values():
        if policy_id and a.policy_id != policy_id:
            continue
        if device_id and a.device_id != device_id:
            continue
        result.append(a)
    return result


def get_device_applied_rules(device_id: str) -> DeviceAppliedRules:
    app = None
    for a in APPLICATIONS.values():
        if a.device_id == device_id:
            app = a
            break

    if not app:
        return DeviceAppliedRules(device_id=device_id, policy_id=None, policy_name=None, rules=[])

    policy = POLICIES.get(app.policy_id)
    if not policy:
        return DeviceAppliedRules(device_id=device_id, policy_id=app.policy_id, policy_name=None, rules=[])

    rules = [r for r in RULES.values() if r.policy_id == policy.id]
    return DeviceAppliedRules(
        device_id=device_id,
        policy_id=policy.id,
        policy_name=policy.name,
        rules=rules
    )


def unapply_policy(device_id: str) -> bool:
    changed = False
    for aid in list(APPLICATIONS.keys()):
        if APPLICATIONS[aid].device_id == device_id:
            del APPLICATIONS[aid]
            changed = True
    if changed:
        _save_applications()
        return True
    return False


def list_registered_devices() -> List[Dict[str, Any]]:
    result = []
    for device_id, dt_id in DEVICE_TYPE_MAP.items():
        dt = DEVICE_TYPES.get(dt_id)
        applied = None
        for a in APPLICATIONS.values():
            if a.device_id == device_id:
                applied = a
                break
        result.append({
            "device_id": device_id,
            "device_type_id": dt_id,
            "device_type_name": dt.name if dt else "未知",
            "applied_policy_id": applied.policy_id if applied else None,
            "applied_policy_name": POLICIES.get(applied.policy_id).name if applied and POLICIES.get(applied.policy_id) else None,
        })
    return result


init_mock_data()

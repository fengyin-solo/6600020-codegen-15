from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.schemas import (
    DeviceType, DeviceTypeCreate,
    ThresholdPolicy, ThresholdPolicyCreate, ThresholdPolicyUpdate,
    PolicyApplication,
    BatchApplyRequest, BatchApplyResponse,
    DeviceAppliedRules
)
from app.services import threshold_policy_service as svc
from pydantic import BaseModel

router = APIRouter()


class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_type_id: str


class BatchDeviceRegisterRequest(BaseModel):
    devices: List[DeviceRegisterRequest]


@router.get("/device-types", response_model=List[DeviceType])
def list_device_types():
    return svc.list_device_types()


@router.get("/device-types/{dt_id}", response_model=DeviceType)
def get_device_type(dt_id: str):
    dt = svc.get_device_type(dt_id)
    if not dt:
        raise HTTPException(status_code=404, detail="设备类型不存在")
    return dt


@router.post("/device-types", response_model=DeviceType)
def create_device_type(data: DeviceTypeCreate):
    return svc.create_device_type(data)


@router.put("/device-types/{dt_id}", response_model=DeviceType)
def update_device_type(dt_id: str, data: DeviceTypeCreate):
    dt = svc.update_device_type(dt_id, data)
    if not dt:
        raise HTTPException(status_code=404, detail="设备类型不存在")
    return dt


@router.delete("/device-types/{dt_id}")
def delete_device_type(dt_id: str):
    if not svc.delete_device_type(dt_id):
        raise HTTPException(status_code=404, detail="设备类型不存在")
    return {"status": "deleted"}


@router.get("/devices", response_model=List[dict])
def list_registered_devices():
    return svc.list_registered_devices()


@router.post("/devices/register")
def register_device(data: DeviceRegisterRequest):
    if not svc.get_device_type(data.device_type_id):
        raise HTTPException(status_code=400, detail="设备类型不存在")
    svc.register_device(data.device_id, data.device_type_id)
    return {"status": "registered", "device_id": data.device_id, "device_type_id": data.device_type_id}


@router.post("/devices/batch-register")
def batch_register_devices(data: BatchDeviceRegisterRequest):
    results = []
    for d in data.devices:
        if not svc.get_device_type(d.device_type_id):
            results.append({"device_id": d.device_id, "success": False, "reason": "设备类型不存在"})
            continue
        svc.register_device(d.device_id, d.device_type_id)
        results.append({"device_id": d.device_id, "success": True, "device_type_id": d.device_type_id})
    return {"results": results}


@router.get("/policies", response_model=List[ThresholdPolicy])
def list_policies(device_type_id: Optional[str] = Query(None, description="按设备类型筛选")):
    return svc.list_policies(device_type_id)


@router.get("/policies/{policy_id}", response_model=ThresholdPolicy)
def get_policy(policy_id: str):
    p = svc.get_policy(policy_id)
    if not p:
        raise HTTPException(status_code=404, detail="策略不存在")
    return p


@router.post("/policies", response_model=ThresholdPolicy)
def create_policy(data: ThresholdPolicyCreate):
    if not svc.get_device_type(data.device_type_id):
        raise HTTPException(status_code=400, detail="设备类型不存在")
    return svc.create_policy(data)


@router.put("/policies/{policy_id}", response_model=ThresholdPolicy)
def update_policy(policy_id: str, data: ThresholdPolicyUpdate):
    p = svc.update_policy(policy_id, data)
    if not p:
        raise HTTPException(status_code=404, detail="策略不存在")
    return p


@router.delete("/policies/{policy_id}")
def delete_policy(policy_id: str):
    if not svc.delete_policy(policy_id):
        raise HTTPException(status_code=404, detail="策略不存在")
    return {"status": "deleted"}


@router.post("/policies/batch-apply", response_model=BatchApplyResponse)
def batch_apply_policy(data: BatchApplyRequest):
    return svc.batch_apply_policy(data.policy_id, data.device_ids)


@router.get("/applications", response_model=List[PolicyApplication])
def list_applications(
    policy_id: Optional[str] = Query(None),
    device_id: Optional[str] = Query(None)
):
    return svc.list_applications(policy_id, device_id)


@router.get("/devices/{device_id}/applied-rules", response_model=DeviceAppliedRules)
def get_device_applied_rules(device_id: str):
    return svc.get_device_applied_rules(device_id)


@router.delete("/devices/{device_id}/applied-policy")
def unapply_policy_from_device(device_id: str):
    if not svc.unapply_policy(device_id):
        raise HTTPException(status_code=404, detail="设备未应用任何策略")
    return {"status": "unapplied"}

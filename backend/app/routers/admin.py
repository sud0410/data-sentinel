import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import Alert, User
from app.schemas import AlertOut, DAGTriggerRequest, DAGTriggerResponse
from app.services import require_admin

settings = get_settings()
router = APIRouter(prefix="/admin", tags=["admin"])

ALLOWED_DAGS = {"daily_aggregation_dag", "data_quality_dag"}


@router.post("/trigger-dag", response_model=DAGTriggerResponse)
async def trigger_dag(
    payload: DAGTriggerRequest,
    _: User = Depends(require_admin),
):
    if payload.dag_id not in ALLOWED_DAGS:
        raise HTTPException(status_code=400, detail=f"DAG '{payload.dag_id}' is not allowed")

    url = f"{settings.airflow_base_url}/api/v1/dags/{payload.dag_id}/dagRuns"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            url,
            json={"conf": payload.conf},
            auth=(settings.airflow_username, settings.airflow_password),
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail=f"Airflow error: {resp.text}")

    data = resp.json()
    return DAGTriggerResponse(dag_run_id=data["dag_run_id"], state=data["state"])


@router.get("/alerts", response_model=list[AlertOut])
async def list_alerts(
    resolved: bool | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = select(Alert).order_by(Alert.created_at.desc()).limit(limit)
    if resolved is not None:
        q = q.where(Alert.resolved == resolved)
    result = await db.execute(q)
    return result.scalars().all()


@router.patch("/alerts/{alert_id}/resolve", response_model=AlertOut)
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.resolved = True
    await db.commit()
    await db.refresh(alert)
    return alert

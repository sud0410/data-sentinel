from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import DQMetric, User
from app.schemas import DQMetricOut
from app.services import get_current_user

router = APIRouter(prefix="/dq", tags=["data-quality"])


@router.get("/metrics", response_model=list[DQMetricOut])
async def list_metrics(
    check_name: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(DQMetric).order_by(DQMetric.computed_at.desc()).limit(limit)
    if check_name:
        q = q.where(DQMetric.check_name == check_name)
    result = await db.execute(q)
    return result.scalars().all()

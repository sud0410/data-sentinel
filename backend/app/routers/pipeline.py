from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import PipelineRun
from app.schemas import LiveStatsOut, PipelineRunOut
from app.services import get_current_user, get_live_stats
from app.models import User

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/runs", response_model=list[PipelineRunOut])
async def list_runs(
    dag_id: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(PipelineRun).order_by(PipelineRun.run_date.desc()).limit(limit)
    if dag_id:
        q = q.where(PipelineRun.dag_id == dag_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/stats", response_model=LiveStatsOut)
async def live_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await get_live_stats(db)

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PipelineRun, Transaction
from app.schemas import LiveStatsOut


async def get_live_stats(db: AsyncSession) -> LiveStatsOut:
    total_result = await db.execute(select(func.count()).select_from(Transaction))
    total = total_result.scalar() or 0

    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    hour_result = await db.execute(
        select(func.count()).select_from(Transaction).where(Transaction.timestamp >= one_hour_ago)
    )
    last_hour = hour_result.scalar() or 0

    run_result = await db.execute(
        select(PipelineRun).order_by(PipelineRun.run_date.desc()).limit(1)
    )
    last_run = run_result.scalar_one_or_none()

    one_min_ago = datetime.now(timezone.utc) - timedelta(minutes=1)
    rate_result = await db.execute(
        select(func.count()).select_from(Transaction).where(Transaction.timestamp >= one_min_ago)
    )
    rate = float(rate_result.scalar() or 0)

    return LiveStatsOut(
        total_transactions=total,
        transactions_last_hour=last_hour,
        active_pipelines=2,
        last_run_status=last_run.status if last_run else None,
        ingestion_rate_per_minute=rate,
    )

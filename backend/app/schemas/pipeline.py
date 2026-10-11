from datetime import datetime

from pydantic import BaseModel


class PipelineRunOut(BaseModel):
    id: int
    dag_id: str
    run_date: datetime
    status: str
    row_count: int | None
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class LiveStatsOut(BaseModel):
    total_transactions: int
    transactions_last_hour: int
    active_pipelines: int
    last_run_status: str | None
    ingestion_rate_per_minute: float


class DQMetricOut(BaseModel):
    id: int
    dag_id: str
    check_name: str
    metric_value: float | None
    threshold: float | None
    passed: bool
    run_date: datetime
    computed_at: datetime

    model_config = {"from_attributes": True}


class AlertOut(BaseModel):
    id: int
    source: str
    severity: str
    message: str
    resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DAGTriggerRequest(BaseModel):
    dag_id: str
    conf: dict = {}


class DAGTriggerResponse(BaseModel):
    dag_run_id: str
    state: str

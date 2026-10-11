import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.email import send_email

ALERT_EMAIL = os.getenv("ALERT_EMAIL", "alerts@example.com")
NULL_RATE_THRESHOLD = 0.05
ROW_COUNT_DRIFT_THRESHOLD = 0.40
default_args = {
    "owner": "datasentinel",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
}


def _ensure_dq_table(hook: PostgresHook):
    hook.run("""
        CREATE TABLE IF NOT EXISTS dq_metrics (
            id              SERIAL PRIMARY KEY,
            dag_id          TEXT NOT NULL,
            check_name      TEXT NOT NULL,
            metric_value    NUMERIC(10, 6),
            threshold       NUMERIC(10, 6),
            passed          BOOLEAN NOT NULL,
            run_date        DATE NOT NULL DEFAULT CURRENT_DATE,
            computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)


def _send_alert(check_name: str, metric: float, threshold: float):
    body = f"""
    <h3>DataSentinel DQ Alert</h3>
    <p>Check <strong>{check_name}</strong> failed.</p>
    <ul>
        <li>Metric value: {metric:.4f}</li>
        <li>Threshold: {threshold:.4f}</li>
        <li>Time: {datetime.utcnow().isoformat()}Z</li>
    </ul>
    """
    try:
        send_email(to=ALERT_EMAIL, subject=f"[DataSentinel] DQ Failure: {check_name}", html_content=body)
    except Exception as exc:
        print(f"[dq_dag] email alert failed: {exc}")


def check_null_rate(**context):
    hook = PostgresHook(postgres_conn_id="datasentinel_postgres")
    _ensure_dq_table(hook)
    run_date = context["ds"]

    rows = hook.get_records(f"""
        SELECT
            COUNT(*) FILTER (WHERE user_id IS NULL OR merchant IS NULL OR amount IS NULL) AS null_count,
            COUNT(*) AS total
        FROM transactions
        WHERE DATE(timestamp) = '{run_date}';
    """)
    total = rows[0][1] or 1
    null_count = rows[0][0]
    rate = null_count / total
    passed = rate <= NULL_RATE_THRESHOLD

    hook.run(f"""
        INSERT INTO dq_metrics (dag_id, check_name, metric_value, threshold, passed)
        VALUES ('data_quality_dag', 'null_rate', {rate}, {NULL_RATE_THRESHOLD}, {passed});
    """)

    if not passed:
        _send_alert("null_rate", rate, NULL_RATE_THRESHOLD)
        raise ValueError(f"null_rate {rate:.4f} exceeds threshold {NULL_RATE_THRESHOLD}")


def check_row_count_drift(**context):
    hook = PostgresHook(postgres_conn_id="datasentinel_postgres")
    _ensure_dq_table(hook)
    run_date = context["ds"]

    rows = hook.get_records(f"""
        SELECT
            (SELECT COUNT(*) FROM transactions WHERE DATE(timestamp) = '{run_date}') AS today,
            (SELECT COUNT(*) FROM transactions WHERE DATE(timestamp) = '{run_date}'::date - 1) AS yesterday;
    """)
    today = rows[0][0] or 0
    yesterday = rows[0][1] or 1
    drift = abs(today - yesterday) / yesterday
    passed = drift <= ROW_COUNT_DRIFT_THRESHOLD

    hook.run(f"""
        INSERT INTO dq_metrics (dag_id, check_name, metric_value, threshold, passed)
        VALUES ('data_quality_dag', 'row_count_drift', {drift}, {ROW_COUNT_DRIFT_THRESHOLD}, {passed});
    """)

    if not passed:
        _send_alert("row_count_drift", drift, ROW_COUNT_DRIFT_THRESHOLD)
        raise ValueError(f"row_count_drift {drift:.4f} exceeds threshold {ROW_COUNT_DRIFT_THRESHOLD}")


def check_duplicates(**context):
    hook = PostgresHook(postgres_conn_id="datasentinel_postgres")
    _ensure_dq_table(hook)
    run_date = context["ds"]

    rows = hook.get_records(f"""
        SELECT COUNT(*) FROM (
            SELECT transaction_id, COUNT(*) AS cnt
            FROM transactions
            WHERE DATE(timestamp) = '{run_date}'
            GROUP BY transaction_id
            HAVING COUNT(*) > 1
        ) dupes;
    """)
    dup_count = rows[0][0]
    passed = dup_count == 0

    hook.run(f"""
        INSERT INTO dq_metrics (dag_id, check_name, metric_value, threshold, passed)
        VALUES ('data_quality_dag', 'duplicate_count', {dup_count}, 0, {passed});
    """)

    if not passed:
        _send_alert("duplicate_count", dup_count, 0)
        raise ValueError(f"Found {dup_count} duplicate transaction_ids")


with DAG(
    dag_id="data_quality_dag",
    default_args=default_args,
    description="Data quality checks: null rate, row count drift, duplicates",
    schedule="0 2 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["datasentinel", "data-quality"],
) as dag:
    t_null = PythonOperator(task_id="check_null_rate", python_callable=check_null_rate)
    t_drift = PythonOperator(task_id="check_row_count_drift", python_callable=check_row_count_drift)
    t_dupes = PythonOperator(task_id="check_duplicates", python_callable=check_duplicates)

    t_null >> t_drift >> t_dupes

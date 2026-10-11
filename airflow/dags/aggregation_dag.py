from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

default_args = {
    "owner": "datasentinel",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def run_aggregation(**context):
    hook = PostgresHook(postgres_conn_id="datasentinel_postgres")
    run_date = context["ds"]

    hook.run("""
        CREATE TABLE IF NOT EXISTS daily_aggregations (
            agg_date        DATE NOT NULL,
            user_id         TEXT NOT NULL,
            category        TEXT NOT NULL,
            total_amount    NUMERIC(14, 2) NOT NULL,
            transaction_count INTEGER NOT NULL,
            computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (agg_date, user_id, category)
        );
    """)

    hook.run(f"""
        INSERT INTO daily_aggregations (agg_date, user_id, category, total_amount, transaction_count)
        SELECT
            DATE(timestamp) AS agg_date,
            user_id,
            category,
            SUM(amount)    AS total_amount,
            COUNT(*)       AS transaction_count
        FROM transactions
        WHERE DATE(timestamp) = '{run_date}'
        GROUP BY DATE(timestamp), user_id, category
        ON CONFLICT (agg_date, user_id, category) DO UPDATE
            SET total_amount      = EXCLUDED.total_amount,
                transaction_count = EXCLUDED.transaction_count,
                computed_at       = NOW();
    """)

    hook.run("""
        INSERT INTO pipeline_runs (dag_id, run_date, status, row_count, started_at, finished_at)
        VALUES (
            'daily_aggregation_dag',
            NOW()::date,
            'success',
            (SELECT COUNT(*) FROM daily_aggregations WHERE agg_date = NOW()::date),
            NOW(),
            NOW()
        )
        ON CONFLICT DO NOTHING;
    """)


with DAG(
    dag_id="daily_aggregation_dag",
    default_args=default_args,
    description="Aggregate daily spend per user and category from raw transactions",
    schedule="0 1 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["datasentinel", "aggregation"],
) as dag:
    aggregate = PythonOperator(
        task_id="aggregate_daily_spend",
        python_callable=run_aggregation,
    )

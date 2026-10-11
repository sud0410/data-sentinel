import json
import os
import signal
import sys
from datetime import datetime, timezone

from confluent_kafka import Consumer, KafkaError
from pydantic import ValidationError
from schemas import TransactionEvent
from sqlalchemy import Column, DateTime, Numeric, String, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "financial.transactions")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "datasentinel-consumer")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "datasentinel")
POSTGRES_USER = os.getenv("POSTGRES_USER", "datasentinel")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "changeme")

DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    merchant = Column(String, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    ingested_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


def init_db():
    Base.metadata.create_all(engine)


def process_message(raw: bytes, session: Session) -> bool:
    try:
        data = json.loads(raw)
        event = TransactionEvent.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        print(f"[consumer] schema validation failed: {exc}")
        return False

    existing = session.get(Transaction, str(event.transaction_id))
    if existing:
        return True

    tx = Transaction(
        transaction_id=str(event.transaction_id),
        user_id=event.user_id,
        merchant=event.merchant,
        category=event.category.value,
        amount=event.amount,
        currency=event.currency,
        timestamp=event.timestamp,
    )
    session.add(tx)
    session.commit()
    return True


def main():
    init_db()

    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": KAFKA_GROUP_ID,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([KAFKA_TOPIC])
    print(f"[consumer] subscribed to {KAFKA_TOPIC}")

    running = True

    def shutdown(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    with Session(engine) as session:
        while running:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    print(f"[consumer] error: {msg.error()}")
                continue

            success = process_message(msg.value(), session)
            if success:
                consumer.commit(asynchronous=False)

    consumer.close()
    print("[consumer] closed")


if __name__ == "__main__":
    main()

import json
import os
import random
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from confluent_kafka import Producer
from faker import Faker
from schemas import TransactionCategory, TransactionEvent

fake = Faker()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "financial.transactions")
RATE_PER_SECOND = float(os.getenv("PRODUCER_RATE_PER_SECOND", "5"))

MERCHANTS = [
    ("Whole Foods Market", TransactionCategory.FOOD),
    ("Uber", TransactionCategory.TRANSPORT),
    ("Netflix", TransactionCategory.ENTERTAINMENT),
    ("CVS Pharmacy", TransactionCategory.HEALTHCARE),
    ("Amazon", TransactionCategory.RETAIL),
    ("Con Edison", TransactionCategory.UTILITIES),
    ("Delta Airlines", TransactionCategory.TRAVEL),
    ("Starbucks", TransactionCategory.FOOD),
    ("Lyft", TransactionCategory.TRANSPORT),
    ("Spotify", TransactionCategory.ENTERTAINMENT),
]

USERS = [f"user_{i:04d}" for i in range(1, 51)]


def delivery_report(err, msg):
    if err:
        print(f"[producer] delivery failed: {err}")


def build_event() -> TransactionEvent:
    merchant, category = random.choice(MERCHANTS)
    return TransactionEvent(
        transaction_id=uuid.uuid4(),
        user_id=random.choice(USERS),
        merchant=merchant,
        category=category,
        amount=Decimal(str(round(random.uniform(1.0, 2500.0), 2))),
        currency="USD",
        timestamp=datetime.now(timezone.utc),
    )


def main():
    producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})
    interval = 1.0 / RATE_PER_SECOND
    print(f"[producer] sending to {KAFKA_TOPIC} at {RATE_PER_SECOND} msg/s")

    try:
        while True:
            event = build_event()
            payload = event.model_dump_json().encode("utf-8")
            producer.produce(
                KAFKA_TOPIC,
                key=event.user_id.encode("utf-8"),
                value=payload,
                callback=delivery_report,
            )
            producer.poll(0)
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        producer.flush()
        print("[producer] flushed and exiting")


if __name__ == "__main__":
    main()

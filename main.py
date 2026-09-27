

import sqlite3
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


DATABASE = Path(__file__).with_name("cardguard.db")

app = FastAPI(
    title="CardGuard API",
    description="A fictional credit card transaction risk analysis service.",
    version="0.2.0",
)


class Transaction(BaseModel):
    card_id: str = Field(min_length=1)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    merchant: str = Field(min_length=1)
    country: str = Field(min_length=2, max_length=2)


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT NOT NULL,
                amount_cents INTEGER NOT NULL,
                merchant TEXT NOT NULL,
                country TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                reasons TEXT NOT NULL
            )
        """)


initialize_database()


def evaluate_risk(transaction: Transaction, previous: list, now: datetime):
    reasons = []

    # Rule 1: High transaction amount
    if transaction.amount >= 2000:
        reasons.append("High transaction amount")

    # Rule 2: Three or more transactions within ten minutes
    ten_minutes_ago = now - timedelta(minutes=10)

    recent = [
        row for row in previous
        if datetime.fromisoformat(row["timestamp"]) >= ten_minutes_ago
    ]

    if len(recent) >= 2:
        reasons.append("Multiple transactions within ten minutes")

    # Rule 3: Country change within thirty minutes
    thirty_minutes_ago = now - timedelta(minutes=30)

    for row in previous:
        previous_time = datetime.fromisoformat(row["timestamp"])

        if (
            previous_time >= thirty_minutes_ago
            and row["country"] != transaction.country.upper()
        ):
            reasons.append("Rapid change in transaction country")
            break

    return {
        "risk_level": "review" if reasons else "low",
        "reasons": reasons,
    }


def format_transaction(row):
    return {
        "id": row["id"],
        "card_id": row["card_id"],
        "amount": row["amount_cents"] / 100,
        "merchant": row["merchant"],
        "country": row["country"],
        "timestamp": row["timestamp"],
        "risk_level": row["risk_level"],
        "reasons": row["reasons"].split("|") if row["reasons"] else [],
    }


@app.get("/")
def home():
    return {"message": "CardGuard API is running"}


@app.post("/transactions", status_code=201)
def create_transaction(transaction: Transaction):
    now = datetime.now(timezone.utc)

    with get_connection() as connection:
        previous = connection.execute(
            """
            SELECT * FROM transactions
            WHERE card_id = ?
            ORDER BY timestamp DESC
            """,
            (transaction.card_id,),
        ).fetchall()

        risk = evaluate_risk(transaction, previous, now)

        amount_cents = int(transaction.amount * 100)

        cursor = connection.execute(
            """
            INSERT INTO transactions (
                card_id, amount_cents, merchant, country,
                timestamp, risk_level, reasons
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction.card_id,
                amount_cents,
                transaction.merchant,
                transaction.country.upper(),
                now.isoformat(),
                risk["risk_level"],
                "|".join(risk["reasons"]),
            ),
        )

        transaction_id = cursor.lastrowid

        saved = connection.execute(
            "SELECT * FROM transactions WHERE id = ?",
            (transaction_id,),
        ).fetchone()

    return format_transaction(saved)


@app.get("/transactions")
def list_transactions(card_id: str | None = None):
    with get_connection() as connection:
        if card_id:
            rows = connection.execute(
                """
                SELECT * FROM transactions
                WHERE card_id = ?
                ORDER BY id DESC
                """,
                (card_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM transactions ORDER BY id DESC"
            ).fetchall()

    return [format_transaction(row) for row in rows]


@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: int):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM transactions WHERE id = ?",
            (transaction_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return format_transaction(row)
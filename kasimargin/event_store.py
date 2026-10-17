"""Private, local event storage for a single operator-entered trading day.

This module deliberately records only the operator's entries.  It does not
verify a bank, settle a card payment, or turn recorded sales into cash.
"""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import sqlite3
from contextlib import contextmanager

from .engine import ContractError, exact_keys, instant, money
from .jsonio import dumps

MAX_BROWSER_CENTS = 9_007_199_254_740_991
SOURCE_KIND = "OPERATOR_REPORTED"


class IdempotencyConflict(ContractError):
    pass


class EventStore:
    def __init__(self, database):
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self._open() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS ledger_events (
                    id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    request_digest TEXT NOT NULL,
                    business_day TEXT NOT NULL,
                    event_type TEXT NOT NULL CHECK(event_type IN ('sale', 'expense')),
                    payment_method TEXT NOT NULL CHECK(payment_method IN ('cash', 'card')),
                    amount_cents INTEGER NOT NULL,
                    occurred_at TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    replaces_id TEXT UNIQUE REFERENCES ledger_events(id),
                    correction_reason TEXT,
                    is_current INTEGER NOT NULL CHECK(is_current IN (0, 1))
                );
                CREATE INDEX IF NOT EXISTS ledger_events_day_current
                    ON ledger_events(business_day, is_current, occurred_at, id);
            """)

    def _connect(self):
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _open(self):
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _digest(value):
        return sha256(dumps(value).encode("utf-8")).hexdigest()

    @staticmethod
    def _day(value):
        if not isinstance(value, str) or len(value) != 10:
            raise ContractError("business_day must be an ISO date")
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ContractError("business_day must be an ISO date") from exc
        return value

    @staticmethod
    def _identifier(value, name):
        if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 128:
            raise ContractError(f"{name} must be a trimmed non-empty string up to 128 characters")
        return value

    @staticmethod
    def _amount(value):
        amount = money(value, "amount_cents")
        if amount is None or amount > MAX_BROWSER_CENTS:
            raise ContractError("amount_cents must be an exact browser-safe non-negative integer")
        return amount

    @staticmethod
    def _row(row):
        return {key: row[key] for key in row.keys()}

    def _known_retry(self, connection, key, digest):
        row = connection.execute("SELECT * FROM ledger_events WHERE idempotency_key = ?", (key,)).fetchone()
        if row is None:
            return None
        if row["request_digest"] != digest:
            raise IdempotencyConflict("idempotency key was already used with different content")
        result = self._row(row)
        result["idempotent_replay"] = True
        return result

    def append(self, value):
        exact_keys(value, {"id", "idempotency_key", "business_day", "event_type", "payment_method", "amount_cents", "occurred_at", "source_kind"}, "ledger event")
        event_id = self._identifier(value["id"], "event id")
        key = self._identifier(value["idempotency_key"], "idempotency key")
        business_day = self._day(value["business_day"])
        event_type, payment_method = value["event_type"], value["payment_method"]
        if event_type not in ("sale", "expense"):
            raise ContractError("event_type must be sale or expense")
        if payment_method not in ("cash", "card") or (event_type == "expense" and payment_method != "cash"):
            raise ContractError("only cash/card sales and cash expenses are supported")
        if value["source_kind"] != SOURCE_KIND:
            raise ContractError("source_kind must be OPERATOR_REPORTED")
        amount = self._amount(value["amount_cents"])
        occurred_at = instant(value["occurred_at"], "occurred_at").isoformat()
        digest = self._digest(value)
        recorded_at = datetime.now(timezone.utc).isoformat()
        try:
            with self._open() as connection:
                connection.execute("BEGIN IMMEDIATE")
                retry = self._known_retry(connection, key, digest)
                if retry is not None:
                    connection.commit()
                    return retry
                connection.execute("""INSERT INTO ledger_events
                    (id, idempotency_key, request_digest, business_day, event_type, payment_method, amount_cents,
                     occurred_at, recorded_at, source_kind, revision, replaces_id, correction_reason, is_current)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, NULL, NULL, 1)""",
                    (event_id, key, digest, business_day, event_type, payment_method, amount, occurred_at, recorded_at, SOURCE_KIND))
                row = connection.execute("SELECT * FROM ledger_events WHERE id = ?", (event_id,)).fetchone()
                connection.commit()
                result = self._row(row)
                result["idempotent_replay"] = False
                return result
        except sqlite3.IntegrityError as exc:
            raise ContractError("event could not be saved") from exc

    def correct(self, value):
        exact_keys(value, {"id", "idempotency_key", "replaces_id", "expected_revision", "amount_cents", "occurred_at", "reason"}, "event correction")
        event_id = self._identifier(value["id"], "event id")
        key = self._identifier(value["idempotency_key"], "idempotency key")
        replaces_id = self._identifier(value["replaces_id"], "replaces_id")
        if type(value["expected_revision"]) is not int or value["expected_revision"] < 1:
            raise ContractError("expected_revision must be a positive integer")
        if value["reason"] is not None and (not isinstance(value["reason"], str) or len(value["reason"]) > 280):
            raise ContractError("reason must be null or a short string")
        amount = self._amount(value["amount_cents"])
        occurred_at = instant(value["occurred_at"], "occurred_at").isoformat()
        digest = self._digest(value)
        recorded_at = datetime.now(timezone.utc).isoformat()
        try:
            with self._open() as connection:
                connection.execute("BEGIN IMMEDIATE")
                retry = self._known_retry(connection, key, digest)
                if retry is not None:
                    connection.commit()
                    return retry
                previous = connection.execute("SELECT * FROM ledger_events WHERE id = ? AND is_current = 1", (replaces_id,)).fetchone()
                if previous is None or previous["revision"] != value["expected_revision"]:
                    raise IdempotencyConflict("event is not current at the expected revision")
                connection.execute("UPDATE ledger_events SET is_current = 0 WHERE id = ?", (replaces_id,))
                connection.execute("""INSERT INTO ledger_events
                    (id, idempotency_key, request_digest, business_day, event_type, payment_method, amount_cents,
                     occurred_at, recorded_at, source_kind, revision, replaces_id, correction_reason, is_current)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                    (event_id, key, digest, previous["business_day"], previous["event_type"], previous["payment_method"], amount,
                     occurred_at, recorded_at, SOURCE_KIND, previous["revision"] + 1, replaces_id, value["reason"]))
                row = connection.execute("SELECT * FROM ledger_events WHERE id = ?", (event_id,)).fetchone()
                connection.commit()
                result = self._row(row)
                result["idempotent_replay"] = False
                return result
        except sqlite3.IntegrityError as exc:
            raise ContractError("event correction could not be saved") from exc

    def current_day(self, business_day):
        day = self._day(business_day)
        with self._open() as connection:
            rows = [self._row(row) for row in connection.execute(
                "SELECT * FROM ledger_events WHERE business_day = ? AND is_current = 1 ORDER BY occurred_at, id", (day,))]
        totals = {"recorded_sales_cents": 0, "cash_sales_cents": 0, "card_sales_cents": 0, "cash_expenses_cents": 0}
        for row in rows:
            if row["event_type"] == "sale":
                totals["recorded_sales_cents"] += row["amount_cents"]
                totals[f"{row['payment_method']}_sales_cents"] += row["amount_cents"]
            else:
                totals["cash_expenses_cents"] += row["amount_cents"]
        return {"business_day": day, "events": rows, **totals, "record_count": len(rows),
                "record_status": "OPERATOR_REPORTED_RECORDS_MAY_BE_INCOMPLETE",
                "cash_position_status": "NOT_PREPARED"}

    def history(self, event_id):
        current = self._identifier(event_id, "event id")
        with self._open() as connection:
            row = connection.execute("SELECT * FROM ledger_events WHERE id = ?", (current,)).fetchone()
            if row is None:
                raise ContractError("event was not found")
            root = row["id"]
            while row["replaces_id"] is not None:
                root = row["replaces_id"]
                row = connection.execute("SELECT * FROM ledger_events WHERE id = ?", (root,)).fetchone()
            rows = [self._row(row)]
            while True:
                next_row = connection.execute("SELECT * FROM ledger_events WHERE replaces_id = ?", (rows[-1]["id"],)).fetchone()
                if next_row is None:
                    return rows
                rows.append(self._row(next_row))

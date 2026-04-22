"""
End-to-end test for calibrator.check_resolutions after the condition_ids fix.

Inserts a synthetic V2 trade referencing a known-resolved market with a
specific classification, runs check_resolutions(), verifies a calibration
row was written, then cleans up.

Run from repo root:
    python scripts/test_calibrator.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backtest import fetch_resolved_markets
from logger import DB_PATH
from calibrator import check_resolutions

TEST_MARKER = "__test_calibrator_fixture__"


def pick_resolved_market() -> tuple[str, float]:
    for m in fetch_resolved_markets(limit=10):
        if m.get("condition_id") and m.get("resolved_yes_price") is not None:
            return m["condition_id"], float(m["resolved_yes_price"])
    raise RuntimeError("No resolved markets returned")


def insert_test_trade(condition_id: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    # Trade: side=YES, classification=bullish, entry market_price=0.30
    # If resolved YES-price > 0.30, actual_direction=bullish → correct=True
    cur = conn.execute(
        """INSERT INTO trades
           (market_question, market_id, side, amount_usd, edge, claude_score,
            market_price, reasoning, headlines, status, classification,
            materiality, news_source)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (TEST_MARKER, condition_id, "YES", 5.0, 0.5, 0.80, 0.30,
         "fixture", "fixture", "dry_run", "bullish", 0.75, "manual-test"),
    )
    trade_id = cur.lastrowid
    conn.commit()
    conn.close()
    return trade_id


def read_calibration(trade_id: int) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM calibration WHERE trade_id = ?", (trade_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def cleanup(trade_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM calibration WHERE trade_id = ?", (trade_id,))
    conn.execute("DELETE FROM trades WHERE id = ?", (trade_id,))
    conn.commit()
    conn.close()


def main() -> int:
    print("→ Fetching a resolved market...")
    condition_id, resolved_price = pick_resolved_market()
    print(f"  condition_id={condition_id}  resolved_price={resolved_price}")

    print("→ Inserting synthetic V2 trade (YES, bullish, entry=0.30)...")
    trade_id = insert_test_trade(condition_id)
    print(f"  trade_id={trade_id}")

    print("→ Running calibrator.check_resolutions()...")
    n = check_resolutions()
    print(f"  resolved {n} trades")

    print("→ Reading back calibration row...")
    row = read_calibration(trade_id)

    if row is None:
        cleanup(trade_id)
        print("\nFAIL: no calibration row written")
        return 1

    print(f"  entry_price       = {row.get('entry_price')}")
    print(f"  exit_price        = {row.get('exit_price')}")
    print(f"  actual_direction  = {row.get('actual_direction')}")
    print(f"  classification    = {row.get('classification')}")
    print(f"  correct           = {row.get('correct')}")

    cleanup(trade_id)
    print("→ Cleaned up test fixtures")

    expected_dir = "bullish" if resolved_price > 0.30 else ("bearish" if resolved_price < 0.30 else "neutral")
    expected_correct = 1 if expected_dir == "bullish" else 0

    if abs(float(row["exit_price"]) - resolved_price) > 1e-6:
        print(f"\nFAIL: exit_price mismatch. expected={resolved_price} got={row['exit_price']}")
        return 1
    if row["actual_direction"] != expected_dir:
        print(f"\nFAIL: actual_direction mismatch. expected={expected_dir} got={row['actual_direction']}")
        return 1
    if int(row["correct"]) != expected_correct:
        print(f"\nFAIL: correct mismatch. expected={expected_correct} got={row['correct']}")
        return 1

    print(f"\nPASS: calibration row written with correct fields")
    return 0


if __name__ == "__main__":
    sys.exit(main())

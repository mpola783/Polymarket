"""
End-to-end test for PaperPortfolio resolution flow.

Picks a real resolved market from Gamma API, inserts a synthetic open
ledger entry referencing it, runs PaperPortfolio._check_once(), then
verifies resolved_price + pnl_hypothetical were populated. Cleans up
the test entry afterwards.

Run from repo root:
    python scripts/test_paper_portfolio.py
"""
from __future__ import annotations

import asyncio
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backtest import fetch_resolved_markets
from logger import DB_PATH
from market_watcher import MarketWatcher, SignalLedger, PaperPortfolio, LedgerEntry

TEST_SIGNAL_ID = "test-paper-portfolio-001"


def pick_resolved_market() -> tuple[str, str, float]:
    markets = fetch_resolved_markets(limit=10)
    for m in markets:
        if m.get("condition_id") and m.get("resolved_yes_price") is not None:
            return m["condition_id"], m["question"], float(m["resolved_yes_price"])
    raise RuntimeError("No resolved markets returned from Gamma API")


def insert_test_entry(condition_id: str, question: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM signal_ledger WHERE signal_id = ?", (TEST_SIGNAL_ID,))
    conn.execute(
        """INSERT INTO signal_ledger
           (signal_id, market_id, market_question, side, classification,
            materiality, entry_price, headline, source, fired_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            TEST_SIGNAL_ID,
            condition_id,
            question,
            "YES",
            "bullish",
            0.75,
            0.30,
            "synthetic test headline",
            "manual-test",
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def read_entry() -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM signal_ledger WHERE signal_id = ?", (TEST_SIGNAL_ID,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def cleanup() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM signal_ledger WHERE signal_id = ?", (TEST_SIGNAL_ID,))
    conn.commit()
    conn.close()


async def run_one_resolution_pass() -> None:
    watcher = MarketWatcher()
    ledger = SignalLedger(watcher)
    # Hydrate in-memory ledger from DB so our seeded entry is visible to PaperPortfolio
    import logger as logger_mod
    for row in logger_mod.get_ledger_entries(limit=500):
        if row.get("resolved_price") is not None:
            continue
        entry = LedgerEntry(
            signal_id=row["signal_id"],
            market_id=row["market_id"],
            market_question=row["market_question"],
            side=row["side"],
            classification=row.get("classification"),
            materiality=row.get("materiality"),
            entry_price=row["entry_price"],
            headline=row.get("headline"),
            source=row.get("source"),
            fired_at=datetime.fromisoformat(row["fired_at"]),
        )
        ledger.entries[entry.signal_id] = entry

    portfolio = PaperPortfolio(ledger)
    await portfolio._check_once()


def main() -> int:
    print("→ Fetching a resolved market to use as a test target...")
    condition_id, question, expected_price = pick_resolved_market()
    print(f"  picked: {question[:60]}")
    print(f"  condition_id={condition_id}  resolved_yes_price={expected_price}")

    print("→ Inserting synthetic open ledger entry (side=YES, entry=0.30)...")
    insert_test_entry(condition_id, question)

    print("→ Running PaperPortfolio._check_once()...")
    asyncio.run(run_one_resolution_pass())

    print("→ Reading back signal_ledger row...")
    row = read_entry()
    if row is None:
        print("  FAIL: test row disappeared")
        return 1

    resolved = row.get("resolved_price")
    pnl = row.get("pnl_hypothetical")

    print(f"  resolved_price     = {resolved}")
    print(f"  pnl_hypothetical   = {pnl}")

    cleanup()
    print("→ Cleaned up test entry")

    if resolved is None or pnl is None:
        print("\nFAIL: PaperPortfolio did not populate resolution fields")
        return 1

    expected_pnl = resolved - 0.30  # YES side, entry_price=0.30
    if abs(pnl - expected_pnl) > 1e-6:
        print(f"\nFAIL: PnL mismatch. expected={expected_pnl:+.4f} got={pnl:+.4f}")
        return 1

    print(f"\nPASS: resolution populated, PnL formula correct ({pnl:+.4f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

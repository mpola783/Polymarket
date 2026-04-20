"""
Polymarket WebSocket subscriber — live price feed + niche market filtering.
Maintains a live snapshot of tracked markets and detects momentum shifts.
"""
from __future__ import annotations

import asyncio
import json
import time
import logging
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import httpx

import config
import logger
from markets import Market, fetch_active_markets, filter_by_categories, GAMMA_API

if TYPE_CHECKING:
    from edge import Signal

log = logging.getLogger(__name__)


@dataclass
class MarketSnapshot:
    market: Market
    last_price: float
    prev_price: float
    last_update: datetime
    momentum: float = 0.0  # price change per minute

    @property
    def price_change(self) -> float:
        return self.last_price - self.prev_price


@dataclass
class LedgerEntry:
    signal_id: str
    market_id: str
    market_question: str
    side: str
    classification: str | None
    materiality: float | None
    entry_price: float
    headline: str | None
    source: str | None
    fired_at: datetime
    price_5m: float | None = None
    price_1h: float | None = None
    price_6h: float | None = None
    resolved_price: float | None = None
    pnl_hypothetical: float | None = None


class MarketWatcher:
    """Watches niche Polymarket markets via WebSocket + periodic Gamma API refresh."""

    def __init__(self):
        self.snapshots: dict[str, MarketSnapshot] = {}
        self.tracked_markets: list[Market] = []
        self._refresh_interval = 300  # refresh market list every 5 min
        self._ws_connected = False
        self.stats = {
            "ws_messages": 0,
            "price_updates": 0,
            "market_refreshes": 0,
        }

    def get_niche_markets(self, markets: list[Market]) -> list[Market]:
        """Filter to niche markets within volume bounds."""
        return [
            m for m in markets
            if config.MIN_VOLUME_USD <= m.volume <= config.MAX_VOLUME_USD
            and m.active
        ]

    async def refresh_markets(self):
        """Fetch and filter markets from Gamma API."""
        try:
            all_markets = await asyncio.get_event_loop().run_in_executor(
                None, lambda: fetch_active_markets(limit=200)
            )
            categorized = filter_by_categories(all_markets)
            self.tracked_markets = self.get_niche_markets(categorized)

            # Update snapshots
            now = datetime.now(timezone.utc)
            existing_ids = set(self.snapshots.keys())
            new_ids = set()

            for m in self.tracked_markets:
                new_ids.add(m.condition_id)
                if m.condition_id not in self.snapshots:
                    self.snapshots[m.condition_id] = MarketSnapshot(
                        market=m,
                        last_price=m.yes_price,
                        prev_price=m.yes_price,
                        last_update=now,
                    )
                else:
                    snap = self.snapshots[m.condition_id]
                    snap.market = m  # update metadata

            # Remove stale snapshots
            for stale_id in existing_ids - new_ids:
                del self.snapshots[stale_id]

            self.stats["market_refreshes"] += 1
            log.info(f"[watcher] Tracking {len(self.tracked_markets)} niche markets")

        except Exception as e:
            log.warning(f"[watcher] Market refresh error: {e}")

    async def _connect_websocket(self):
        """Connect to Polymarket WebSocket for live price updates."""
        try:
            import websockets
        except ImportError:
            log.warning("[watcher] websockets not installed — using polling fallback")
            return

        while True:
            try:
                async with websockets.connect(config.POLYMARKET_WS_HOST) as ws:
                    self._ws_connected = True
                    log.info("[watcher] WebSocket connected")

                    # Subscribe to tracked markets
                    for market in self.tracked_markets:
                        for token in market.tokens:
                            tid = token.get("token_id")
                            if tid:
                                sub = {"type": "subscribe", "channel": "price", "market": tid}
                                await ws.send(json.dumps(sub))

                    # Listen for updates
                    while True:
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=10)
                            self.stats["ws_messages"] += 1
                            data = json.loads(msg)
                            self._handle_ws_message(data)
                        except asyncio.TimeoutError:
                            # Send ping
                            await ws.ping()

            except Exception as e:
                self._ws_connected = False
                log.warning(f"[watcher] WebSocket error: {e}, reconnecting in 5s")
                await asyncio.sleep(5)

    def _handle_ws_message(self, data: dict):
        """Process a WebSocket price update."""
        msg_type = data.get("type", "")
        if msg_type not in ("price_change", "last_trade_price"):
            return

        market_id = data.get("market", data.get("condition_id", ""))
        price = data.get("price")

        if not market_id or price is None:
            return

        # Find matching snapshot
        for cid, snap in self.snapshots.items():
            token_ids = [t.get("token_id", "") for t in snap.market.tokens]
            if market_id in token_ids or market_id == cid:
                now = datetime.now(timezone.utc)
                elapsed = (now - snap.last_update).total_seconds()
                snap.prev_price = snap.last_price
                snap.last_price = float(price)
                snap.last_update = now
                if elapsed > 0:
                    snap.momentum = (snap.last_price - snap.prev_price) / (elapsed / 60)
                self.stats["price_updates"] += 1
                break

    async def _polling_fallback(self):
        """Poll Gamma API for price updates when WebSocket unavailable."""
        while True:
            await asyncio.sleep(30)
            if self._ws_connected:
                continue
            await self.refresh_markets()

    async def run(self):
        """Start the market watcher — refresh + WebSocket + polling fallback."""
        await self.refresh_markets()

        async def refresh_loop():
            while True:
                await asyncio.sleep(self._refresh_interval)
                await self.refresh_markets()

        await asyncio.gather(
            refresh_loop(),
            self._connect_websocket(),
            self._polling_fallback(),
            return_exceptions=True,
        )

    def get_market_by_question(self, question_fragment: str) -> Market | None:
        """Find a tracked market by partial question match."""
        frag = question_fragment.lower()
        for m in self.tracked_markets:
            if frag in m.question.lower():
                return m
        return None

    def get_snapshot(self, condition_id: str) -> MarketSnapshot | None:
        return self.snapshots.get(condition_id)


class SignalLedger:
    """Records every signal at fire time and schedules price checkpoints."""

    def __init__(self, market_watcher: MarketWatcher) -> None:
        self._watcher = market_watcher
        self.entries: dict[str, LedgerEntry] = {}
        self._tasks: set[asyncio.Task] = set()  # prevent GC of long-running tasks

    def add(self, signal: Signal) -> LedgerEntry:
        signal_id = str(uuid.uuid4())
        entry = LedgerEntry(
            signal_id=signal_id,
            market_id=signal.market.condition_id,
            market_question=signal.market.question,
            side=signal.side,
            classification=signal.classification or None,
            materiality=signal.materiality if signal.materiality else None,
            entry_price=signal.market_price,
            headline=signal.headlines or None,
            source=signal.news_source or None,
            fired_at=datetime.now(timezone.utc),
        )
        self.entries[signal_id] = entry
        try:
            logger.log_ledger_entry(entry)
        except Exception as e:
            log.warning(f"[ledger] DB write failed for {signal_id[:8]}: {e}")

        try:
            asyncio.get_running_loop()
            for label, delay in config.CHECKPOINT_DELAYS.items():
                task = asyncio.create_task(
                    self._schedule_checkpoint(entry, f"price_{label}", delay)
                )
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)
        except RuntimeError:
            log.warning(f"[ledger] No event loop — checkpoint tasks not scheduled for {signal_id[:8]}")

        return entry

    async def _schedule_checkpoint(
        self, entry: LedgerEntry, label: str, delay_seconds: int
    ) -> None:
        await asyncio.sleep(delay_seconds)
        loop = asyncio.get_running_loop()
        price = await loop.run_in_executor(None, self._read_price, entry.market_id)
        if price is None:
            log.warning(f"[ledger] {label} price unavailable for {entry.signal_id[:8]}, skipping")
            return
        setattr(entry, label, price)
        try:
            await loop.run_in_executor(
                None, logger.update_ledger_checkpoint, entry.signal_id, label, price
            )
        except Exception as e:
            log.warning(f"[ledger] DB checkpoint update failed {label}/{entry.signal_id[:8]}: {e}")
        log.info(f"[ledger] {label}={price:.3f} for \"{entry.market_question[:40]}\" ({entry.signal_id[:8]})")

    def _read_price(self, market_id: str) -> float | None:
        snap = self._watcher.get_snapshot(market_id)
        if snap is not None:
            return snap.last_price
        return self._fetch_gamma_price(market_id)

    def _fetch_gamma_price(self, market_id: str) -> float | None:
        try:
            resp = httpx.get(
                f"{GAMMA_API}/markets",
                params={"conditionId": market_id},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data if isinstance(data, list) else data.get("data", [])
            if not items:
                return None
            prices = items[0].get("outcomePrices", "")
            if prices:
                parsed = json.loads(prices) if isinstance(prices, str) else prices
                if parsed:
                    return float(parsed[0])
        except Exception as e:
            log.warning(f"[ledger] Gamma fallback failed for {market_id}: {e}")
        return None

    def get_open_entries(self) -> list[LedgerEntry]:
        return [e for e in self.entries.values() if e.resolved_price is None]


if __name__ == "__main__":
    async def _test():
        watcher = MarketWatcher()
        await watcher.refresh_markets()
        print(f"Tracking {len(watcher.tracked_markets)} niche markets:")
        for m in watcher.tracked_markets[:10]:
            print(f"  [{m.category}] ${m.volume:,.0f} | YES:{m.yes_price:.2f} | {m.question[:60]}")

    asyncio.run(_test())

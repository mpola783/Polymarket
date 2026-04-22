# Polymarket Pipeline V2 — Project Context

## Overview
An AI-powered prediction market trading pipeline. Ingests real-time news (RSS, Twitter, Telegram),
classifies headlines as bullish/bearish/neutral against active Polymarket markets using Claude,
detects edge via materiality scoring, and executes trades (dry-run by default).

**Current focus:** Improving `market_watcher.py` observability, paper trading tracking,
and replacing paid news APIs with free high-signal RSS sources to minimize API costs.

---

## Architecture

```
news_stream.py      → Real-time news ingestion (Twitter, Telegram, RSS fallback)
market_watcher.py   → Polymarket WebSocket + price snapshots + niche market filter
matcher.py          → Routes headlines to relevant markets (keyword overlap)
classifier.py       → Claude classification: bullish / bearish / neutral + materiality
edge.py             → Edge detection + quarter-Kelly position sizing
executor.py         → Trade execution (dry-run or live CLOB)
pipeline.py         → V1 (sync loop) and V2 (async event-driven) orchestrators
dashboard.py        → Bloomberg-style Rich terminal dashboard
backtest.py         → Historical replay against resolved markets
calibrator.py       → Tracks classification accuracy as markets resolve
logger.py           → SQLite persistence (trades, news events, calibration, latency)
config.py           → All settings, API keys, thresholds
cli.py              → Unified CLI entry point
```

---

## Key Design Decisions

### V2 Classification Strategy
Claude is asked **"bullish / bearish / neutral?"** — NOT "what's the probability?"
This is a classification task LLMs are genuinely good at. Materiality (0–1) rates impact strength.

### Niche Market Filter
Only trade markets with **$1K–$500K volume**. High-volume markets are dominated by sophisticated bots.
Niche markets have slower, less-informed crowds — that's where edge exists.

### Token Cost Minimization
- `CLASSIFICATION_MODEL = "claude-haiku-4-5-20251001"` for high-frequency classification
- `SCORING_MODEL = "claude-sonnet-4-6-20250514"` for deeper V1 scoring only
- Pre-filter headlines with keyword heuristics BEFORE calling Claude
- Use a local seen-cache to deduplicate — never classify the same headline twice

### Safety
- `DRY_RUN=true` by default — never trades real money without explicit `--live` flag
- `MAX_BET_USD=25`, `DAILY_LOSS_LIMIT_USD=100`
- Quarter-Kelly sizing: `fraction = edge * 0.25`

---

## File Structure
```
polymarket-pipeline/
├── CLAUDE.md               ← you are here
├── .env                    ← API keys (never commit)
├── .env.example            ← template
├── .claudeignore           ← excludes trades.db, .venv, __pycache__
├── requirements.txt
├── setup.sh
├── cli.py                  ← main entry point
├── config.py
├── pipeline.py             ← V1 + V2 orchestrators
├── market_watcher.py       ← [ACTIVE DEVELOPMENT] signal ledger + paper portfolio
├── news_stream.py          ← [ACTIVE DEVELOPMENT] RSS optimization
├── classifier.py
├── matcher.py
├── edge.py
├── executor.py
├── scorer.py
├── backtest.py
├── calibrator.py
├── logger.py               ← SQLite schema owner
├── dashboard.py
└── trades.db               ← SQLite DB (git-ignored)
```

---

## Environment Variables (`.env`)
```
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional — real-time news (being replaced with free RSS)
TWITTER_BEARER_TOKEN=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHANNEL_IDS=...

# Optional — live trading only
POLYMARKET_API_KEY=...
POLYMARKET_API_SECRET=...
POLYMARKET_API_PASSPHRASE=...
POLYMARKET_PRIVATE_KEY=...

# Pipeline tuning
DRY_RUN=true
MAX_BET_USD=25
DAILY_LOSS_LIMIT_USD=100
EDGE_THRESHOLD=0.10
MAX_VOLUME_USD=500000
MIN_VOLUME_USD=1000
MATERIALITY_THRESHOLD=0.6
SPEED_TARGET_SECONDS=5
```

---

## Common Commands
```bash
# Activate venv first
source .venv/bin/activate

# Run real-time pipeline (dry-run)
python cli.py watch

# Run with live trading
python cli.py watch --live

# Launch terminal dashboard
python cli.py dashboard

# Backtest against resolved markets
python cli.py backtest --limit 30

# Check classification accuracy
python cli.py calibrate

# Browse niche markets
python cli.py niche

# Verify all API connections
python cli.py verify

# View trade log
python cli.py trades --limit 50

# View stats + latency
python cli.py stats
```

---

## SQLite Schema (trades.db)
Managed by `logger.py`. Tables:
- `trades` — every signal logged, including dry-runs. V2 columns: news_source, classification,
  materiality, news_latency_ms, classification_latency_ms, total_latency_ms
- `news_events` — every headline processed, matched_markets, triggered_trades
- `pipeline_runs` — run metadata (V1)
- `outcomes` — resolved trade results (for PnL calculation)
- `calibration` — classification accuracy tracking (correct/incorrect per resolved market)

---

## Active Development Priorities

### 1. `market_watcher.py` — Signal Ledger + Paper Portfolio
**Goal:** Track every would-be trade and measure what would have happened.
- Add `SignalLedger` dataclass: stores signal, entry price, headline, timestamp
- Add `PaperPortfolio`: polls Gamma API for price updates on open positions (every 30 min)
- Record hypothetical PnL as markets resolve
- Add momentum confirmation: only escalate if price moves in predicted direction within 5 min

### 2. `news_stream.py` — Free RSS Optimization
**Goal:** Replace paid Twitter/Telegram with free, high-signal RSS feeds.
- Generate RSS queries dynamically FROM active market questions (not static feeds)
- Add category-specific feeds: CoinTelegraph/The Block (crypto), Google News targeted queries (AI/politics)
- Add Hacker News Firebase API (free, real-time, good for tech/AI)
- Pre-filter with local heuristics before Claude API call (saves 60-70% of token spend)

### 3. Feedback Loop
**Goal:** Know if the classifier is actually right.
- Post-signal price tracking at +5min, +1hr, +6hr intervals
- Accuracy by news source and market category
- Auto-detect strategy degradation and alert

---

## Code Style & Conventions
- Python 3.9+ compatible
- Type hints on all function signatures (`from __future__ import annotations`)
- Dataclasses for structured data (Signal, Classification, MarketSnapshot, etc.)
- `logging` module for operational logs, `rich` Console for user-facing output
- All external API calls wrapped in try/except with graceful fallback
- Async-first for V2 pipeline components; sync wrappers provided for compatibility
- Config values always read from `config.py`, never hardcoded

---

## Dependencies
```
anthropic>=0.40.0       # Claude API
feedparser>=6.0.0       # RSS parsing
httpx>=0.27.0           # HTTP client (sync + async)
python-dotenv>=1.0.0    # .env loading
rich>=13.0.0            # Terminal UI
websockets>=12.0        # Polymarket WebSocket
tweepy>=4.14.0          # Twitter (being phased out)
aiohttp>=3.9.0          # Async HTTP
# py-clob-client        # Install separately for live trading
```

---

## Notes for Claude Code
- `trades.db` is a SQLite file — never edit it directly, always use `logger.py` functions
- `config.py` is the single source of truth for all thresholds and model names
- When adding new DB columns, add a migration in `logger._migrate_v2_columns()` pattern
- The `Signal` dataclass in `edge.py` is the contract between classifier → executor
- `PipelineV2` in `pipeline.py` is the production path; V1 is kept for backward compatibility
- Always test with `DRY_RUN=true` before touching executor live paths

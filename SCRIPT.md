# I Built a News Scraper That Places Polymarket Bets Automatically

## FORMAT
Short-form vertical (Reels/TikTok/Shorts) or IG story series. Screen recording of terminal + face cam or voiceover.

## TRIGGER WORD
PIPELINE

---

## HOOK (0-3 seconds)

**SHOW:** Dashboard running in Ghostty with transparency. Trades flowing. Green on black.

**SAY:**
"I built an AI that reads the news and places bets on Polymarket automatically."

---

## THE SYSTEM (3-15 seconds)

**SHOW:** Scroll through the terminal slowly. Point at specific panels.

**TALKING POINTS:**
- "Here's how it works. Five RSS feeds. TechCrunch, Reuters, Google News, Ars Technica, NYT."
- "Every few seconds it scrapes the latest headlines."
- "Then it pulls active prediction markets from Polymarket — real markets with real money."

**SHOW:** Market scanner panel — markets with prices visible.

---

## THE BRAIN (15-30 seconds)

**SHOW:** Scanner panel showing Claude scores vs market prices. Highlight a row where edge is detected.

**TALKING POINTS:**
- "Here's where it gets interesting. For each market, it sends the headlines to Claude."
- "Claude reads the news and says — 'I think there's a 78% chance this happens. The market says 62%.'"
- "That's a 16% edge. The system flags it and places a bet."
- "If Claude agrees with the market — no trade. It only bets when it sees something the market hasn't priced in yet."

---

## THE EDGE (30-40 seconds)

**SHOW:** A specific signal row. Point at the Claude score, market price, and edge percentage.

**TALKING POINTS:**
- "This isn't random. It's comparing an AI research pipeline against crowd consensus."
- "The market is everyone's average opinion. Claude is reading 30 headlines and forming its own."
- "When those two disagree by more than 10% — that's the trade."
- "Quarter-Kelly sizing. $25 max per bet. $100 daily limit. It's not gambling. It's a system."

---

## THE OUTPUT (40-50 seconds)

**SHOW:** Trade log panel. Scroll through trades — wins, losses, open positions.

**TALKING POINTS:**
- "Every trade is logged. Market question. Claude's score. Market price at time of bet. Edge. Side. Amount."
- "Full audit trail. You can see exactly why it made every decision."
- "Win rate sitting at [read from dashboard]. PnL [read from dashboard]."

---

## THE BUILD (50-60 seconds)

**SHOW:** Quick flash of the file structure in terminal. `ls` the project directory.

**TALKING POINTS:**
- "The whole thing is Python. About 900 lines across 10 files."
- "Scraper. Scorer. Edge detector. Executor. Logger. Dashboard."
- "Modular. Swap out the news sources. Change the scoring model. Adjust the threshold."
- "Took an afternoon to build."

---

## CTA (60-70 seconds)

**SHOW:** Dashboard running. Or cut to face cam.

**SAY:**
"I'm giving away the full pipeline. Every file. Setup guide. One command to install."

"DM me the word PIPELINE and I'll send you the repo."

---

## SCREEN RECORDING CHECKLIST

Before you hit record:

1. `cd ~/Desktop/PROJECTS/polymarket-pipeline`
2. `git checkout demo`
3. `source .venv/bin/activate`
4. `python cli.py dashboard --speed 5`
5. Wait 15-20 seconds for trades to build up
6. Start recording

Ghostty settings for maximum visual impact:
- Background opacity 0.3-0.5 (shows desktop blur)
- Terminal fills most of the screen
- No other windows visible

After recording:
- `git checkout main` (back to lead magnet branch)

---

## STORY SERIES VERSION (if splitting into slides)

**Slide 1 (Hook):** Dashboard screenshot. Text overlay: "I built an AI that bets on Polymarket automatically."

**Slide 2 (The Scraper):** "It scrapes 5 news sources every 60 seconds."

**Slide 3 (The Brain):** "Feeds the headlines to Claude. Gets a confidence score."

**Slide 4 (The Edge):** "Compares Claude's score against the market. When they disagree by 10%+ — it bets."

**Slide 5 (The Output):** Screenshot of trade log. "Every trade logged. Full audit trail."

**Slide 6 (CTA):** "DM me PIPELINE for the full repo + setup guide."

---

## OPTIONAL B-ROLL SHOTS

- Terminal scrolling with trades flowing
- Close-up of a specific signal being detected (green highlight)
- The `python cli.py verify` output showing all checks passing
- Split screen: news headline on left, trade being placed on right
- The PDF setup guide being opened

---

## CAPTION

I built a news scraper that places Polymarket bets automatically.

It scrapes 5 RSS feeds. Sends headlines to Claude. Gets a confidence score on every active prediction market.

When Claude's score diverges from the market price by 10%+ — it bets.

Quarter-Kelly sizing. $25 max. Full audit trail.

900 lines of Python. Took an afternoon.

DM me "PIPELINE" for the full repo + setup guide.

#ai #python #polymarket #predictionmarkets #claude #automation #trading #buildinpublic

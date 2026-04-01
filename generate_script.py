#!/usr/bin/env python3
"""Generate the Polymarket Pipeline Script PDF."""
from __future__ import annotations

from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab import rl_config

import os

# --- Colors ---
BLACK = HexColor("#0A0A0A")
GREEN = HexColor("#00FF41")
CYAN = HexColor("#00E5FF")
DARK_PANEL = HexColor("#111111")
WHITE = HexColor("#E0E0E0")
MUTED = HexColor("#777777")
YELLOW = HexColor("#FFD600")
DIM = HexColor("#444444")

W, H = letter


def draw_bg(c):
    c.setFillColor(BLACK)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def draw_panel(c, x, y, w, h):
    c.setFillColor(DARK_PANEL)
    c.setStrokeColor(HexColor("#1C3D1C"))
    c.setLineWidth(0.5)
    c.roundRect(x, y, w, h, 6, fill=1, stroke=1)


def text_wrap(c, x, y, txt, color=WHITE, size=11, font="Helvetica", max_width=490, line_height=16):
    c.setFillColor(color)
    c.setFont(font, size)
    words = txt.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if c.stringWidth(test, font, size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    for line in lines:
        if y < 60:
            c.showPage()
            draw_bg(c)
            y = H - 60
        c.setFillColor(color)
        c.setFont(font, size)
        c.drawString(x, y, line)
        y -= line_height
    return y


def section_header(c, y, label, timestamp):
    if y < 100:
        c.showPage()
        draw_bg(c)
        y = H - 60

    # Section line
    c.setStrokeColor(GREEN)
    c.setLineWidth(1)
    c.line(50, y + 8, W - 50, y + 8)

    y -= 8
    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, label)

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 10)
    c.drawRightString(W - 50, y, timestamp)

    y -= 25
    return y


def visual_cue(c, y, txt):
    if y < 60:
        c.showPage()
        draw_bg(c)
        y = H - 60

    c.setFillColor(CYAN)
    c.setFont("Helvetica-BoldOblique", 9)
    c.drawString(55, y, f"[SCREEN: {txt}]")
    y -= 18
    return y


def say_line(c, y, txt):
    y = text_wrap(c, 50, y, f'"{txt}"', color=WHITE, size=12, font="Helvetica", max_width=500, line_height=18)
    y -= 6
    return y


def build_pdf(output_path: str):
    c = canvas.Canvas(output_path, pagesize=letter)

    # ===================== COVER =====================
    draw_bg(c)

    c.setStrokeColor(GREEN)
    c.setLineWidth(2)
    c.line(50, H - 40, W - 50, H - 40)

    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(50, H - 110, "SCRIPT")

    c.setFillColor(WHITE)
    c.setFont("Helvetica", 13)
    c.drawString(50, H - 145, "I Built a News Scraper That Places")
    c.drawString(50, H - 163, "Polymarket Bets Automatically")

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 10)
    c.drawString(50, H - 200, "Format: Short-form vertical (Reels / TikTok / Shorts)")
    c.drawString(50, H - 216, "CTA: DM \"PIPELINE\" for the full repo + setup guide")

    c.setStrokeColor(DIM)
    c.setLineWidth(0.5)
    c.line(50, H - 240, W - 50, H - 240)

    # --- Table of contents ---
    y = H - 275
    sections = [
        ("HOOK", "0 - 3s"),
        ("THE SYSTEM", "3 - 15s"),
        ("THE BRAIN", "15 - 30s"),
        ("THE EDGE", "30 - 40s"),
        ("THE OUTPUT", "40 - 50s"),
        ("THE BUILD", "50 - 60s"),
        ("CTA", "60 - 70s"),
    ]

    for label, ts in sections:
        c.setFillColor(GREEN)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(60, y, label)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 11)
        c.drawRightString(250, y, ts)
        y -= 22

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(50, 35, "@brodyautomates")

    c.showPage()

    # ===================== SCRIPT PAGES =====================
    draw_bg(c)
    y = H - 60

    # --- HOOK ---
    y = section_header(c, y, "HOOK", "0 - 3 seconds")
    y = visual_cue(c, y, "Dashboard running in Ghostty. Trades flowing. Green on black.")
    y = say_line(c, y, "I built an AI that reads the news and places bets on Polymarket automatically.")

    y -= 15

    # --- THE SYSTEM ---
    y = section_header(c, y, "THE SYSTEM", "3 - 15 seconds")
    y = visual_cue(c, y, "Scroll through terminal slowly. Point at specific panels.")
    y = say_line(c, y, "Here's how it works. Five RSS feeds. TechCrunch, Reuters, Google News, Ars Technica, NYT.")
    y = say_line(c, y, "Every few seconds it scrapes the latest headlines.")
    y = visual_cue(c, y, "Market scanner panel — markets with prices visible.")
    y = say_line(c, y, "Then it pulls active prediction markets from Polymarket. Real markets with real money.")

    y -= 15

    # --- THE BRAIN ---
    y = section_header(c, y, "THE BRAIN", "15 - 30 seconds")
    y = visual_cue(c, y, "Scanner panel. Claude scores vs market prices. Highlight a row with edge.")
    y = say_line(c, y, "Here's where it gets interesting. For each market, it sends the headlines to Claude.")
    y = say_line(c, y, "Claude reads the news and says — I think there's a 78% chance this happens. The market says 62%.")
    y = say_line(c, y, "That's a 16% edge. The system flags it and places a bet.")
    y = say_line(c, y, "If Claude agrees with the market — no trade. It only bets when it sees something the market hasn't priced in yet.")

    y -= 15

    # --- THE EDGE ---
    y = section_header(c, y, "THE EDGE", "30 - 40 seconds")
    y = visual_cue(c, y, "Close-up on a specific signal row. Claude score, market price, edge %.")
    y = say_line(c, y, "This isn't random. It's comparing an AI research pipeline against crowd consensus.")
    y = say_line(c, y, "The market is everyone's average opinion. Claude is reading 30 headlines and forming its own.")
    y = say_line(c, y, "When those two disagree by more than 10% — that's the trade.")
    y = say_line(c, y, "Quarter-Kelly sizing. $25 max per bet. $100 daily limit. It's not gambling. It's a system.")

    y -= 15

    # --- THE OUTPUT ---
    y = section_header(c, y, "THE OUTPUT", "40 - 50 seconds")
    y = visual_cue(c, y, "Trade log panel. Scroll through trades — wins, losses, open positions.")
    y = say_line(c, y, "Every trade is logged. Market question. Claude's score. Market price at time of bet. Edge. Side. Amount.")
    y = say_line(c, y, "Full audit trail. You can see exactly why it made every decision.")
    y = say_line(c, y, "Win rate sitting at [read from dashboard]. PnL [read from dashboard].")

    y -= 15

    # --- THE BUILD ---
    y = section_header(c, y, "THE BUILD", "50 - 60 seconds")
    y = visual_cue(c, y, "Quick flash of file structure in terminal. ls the project directory.")
    y = say_line(c, y, "The whole thing is Python. About 900 lines across 10 files.")
    y = say_line(c, y, "Scraper. Scorer. Edge detector. Executor. Logger. Dashboard.")
    y = say_line(c, y, "Modular. Swap out the news sources. Change the scoring model. Adjust the threshold.")
    y = say_line(c, y, "Took an afternoon to build.")

    y -= 15

    # --- CTA ---
    y = section_header(c, y, "CTA", "60 - 70 seconds")
    y = visual_cue(c, y, "Dashboard running. Or cut to face cam.")
    y = say_line(c, y, "I'm giving away the full pipeline. Every file. Setup guide. One command to install.")
    y -= 5
    y = say_line(c, y, "DM me the word PIPELINE and I'll send you the repo.")

    # Footer
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(50, 35, "Polymarket Pipeline — Script")
    c.drawRightString(W - 50, 35, "@brodyautomates")

    c.save()


if __name__ == "__main__":
    repo = os.path.join(os.path.dirname(__file__), "SCRIPT.pdf")
    desktop = os.path.expanduser("~/Desktop/Polymarket_Pipeline_Script.pdf")

    build_pdf(repo)
    print(f"Generated: {repo}")
    build_pdf(desktop)
    print(f"Generated: {desktop}")

import yfinance as yf
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText

# =========================
# CONFIG
# =========================

WATCHLIST = {
    "NVDA": 3,
    "STM.PA": 4,
    "SOI.PA": 5,
    "ASML.AS": 3,
    "SU.PA": 3  # Schneider Electric
}

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

USE_EMAIL = EMAIL_USER is not None and EMAIL_PASS is not None

# =========================
# EMAIL
# =========================

def send_mail(subject, body):
    if not USE_EMAIL:
        print("[EMAIL DISABLED]")
        print(subject)
        print(body)
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

# =========================
# DATA
# =========================

def get_daily_move(ticker):
    try:
        data = yf.download(ticker, period="5d", interval="1d", progress=False)

        if data is None or len(data) < 2:
            print(f"{ticker} -> pas assez de data")
            return None

        prev = data["Close"].iloc[-2]
        last = data["Close"].iloc[-1]

        change = ((last - prev) / prev) * 100

        return float(change)

    except Exception as e:
        print(f"{ticker} erreur:", e)
        return None

# =========================
# MAIN
# =========================

print("=== BOT START ===")

for ticker, threshold in WATCHLIST.items():

    move = get_daily_move(ticker)

    if move is None:
        continue

    print(f"{ticker} : {move:.2f}%")

    if abs(move) >= threshold:

        direction = "HAUSSE" if move > 0 else "BAISSE"

        subject = f"[ALERTE] {ticker} {direction} {move:.2f}%"
        body = f"""
Ticker: {ticker}
Direction: {direction}
Variation: {move:.2f}%

Stratégie: momentum daily
"""

        send_mail(subject, body)

print("=== BOT END ===")

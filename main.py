import os
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from zoneinfo import ZoneInfo
import yfinance as yf

TICKERS = {
    "STMPA.PA": "STMicroelectronics",
    "AIR.PA": "Airbus",
    "HO.PA": "Thales",
    "CAP.PA": "Capgemini",
    "OR.PA": "L'Oréal",
    "MC.PA": "LVMH",
    "AI.PA": "Air Liquide",
    "SAF.PA": "Safran",
    "GLE.PA": "Société Générale",
    "SOI.PA": "Soitec",
    "EXA.PA": "Exail Technologies",
    "VLA.PA": "Valneva",
}

THRESHOLDS = {
    "STMPA.PA": 5,
    "SOI.PA": 5,
}

# Seuil pour la section "mouvement majeur" (alerte forte, sans recommandation)
MAJOR_MOVE_THRESHOLD = 10

RECAP_HOURS = [9, 18]

HISTORY_FILE = "history.csv"

EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_TO = os.environ["EMAIL_TO"]
EMAIL_PASS = os.environ["EMAIL_PASS"]


def is_market_hours():
    now_paris = datetime.now(ZoneInfo("Europe/Paris"))
    hour = now_paris.hour
    if hour >= 21 or hour < 5:
        return False
    return True


def is_recap_time():
    now_paris = datetime.now(ZoneInfo("Europe/Paris"))
    return now_paris.hour in RECAP_HOURS and now_paris.minute < 30


def send_mail(title, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = title
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)


def get_daily_move(ticker):
    try:
        data = yf.download(
            ticker,
            period="10d",
            interval="1d",
            progress=False,
            auto_adjust=True,
        )

        if data is None or len(data) < 2:
            return None

        close = data["Close"]
        if hasattr(close, "iloc") and close.ndim > 1:
            close = close.iloc[:, 0]

        close = close.dropna()

        if len(close) < 2:
            return None

        last = float(close.iloc[-1])
        prev = float(close.iloc[-2])

        last_date = close.index[-1]
        prev_date = close.index[-2]

        print(f"{ticker}: comparaison {prev_date.strftime('%d/%m')} ({prev:.2f}) -> {last_date.strftime('%d/%m')} ({last:.2f})")

        return ((last - prev) / prev) * 100, last
    except Exception as e:
        print(f"Erreur sur {ticker} : {e}")
        return None


def save_history(results, now_paris):
    file_exists = os.path.isfile(HISTORY_FILE)

    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["datetime", "ticker", "name", "price", "variation_pct"])

        timestamp = now_paris.strftime("%Y-%m-%d %H:%M")
        for r in results:
            writer.writerow([timestamp, r["ticker"], r["name"], f"{r['price']:.2f}", f"{r['move']:.2f}"])


def build_html(results, alerts, major_moves, title_label):
    now = datetime.now(ZoneInfo("Europe/Paris")).strftime("%d/%m/%Y %H:%M")

    # --- Bloc "mouvements majeurs" (en haut, très visible) ---
    major_html = ""
    if major_moves:
        cards = ""
        for r in major_moves:
            move = r["move"]
            grad = "linear-gradient(135deg, #22c55e, #16a34a)" if move > 0 else "linear-gradient(135deg, #ef4444, #dc2626)"
            sens = "HAUSSE" if move > 0 else "BAISSE"
            cards += f"""
            <div style="background:{grad}; border-radius:12px; padding:16px; margin-bottom:10px; color:#fff;">
              <div style="font-size:13px; font-weight:700; letter-spacing:1px; opacity:0.9;">🔥 MOUVEMENT MAJEUR — {sens}</div>
              <div style="font-size:20px; font-weight:800; margin-top:4px;">{r['name']} ({r['ticker']})</div>
              <div style="font-size:28px; font-weight:800; margin-top:6px;">{move:+.2f}%</div>
              <div style="font-size:13px; opacity:0.9; margin-top:4px;">Prix actuel : {r['price']:.2f}</div>
            </div>
            """
        major_html = f"""
        <div style="margin:0 0 20px 0;">
          {cards}
        </div>
        """

    # --- Cards par action ---
    cards_html = ""
    for r in results:
        move = r["move"]
        if move >= 3:
            bg = "#dcfce7"
            txt = "#15803d"
        elif move >= 0:
            bg = "#f0fdf4"
            txt = "#22c55e"
        elif move >= -3:
            bg = "#fef2f2"
            txt = "#f87171"
        else:
            bg = "#fee2e2"
            txt = "#dc2626"

        arrow = "▲" if move >= 0 else "▼"

        cards_html += f"""
        <tr>
          <td style="padding:6px 0;">
            <div style="background:{bg}; border-radius:10px; padding:14px 16px; display:flex; justify-content:space-between; align-items:center;">
              <div>
                <div style="font-weight:700; color:#111827; font-size:15px;">{r['name']}</div>
                <div style="color:#9ca3af; font-size:12px; margin-top:2px;">{r['ticker']} · {r['price']:.2f} €</div>
              </div>
              <div style="background:{txt}; color:#fff; border-radius:8px; padding:8px 14px; font-weight:800; font-size:15px; white-space:nowrap;">
                {arrow} {move:+.2f}%
              </div>
            </div>
          </td>
        </tr>
        """

    # --- Bloc alertes seuils ---
    alerts_html = ""
    if alerts:
        items = "".join(f"<li style='margin:4px 0;'>{a}</li>" for a in alerts)
        alerts_html = f"""
        <div style="margin-top:20px; padding:16px; background:#fef9c3; border-radius:10px; border:2px solid #facc15;">
          <strong style="color:#854d0e; font-size:14px;">⚡ Seuils dépassés</strong>
          <ul style="margin:8px 0 0 0; padding-left:20px; color:#713f12; font-size:13px;">
            {items}
          </ul>
        </div>
        """

    return f"""
    <html>
      <head>
        <meta name="format-detection" content="telephone=no, date=no, address=no, email=no, url=no">
      </head>
      <body style="margin:0; padding:0; background:#f3f4f6; font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; padding:20px;">
          <div style="background:linear-gradient(135deg, #6366f1, #8b5cf6); border-radius:16px; padding:24px; margin-bottom:16px; color:#fff;">
            <div style="font-size:22px; font-weight:800;">📊 {title_label}</div>
            <div style="font-size:13px; opacity:0.85; margin-top:4px;">{now}</div>
          </div>

          {major_html}

          <div style="background:#ffffff; border-radius:16px; padding:16px; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <table style="width:100%; border-collapse:collapse;">
              {cards_html}
            </table>
            {alerts_html}
          </div>

          <div style="text-align:center; padding:16px;">
            <p style="font-size:11px; color:#9ca3af; margin:0;">Bot automatique · GitHub Actions</p>
          </div>
        </div>
      </body>
    </html>
    """


def main():
    if not is_market_hours():
        print("Hors plage horaire (21h-5h Paris), pas d'envoi.")
        return

    now_paris = datetime.now(ZoneInfo("Europe/Paris"))
    results = []
    alerts = []
    major_moves = []

    print("=== SCAN CAC / EURONEXT ===")

    for ticker, name in TICKERS.items():
        data = get_daily_move(ticker)
        if data is None:
            continue

        move, price = data
        results.append({"ticker": ticker, "name": name, "move": move, "price": price})
        print(f"{name} ({ticker}) : {move:.2f}% | {price:.2f}")

        threshold = THRESHOLDS.get(ticker)
        if threshold is not None and abs(move) >= threshold:
            direction = "hausse" if move > 0 else "baisse"
            alerts.append(f"{name} ({ticker}) en {direction} de {move:.2f}%")

        if abs(move) >= MAJOR_MOVE_THRESHOLD:
            major_moves.append({"ticker": ticker, "name": name, "move": move, "price": price})

    results.sort(key=lambda x: x["move"], reverse=True)

    save_history(results, now_paris)

    recap = is_recap_time()

    if alerts or major_moves:
        html_body = build_html(results, alerts, major_moves, "Scan Bourse FR")
        title = "🔥 MOUVEMENT MAJEUR" if major_moves else "📈 ALERTE — Scan bourse"
        send_mail(title, html_body)
        print("\n=== MAIL ALERTE ENVOYÉ ===")
    elif recap:
        html_body = build_html(results, alerts, major_moves, "Récap quotidien — Scan Bourse FR")
        send_mail("📊 Récap quotidien — Scan bourse", html_body)
        print("\n=== MAIL RECAP ENVOYÉ ===")
    else:
        print("\n=== Pas d'alerte / pas l'heure du récap, aucun mail envoyé ===")


if __name__ == "__main__":
    main()

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import yfinance as yf

TICKERS = {
    "STM": "STMicroelectronics",
    "SU.PA": "Schneider Electric",
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
    "TEP.PA": "Teleperformance",
    "OVH.PA": "OVHcloud",
    "VLA.PA": "Valneva",
}

THRESHOLDS = {
    "STM": 5,
    "SOI.PA": 5,
}

EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_TO = os.environ["EMAIL_TO"]
EMAIL_PASS = os.environ["EMAIL_PASS"]


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
            period="5d",
            interval="1d",
            progress=False,
            auto_adjust=True,
        )

        if data is None or len(data) < 2:
            return None

        close = data["Close"]
        if hasattr(close, "iloc") and close.ndim > 1:
            close = close.iloc[:, 0]

        prev = float(close.iloc[-2])
        last = float(close.iloc[-1])
        last_price = last

        return ((last - prev) / prev) * 100, last_price

    except Exception as e:
        print(f"Erreur sur {ticker} : {e}")
        return None


def build_html(results, alerts):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    rows = ""
    for r in results:
        move = r["move"]
        color = "#16a34a" if move >= 0 else "#dc2626"
        arrow = "▲" if move >= 0 else "▼"
        rows += f"""
        <tr style="border-bottom:1px solid #eee;">
          <td style="padding:10px 12px; font-weight:600;">{r['name']}</td>
          <td style="padding:10px 12px; color:#888; font-size:13px;">{r['ticker']}</td>
          <td style="padding:10px 12px; text-align:right;">{r['price']:.2f}</td>
          <td style="padding:10px 12px; text-align:right; color:{color}; font-weight:700;">
            {arrow} {move:+.2f}%
          </td>
        </tr>
        """

    alerts_html = ""
    if alerts:
        items = "".join(f"<li style='margin:4px 0;'>{a}</li>" for a in alerts)
        alerts_html = f"""
        <div style="margin-top:24px; padding:16px; background:#fef3c7; border-left:4px solid #f59e0b; border-radius:6px;">
          <strong style="color:#92400e;">⚠️ Alertes seuils dépassés</strong>
          <ul style="margin:8px 0 0 0; padding-left:20px; color:#78350f;">
            {items}
          </ul>
        </div>
        """

    return f"""
    <html>
      <body style="margin:0; padding:0; background:#f4f4f7; font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; padding:24px;">
          <div style="background:#ffffff; border-radius:10px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,0.08);">
            <div style="background:#111827; padding:20px 24px;">
              <h1 style="color:#fff; font-size:18px; margin:0;">📈 Scan Bourse FR</h1>
              <p style="color:#9ca3af; font-size:13px; margin:4px 0 0 0;">{now}</p>
            </div>
            <div style="padding:0 24px;">
              <table style="width:100%; border-collapse:collapse; margin-top:8px;">
                <thead>
                  <tr style="text-align:left; font-size:12px; color:#9ca3af; text-transform:uppercase;">
                    <th style="padding:10px 12px;">Société</th>
                    <th style="padding:10px 12px;">Ticker</th>
                    <th style="padding:10px 12px; text-align:right;">Prix</th>
                    <th style="padding:10px 12px; text-align:right;">Variation</th>
                  </tr>
                </thead>
                <tbody>
                  {rows}
                </tbody>
              </table>
              {alerts_html}
            </div>
            <div style="padding:16px 24px; text-align:center;">
              <p style="font-size:11px; color:#9ca3af; margin:0;">Bot automatique · GitHub Actions</p>
            </div>
          </div>
        </div>
      </body>
    </html>
    """


def main():
    results = []
    alerts = []

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

    # Tri par variation décroissante
    results.sort(key=lambda x: x["move"], reverse=True)

    html_body = build_html(results, alerts)
    title = "📈 Scan bourse" + (" — ⚠️ ALERTE" if alerts else "")

    send_mail(title, html_body)
    print("\n=== MAIL ENVOYÉ ===")


if __name__ == "__main__":
    main()

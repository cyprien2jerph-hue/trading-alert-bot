import os
import smtplib
from email.mime.text import MIMEText
import yfinance as yf

TICKERS = {
    "STM": "STMicroelectronics",
    "2CRSI.PA": "2CRSi",
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

# Seuils d'alerte (en %) — optionnel, met None pour désactiver les alertes par titre
THRESHOLDS = {
    "NVDA": 4,
    "STM": 5,
    "SOI.PA": 5,
}

EMAIL_FROM = os.environ["EMAIL_FROM"]
EMAIL_TO = os.environ["EMAIL_TO"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]


def send_mail(title, body):
    msg = MIMEText(body)
    msg["Subject"] = title
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_FROM, EMAIL_PASSWORD)
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

        # Gère le cas MultiIndex (plusieurs colonnes possibles selon version yfinance)
        if hasattr(close, "iloc") and close.ndim > 1:
            close = close.iloc[:, 0]

        prev = float(close.iloc[-2])
        last = float(close.iloc[-1])

        return ((last - prev) / prev) * 100

    except Exception as e:
        print(f"Erreur sur {ticker} : {e}")
        return None


def main():
    results = []
    alerts = []

    print("=== SCAN CAC / EURONEXT ===")

    for ticker, name in TICKERS.items():
        move = get_daily_move(ticker)

        if move is None:
            continue

        results.append({"ticker": ticker, "name": name, "move": move})
        print(f"{name} ({ticker}) : {move:.2f}%")

        threshold = THRESHOLDS.get(ticker)
        if threshold is not None and abs(move) >= threshold:
            direction = "hausse" if move > 0 else "baisse"
            alerts.append(f"{name} ({ticker}) en {direction} de {move:.2f}%")

    results.sort(key=lambda x: x["move"], reverse=True)

    print("\n=== TOP MOMENTUM ===")
    for r in results[:5]:
        print(f"{r['name']} | {r['ticker']} | {r['move']:.2f}%")

    print("\n=== FLOP MOMENTUM ===")
    for r in results[-5:]:
        print(f"{r['name']} | {r['ticker']} | {r['move']:.2f}%")

    # --- Construction du mail récap ---
    lines = []
    lines.append("=== TOUTES LES VALEURS ===")
    for r in results:
        lines.append(f"{r['name']} ({r['ticker']}) : {r['move']:.2f}%")

    if alerts:
        lines.append("\n=== ALERTES ===")
        lines.extend(alerts)

    body = "\n".join(lines)
    title = "Scan bourse - " + ("ALERTE" if alerts else "Récap horaire")

    send_mail(title, body)
    print("\n=== MAIL ENVOYÉ ===")


if __name__ == "__main__":
    main()

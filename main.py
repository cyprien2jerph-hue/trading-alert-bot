import os
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")
import yfinance as yf
if data is None or len(data) < 2:
    print("Pas assez de données marché")
    exit()
import smtplib
from email.mime.text import MIMEText

# --- CONFIG ---
EMAIL_USER = "cyprien2jerph@gmail.com"
EMAIL_PASS = "exwr endx fval olar "
EMAIL_TO = "cyprien2jerph@gmail.com"

TICKER = "NVDA"

# --- récupérer prix ---
data = yf.download(TICKER, period="1d", interval="5m")

try:
    current_price = data["Close"].iloc[-1]
    previous_price = data["Close"].iloc[0]
except:
    print("Erreur lecture données")
    exit()

change = ((current_price - previous_price) / previous_price) * 100

print(f"{TICKER} variation: {change:.2f}%")

# --- condition d'alerte ---
if abs(change) >= 2.5:
    subject = f"ALERTE {TICKER} {change:.2f}%"

    body = f"""
    Mouvement important détecté :

    Action : {TICKER}
    Variation : {change:.2f}%

    Prix actuel : {current_price}
    """

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASS)
    server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())
    server.quit()

    print("Email envoyé")
else:
    print("Pas de signal important")

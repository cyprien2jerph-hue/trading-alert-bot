import yfinance as yf

# =========================
# ACTIONS FRANÇAISES
# =========================

TICKERS = {
    "SOI.PA": "Soitec",
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
    "GLE.PA": "Société Générale"
}
}

# =========================
# CALCUL VARIATION
# =========================

def get_daily_move(ticker):
    try:
        data = yf.download(
            ticker,
            period="5d",
            interval="1d",
            progress=False,
            auto_adjust=True
        )

        if data is None or len(data) < 2:
            return None

        close = data["Close"]

        prev = float(close.iloc[-2])
        last = float(close.iloc[-1])

        return ((last - prev) / prev) * 100

    except Exception as e:
        print(f"Erreur sur {ticker} : {e}")
        return None

# =========================
# SCAN
# =========================

results = []

print("=== SCAN CAC / EURONEXT ===")

for ticker, name in TICKERS.items():

    move = get_daily_move(ticker)

    if move is None:
        continue

    results.append({
        "ticker": ticker,
        "name": name,
        "move": move
    })

    print(f"{name} ({ticker}) : {move:.2f}%")

# =========================
# CLASSEMENT
# =========================

results.sort(key=lambda x: x["move"], reverse=True)

print("\n=== TOP MOMENTUM ===")

for r in results[:5]:
    print(
        f"{r['name']} | {r['ticker']} | {r['move']:.2f}%"
    )

print("\n=== FLOP MOMENTUM ===")

for r in results[-5:]:
    print(
        f"{r['name']} | {r['ticker']} | {r['move']:.2f}%"
    )

print("\n=== FIN DU SCAN ===")

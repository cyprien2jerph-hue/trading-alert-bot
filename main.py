import yfinance as yf

# =========================
# UNIVERS CAC 40 / FRANCE
# =========================

TICKERS = {
    "STMPA.PA": "STMicroelectronics",
    "SOI.PA": "Soitec",
    "SU.PA": "Schneider Electric",
    "AIR.PA": "Airbus",
    "HO.PA": "Thales",
    "CAP.PA": "Capgemini",
    "OR.PA": "L'Oréal",
    "MC.PA": "LVMH",
    "AI.PA": "Air Liquide",
    "SAF.PA": "Safran"
}

# =========================
# CALCUL VARIATION
# =========================

def get_daily_move(ticker):
    data = yf.download(ticker, period="2d", interval="1d", progress=False)

    if data is None or len(data) < 2:
        return None

    prev = data["Close"].iloc[-2]
    last = data["Close"].iloc[-1]

    return ((last - prev) / prev) * 100

# =========================
# SCAN DU MARCHE
# =========================

results = {}

print("=== SCAN CAC 40 MOMENTUM ===")

for ticker, name in TICKERS.items():

    move = get_daily_move(ticker)

    if move is None:
        continue

    results[ticker] = (name, move)

    print(f"{name} ({ticker}) : {move:.2f}%")

# =========================
# RANKING
# =========================

ranked = sorted(results.items(), key=lambda x: x[1][1], reverse=True)

print("\n=== TOP MOMENTUM ===")

for ticker, (name, move) in ranked:
    print(f"{name} : {move:.2f}%")

# =========================
# SIGNALS
# =========================

if len(ranked) > 0:

    best_ticker, (best_name, best_move) = ranked[0]
    worst_ticker, (worst_name, worst_move) = ranked[-1]

    print("\n=== SIGNALS ===")

    if best_move > 2:
        print(f"🔥 LEADER DU JOUR : {best_name} ({best_move:.2f}%)")

    if worst_move < -2:
        print(f"⚠️ FAIBLE : {worst_name} ({worst_move:.2f}%)")

print("\n=== END ===")

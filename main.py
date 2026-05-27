import yfinance as yf

WATCHLIST = {
    "NVDA": 4,
    "STM.PA": 5,
    "SOI.PA": 5
}

def get_move(ticker):
    data = yf.download(ticker, period="2d", interval="1h")
    if len(data) < 2:
        return None

    old = data["Close"].iloc[-2]
    new = data["Close"].iloc[-1]

    return ((new - old) / old) * 100


for ticker, seuil in WATCHLIST.items():
    try:
        move = get_move(ticker)

        if move is None:
            continue

        print(ticker, "variation :", round(move, 2), "%")

        if abs(move) >= seuil:
            print("🚨 ALERTE :", ticker)

    except Exception as e:
        print("Erreur :", ticker, e)

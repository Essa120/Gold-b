import requests
import pandas as pd
from datetime import datetime
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
API_KEY = "4641d466300d46c587952fd42f03e811"

symbols = {
    "GOLD": "XAU/USD",
    "BTC/USD": "BTC/USD",
    "ETH/USD": "ETH/USD"
}

intervals = ["1min", "5min", "15min", "1h"]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram error:", e)

def fetch_data(symbol, interval):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={API_KEY}"
        res = requests.get(url)
        data = res.json()
        if "values" not in data:
            raise ValueError(data.get("message", "No data"))
        df = pd.DataFrame(data["values"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        df = df.astype(float).sort_index()
        return df
    except Exception as e:
        send_telegram(f"⚠️ Error fetching {symbol} [{interval}]: {e}")
        return None

def calculate_rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df):
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line, signal_line

def get_signal(df):
    df["fast"] = df["close"].rolling(3).mean()
    df["slow"] = df["close"].rolling(7).mean()
    df["RSI"] = calculate_rsi(df)
    df["MACD"], df["MACD_signal"] = calculate_macd(df)

    if df["RSI"].iloc[-1] > 70 or df["RSI"].iloc[-1] < 30:
        return None  # RSI تشبع

    price_condition = None
    macd_condition = None

    if df["fast"].iloc[-1] > df["slow"].iloc[-1] and df["fast"].iloc[-2] <= df["slow"].iloc[-2]:
        price_condition = "BUY"
    elif df["fast"].iloc[-1] < df["slow"].iloc[-1] and df["fast"].iloc[-2] >= df["slow"].iloc[-2]:
        price_condition = "SELL"

    if df["MACD"].iloc[-1] > df["MACD_signal"].iloc[-1] and df["MACD"].iloc[-2] <= df["MACD_signal"].iloc[-2]:
        macd_condition = "BUY"
    elif df["MACD"].iloc[-1] < df["MACD_signal"].iloc[-1] and df["MACD"].iloc[-2] >= df["MACD_signal"].iloc[-2]:
        macd_condition = "SELL"

    if price_condition and macd_condition and price_condition == macd_condition:
        return price_condition
    else:
        return None

def generate_signals():
    for name, symbol in symbols.items():
        signal_counts = {"BUY": 0, "SELL": 0}
        price = None

        for interval in intervals:
            df = fetch_data(symbol, interval)
            if df is None or len(df) < 30:
                continue
            sig = get_signal(df)
            if sig:
                signal_counts[sig] += 1
                if price is None:
                    price = round(df["close"].iloc[-1], 2)

        total = sum(signal_counts.values())
        if total >= 2:
            direction = "BUY" if signal_counts["BUY"] > signal_counts["SELL"] else "SELL"
            confidence = round((signal_counts[direction] / total) * 100, 1)
            tp = round(price * (1.001 if direction == "BUY" else 0.999), 2)
            sl = round(price * (0.999 if direction == "BUY" else 1.001), 2)

            msg = (
                f"{direction} {name}\n"
                f"نسبة نجاح متوقعة: %{confidence}\n"
                f"دخول: {price}\n"
                f"TP: {tp}\n"
                f"SL: {sl}\n"
                f"UTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            send_telegram(msg)

@app.route('/')
def home():
    return "Multi-timeframe bot with RSI + MACD is running!"

@app.route('/run')
def run_now():
    generate_signals()
    return "Executed!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

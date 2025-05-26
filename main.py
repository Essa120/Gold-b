import requests
import pandas as pd
from flask import Flask
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
API_KEY = "4641d466300d46c587952fd42f03e811"

symbols = {
    "GOLD": "XAU/USD",
    "BTC/USD": "BTC/USD",
    "ETH/USD": "ETH/USD"
}

intervals = ["1min", "15min"]


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram Error:", e)


def fetch_data(symbol, interval):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=30&apikey={API_KEY}"
        res = requests.get(url)
        data = res.json()

        if "values" not in data:
            raise ValueError(data.get("message", "No data"))

        df = pd.DataFrame(data["values"])
        df = df.rename(columns={"datetime": "timestamp", "close": "price"})
        df["price"] = df["price"].astype(float)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp").sort_index()
        return df
    except Exception as e:
        send_telegram(f"⚠️ Error fetching {symbol} [{interval}]: {e}")
        return None


def analyze():
    for name, symbol in symbols.items():
        frames_data = []

        for interval in intervals:
            df = fetch_data(symbol, interval)
            if df is None or len(df) < 15:
                continue

            df["fast"] = df["price"].rolling(window=3).mean()
            df["slow"] = df["price"].rolling(window=7).mean()
            df["macd"] = df["fast"] - df["slow"]

            last_fast = df["fast"].iloc[-1]
            last_slow = df["slow"].iloc[-1]
            prev_fast = df["fast"].iloc[-2]
            prev_slow = df["slow"].iloc[-2]

            signal = None
            if last_fast > last_slow and prev_fast <= prev_slow:
                signal = "BUY"
            elif last_fast < last_slow and prev_fast >= prev_slow:
                signal = "SELL"

            if signal:
                score = ((last_fast - last_slow) / df["price"].iloc[-1]) * 10000
                frames_data.append((signal, round(score, 1)))

        if not frames_data:
            continue

        # فلترة الإشارات الضعيفة
        signals = [s for s in frames_data if abs(s[1]) >= 10]
        if not signals:
            continue

        main_signal = max(signals, key=lambda x: x[1])
        direction, confidence = main_signal
        price = round(df["price"].iloc[-1], 2)
        tp = round(price * (1.001 if direction == "BUY" else 0.999), 2)
        sl = round(price * (0.999 if direction == "BUY" else 1.001), 2)

       

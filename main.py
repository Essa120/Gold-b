import requests
import pandas as pd
from datetime import datetime
from flask import Flask

app = Flask(__name__)

# إعدادات
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
API_KEY = "4641d466300d46c587952fd42f03e811"

# الأدوات
symbols = {
    "GOLD": "XAU/USD",
    "BTC/USD": "BTC/USD",
    "ETH/USD": "ETH/USD",
    "US30": "DJI",
    "US100": "NDX"
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram Error:", e)

def fetch_data(symbol):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=30&apikey={API_KEY}"
        res = requests.get(url)
        data = res.json()

        if "values" not in data:
            raise ValueError(data.get("message", "No data"))
        
        df = pd.DataFrame(data["values"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        df = df.sort_index()
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        send_telegram(f"⚠️ Error fetching {symbol}: {e}")
        return None

def generate_signals():
    for name, symbol in symbols.items():
        df = fetch_data(symbol)
        if df is None or len(df) < 7:
            continue

        df["fast"] = df["close"].rolling(3).mean()
        df["slow"] = df["close"].rolling(7).mean()

        if df["fast"].iloc[-1] > df["slow"].iloc[-1] and df["fast"].iloc[-2] <= df["slow"].iloc[-2]:
            entry = round(df["close"].iloc[-1], 2)
            tp = round(entry * 1.001, 2)
            sl = round(entry * 0.999, 2)
            msg = (
                f"BUY {name}\n"
                f"دخول: {entry}\n"
                f"TP: {tp}\n"
                f"SL: {sl}\n"
                f"الوقت: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )
            send_telegram(msg)

@app.route("/")
def home():
    return "Bot is running!"

@app.route("/run")
def run_now():
    generate_signals()
    return "Executed."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

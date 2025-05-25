import requests
import pandas as pd
from flask import Flask
from datetime import datetime
import time

app = Flask(__name__)

BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"

# أدوات التداول
symbols = {
    "GOLD": "XAUUSD=X",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "US30": "^DJI",
    "US100": "^NDX"
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram Error:", e)

def fetch_data(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=15m"
        r = requests.get(url)
        data = r.json()

        if "chart" in data and data["chart"]["result"]:
            result = data["chart"]["result"][0]
            prices = result["indicators"]["quote"][0]["close"]
            times = result["timestamp"]
            df = pd.DataFrame({"price": prices}, index=pd.to_datetime(times, unit='s'))
            return df.dropna()
        else:
            raise ValueError("Empty result")
    except Exception as e:
        send_telegram(f"⚠️ Error fetching {symbol}: {e}")
        return None

def generate_signal(name, symbol):
    df = fetch_data(symbol)
    if df is None or len(df) < 7:
        return

    df["fast"] = df["price"].rolling(3).mean()
    df["slow"] = df["price"].rolling(7).mean()

    if df["fast"].iloc[-1] > df["slow"].iloc[-1] and df["fast"].iloc[-2] <= df["slow"].iloc[-2]:
        entry = round(df["price"].iloc[-1], 2)
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
    return "Bot is working."

@app.route("/run")
def run_bot():
    # كل تشغيل يتم تحليل أداة واحدة فقط لتقليل الضغط
    now_index = int(datetime.utcnow().minute / 3) % len(symbols)
    name = list(symbols.keys())[now_index]
    symbol = symbols[name]
    generate_signal(name, symbol)
    return f"Checked {name}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

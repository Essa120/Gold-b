import requests
import pandas as pd
import time
from flask import Flask
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"

symbols = {
    "GOLD": "XAUUSD=X",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "US30": "^DJI",
    "US100": "^NDX"
}

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram Error:", e)

def fetch_yahoo_data(symbol, name):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=15m"
    try:
        res = requests.get(url)
        if res.status_code == 429:
            raise Exception("HTTP 429 - Too Many Requests")
        data = res.json()
        if "chart" in data and data["chart"]["result"]:
            result = data["chart"]["result"][0]
            prices = result["indicators"]["quote"][0]["close"]
            timestamps = result["timestamp"]
            df = pd.DataFrame({"price": prices}, index=pd.to_datetime(timestamps, unit='s'))
            return df.dropna()
        else:
            raise ValueError("No valid chart data")
    except Exception as e:
        send_telegram(f"⚠️ Error fetching {symbol} ({name}):\n{e}")
        return None

def generate_signals():
    for name, symbol in symbols.items():
        df = fetch_yahoo_data(symbol, name)
        time.sleep(5)  # تأخير بسيط بين كل أداة لتفادي الحظر
        if df is None or len(df) < 10:
            continue
        df["fast_ma"] = df["price"].rolling(window=3).mean()
        df["slow_ma"] = df["price"].rolling(window=7).mean()
        if (
            df["fast_ma"].iloc[-1] > df["slow_ma"].iloc[-1] and
            df["fast_ma"].iloc[-2] <= df["slow_ma"].iloc[-2]
        ):
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

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/run')
def run_now():
    send_telegram("✅ تم تشغيل السيرفر بنجاح! البوت يعمل الآن 24/7")
    generate_signals()
    return "Bot executed."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

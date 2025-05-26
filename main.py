import requests
import pandas as pd
from flask import Flask
from datetime import datetime
import numpy as np

app = Flask(__name__)

BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
API_KEY = "4641d466300d46c587952fd42f03e811"

symbols = {
    "XAU/USD": "XAU/USD",
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
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={API_KEY}"
    try:
        res = requests.get(url)
        data = res.json()
        if "values" not in data:
            raise ValueError(data.get("message", "No data returned"))

        df = pd.DataFrame(data["values"])
        df = df.rename(columns={"datetime": "time", "close": "price"})
        df["price"] = df["price"].astype(float)
        df = df.sort_values("time")
        return df
    except Exception as e:
        send_telegram(f"⚠️ Error fetching {symbol} [{interval}]: {e}")
        return None

def calculate_indicators(df):
    df["MA_fast"] = df["price"].rolling(window=3).mean()
    df["MA_slow"] = df["price"].rolling(window=7).mean()
    df["EMA"] = df["price"].ewm(span=5, adjust=False).mean()
    df["RSI"] = compute_rsi(df["price"], 14)
    df["MACD"] = df["price"].ewm(span=12).mean() - df["price"].ewm(span=26).mean()
    return df

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def analyze(df):
    if df is None or len(df) < 20:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    if (
        last["MA_fast"] > last["MA_slow"] and prev["MA_fast"] <= prev["MA_slow"]
        and last["RSI"] < 70 and last["MACD"] > 0
    ):
        return "buy", last["price"]
    elif (
        last["MA_fast"] < last["MA_slow"] and prev["MA_fast"] >= prev["MA_slow"]
        and last["RSI"] > 30 and last["MACD"] < 0
    ):
        return "sell", last["price"]
    else:
        return None

def generate_signals():
    for name, symbol in symbols.items():
        results = []
        for interval in intervals:
            df = fetch_data(symbol, interval)
            if df is not None:
                df = calculate_indicators(df)
                result = analyze(df)
                if result:
                    results.append((interval, result))

        # فلترة الإشارات بناءً على تقاطع الفريمات
        buys = [res for res in results if res[1][0] == "buy"]
        sells = [res for res in results if res[1][0] == "sell"]

        if len(buys) == len(intervals):
            entry = round(buys[0][1][1], 2)
            tp = round(entry * 1.001, 2)
            sl = round(entry * 0.999, 2)
            percent = round((tp - entry) / (entry - sl) * 100, 1)
            msg = (
                f"BUY {name}\n"
                f"نسبة نجاح متوقعة: %{percent}\n"
                f"دخول: {entry}\nTP: {tp}\nSL: {sl}\n"
                f"UTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            send_telegram(msg)
        elif len(sells) == len(intervals):
            entry = round(sells[0][1][1], 2)
            tp = round(entry * 0.999, 2)
            sl = round(entry * 1.001, 2)
            percent = round((entry - tp) / (sl - entry) * 100, 1)
            msg = (
                f"SELL {name}\n"
                f"نسبة نجاح متوقعة: %{percent}\n"
                f"دخول: {entry}\nTP: {tp}\nSL: {sl}\n"
                f"UTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
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

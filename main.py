
import requests
import pandas as pd
from flask import Flask
from datetime import datetime
import threading
import time

# بيانات بوت Telegram
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"

# إعداد Flask للسيرفر
app = Flask(__name__)

# رموز الأدوات المطلوبة من Yahoo Finance
symbols = {
    "GOLD": "GC=F",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD"
}

# إرسال رسالة إلى تيليجرام
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram Error:", e)

# جلب البيانات من Yahoo Finance
def fetch_data(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=15m"
        response = requests.get(url)
        if response.status_code != 200:
            raise ValueError(f"Invalid HTTP status: {response.status_code}")
        data = response.json()
        result = data["chart"]["result"][0]
        prices = result["indicators"]["quote"][0]["close"]
        timestamps = result["timestamp"]
        df = pd.DataFrame({"price": prices}, index=pd.to_datetime(timestamps, unit="s"))
        return df.dropna()
    except Exception as e:
        send_telegram(f"⚠️ {symbol}: فشل تحميل البيانات من جميع المصادر\nYahoo error: {str(e)}")
        return None

# تحليل البيانات وإرسال التوصيات
last_signals = {}

def analyze():
    for name, symbol in symbols.items():
        df = fetch_data(symbol)
        if df is None or len(df) < 10:
            continue

        df["fast_ma"] = df["price"].rolling(window=3).mean()
        df["slow_ma"] = df["price"].rolling(window=7).mean()

        if (
            df["fast_ma"].iloc[-1] > df["slow_ma"].iloc[-1]
            and df["fast_ma"].iloc[-2] <= df["slow_ma"].iloc[-2]
        ):
            signal = "BUY"
        elif (
            df["fast_ma"].iloc[-1] < df["slow_ma"].iloc[-1]
            and df["fast_ma"].iloc[-2] >= df["slow_ma"].iloc[-2]
        ):
            signal = "SELL"
        else:
            continue

        entry = round(df["price"].iloc[-1], 2)
        tp = round(entry * 1.001, 2) if signal == "BUY" else round(entry * 0.999, 2)
        sl = round(entry * 0.999, 2) if signal == "BUY" else round(entry * 1.001, 2)
        confidence = round(abs(df["fast_ma"].iloc[-1] - df["slow_ma"].iloc[-1]) / entry * 100, 1)

        message = (
            f"{signal} {name}\n"
            f"نسبة نجاح متوقعة: %{confidence}\n"
            f"دخول: {entry}\n"
            f"TP: {tp}\n"
            f"SL: {sl}\n"
            f"UTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # فلترة التكرار
        if last_signals.get(name) != message:
            send_telegram(message)
            last_signals[name] = message

@app.route('/')
def index():
    return 'ScalpX Bot is Running!'

def run_loop():
    while True:
        analyze()
        time.sleep(300)

if __name__ == '__main__':
    threading.Thread(target=run_loop).start()
    app.run(host='0.0.0.0', port=10000)

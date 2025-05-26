import yfinance as yf
import requests
import pandas as pd
import threading
import time
from flask import Flask
from datetime import datetime

# بيانات البوت
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"

# إعداد تطبيق Flask
app = Flask(__name__)

# الأدوات المطلوبة
symbols = {
    "GOLD": "GC=F",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD"
}

# سجل آخر توصية لكل أداة لتجنب التكرار
last_signals = {}

# إرسال رسالة تيليجرام
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram Error:", e)

# تحليل البيانات وإصدار إشارات
def analyze():
    for name, symbol in symbols.items():
        try:
            df = yf.download(tickers=symbol, interval="1m", period="15m", progress=False)
            if df.empty or len(df) < 7:
                continue

            df["fast_ma"] = df["Close"].rolling(window=3).mean()
            df["slow_ma"] = df["Close"].rolling(window=7).mean()

            signal = ""
            if df["fast_ma"].iloc[-1] > df["slow_ma"].iloc[-1] and df["fast_ma"].iloc[-2] <= df["slow_ma"].iloc[-2]:
                signal = "BUY"
            elif df["fast_ma"].iloc[-1] < df["slow_ma"].iloc[-1] and df["fast_ma"].iloc[-2] >= df["slow_ma"].iloc[-2]:
                signal = "SELL"
            else:
                continue

            entry = round(df["Close"].iloc[-1], 2)
            tp = round(entry * 1.001, 2) if signal == "BUY" else round(entry * 0.999, 2)
            sl = round(entry * 0.999, 2) if signal == "BUY" else round(entry * 1.001, 2)
            confidence = round(abs(df["fast_ma"].iloc[-1] - df["slow_ma"].iloc[-1]) / entry * 100, 2)

            message = (
                f"{signal} {name}\n"
                f"نسبة نجاح متوقعة: %{confidence}\n"
                f"دخول: {entry}\n"
                f"TP: {tp}\n"
                f"SL: {sl}\n"
                f"UTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            if last_signals.get(name) != message:
                send_telegram(message)
                last_signals[name] = message

        except Exception as e:
            send_telegram(f"⚠️ {symbol}: خطأ في تحميل البيانات\n{str(e)}")

@app.route('/')
def index():
    return "ScalpX Bot is Running!"

def run_loop():
    while True:
        analyze()
        time.sleep(300)

if __name__ == '__main__':
    threading.Thread(target=run_loop).start()
    app.run(host='0.0.0.0', port=10000)

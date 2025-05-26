import os
import requests
import time
import threading
import pandas as pd
from datetime import datetime
from flask import Flask
from dotenv import load_dotenv
import yfinance as yf

# تحميل متغيرات البيئة
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# إعداد التطبيق
app = Flask(__name__)

# أدوات التحليل
symbols = {
    "GOLD": "XAUUSD=X",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD"
}

# ذاكرة لمنع التكرار
last_signals = {}

# إرسال رسالة إلى تليجرام
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=payload)
    except:
        print("خطأ في إرسال الرسالة")

# التحليل الفني باستخدام Yahoo Finance
def analyze():
    global last_signals
    for name, symbol in symbols.items():
        try:
            df = yf.download(symbol, period="1d", interval="1m")
            if df is None or df.empty or len(df) < 30:
                continue

            df['sma'] = df['Close'].rolling(window=9).mean()
            df['macd'] = df['Close'].ewm(span=12, adjust=False).mean() - df['Close'].ewm(span=26, adjust=False).mean()

            signal = ''
            if df['Close'].iloc[-1] > df['sma'].iloc[-1] and df['macd'].iloc[-1] > 0:
                signal = 'BUY'
            elif df['Close'].iloc[-1] < df['sma'].iloc[-1] and df['macd'].iloc[-1] < 0:
                signal = 'SELL'

            if signal:
                price = round(df['Close'].iloc[-1], 2)
                tp = round(price * 1.001, 2) if signal == 'BUY' else round(price * 0.999, 2)
                sl = round(price * 0.999, 2) if signal == 'BUY' else round(price * 1.001, 2)
                key = f"{name}-{signal}-{price}"

                if last_signals.get(name) != key:
                    last_signals[name] = key
                    msg = (
                        f"{signal} {name}\n"
                        f"نسبة نجاح متوقعة: %60\n"
                        f"دخول: {price}\nTP: {tp}\nSL: {sl}\n"
                        f"UTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    send_message(msg)
        except Exception as e:
            send_message(f"⚠️ خطأ أثناء تحليل {name}: {e}")

# الصفحة الرئيسية
@app.route('/')
def index():
    return 'ScalpX Bot is Running!'

# بدء الحلقة الزمنية

def run():
    while True:
        analyze()
        time.sleep(300)  # كل 5 دقائق

if __name__ == '__main__':
    threading.Thread(target=run).start()
    app.run(host='0.0.0.0', port=10000)

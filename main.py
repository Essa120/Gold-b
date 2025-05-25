from flask import Flask
import requests
import os
import time
import threading
import pandas as pd
from datetime import datetime
import yfinance as yf

app = Flask(__name__)

BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
ALERT_FLAG_FILE = "boot_alert_sent.txt"

# الأدوات المطلوبة
SYMBOLS = {
    "GOLD": "GC=F",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "US30": "^DJI",
    "US100": "^IXIC"
}

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)

# إرسال رسالة التشغيل مرة واحدة فقط
def notify_on_boot():
    if not os.path.exists(ALERT_FLAG_FILE):
        send_telegram_message("✅ تم تشغيل السيرفر بنجاح! البوت يعمل الآن 24/7")
        with open(ALERT_FLAG_FILE, "w") as f:
            f.write("sent")

# السكالبينج البسيط
def check_signals():
    while True:
        for name, symbol in SYMBOLS.items():
            try:
                df = yf.download(symbol, period="1d", interval="1m")
                ma5 = df['Close'].rolling(window=5).mean()
                ma20 = df['Close'].rolling(window=20).mean()

                if ma5.iloc[-2] < ma20.iloc[-2] and ma5.iloc[-1] > ma20.iloc[-1]:
                    text = f"BUY {name}\nدخول: Ticker\n{df.tail(1)}\n\nTP: Ticker\n{df.tail(1) + 10}\n\nSL: Ticker\n{df.tail(1) - 10}"
                    send_telegram_message(text)

                elif ma5.iloc[-2] > ma20.iloc[-2] and ma5.iloc[-1] < ma20.iloc[-1]:
                    text = f"SELL {name}\nدخول: Ticker\n{df.tail(1)}\n\nTP: Ticker\n{df.tail(1) - 10}\n\nSL: Ticker\n{df.tail(1) + 10}"
                    send_telegram_message(text)
            except Exception as e:
                send_telegram_message(f"Error with {name}: {e}")
        time.sleep(300)

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == '__main__':
    notify_on_boot()
    threading.Thread(target=check_signals).start()
    app.run(host='0.0.0.0', port=10000)

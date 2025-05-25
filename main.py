from flask import Flask
import requests
import pandas as pd
import time
import threading
from datetime import datetime
import yfinance as yf

app = Flask(__name__)

# إعدادات تيليجرام
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# الرموز
SYMBOLS = {
    "GOLD": "GC=F",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "US30": "^DJI",
    "US100": "^NDX"
}

sent_startup_message = False

def send_telegram_message(text):
    try:
        requests.post(API_URL, data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("Telegram Error:", e)

def check_signals(symbol_name, yf_symbol):
    try:
        df = yf.download(yf_symbol, interval='1m', period='1d', progress=False)

        if df.empty or len(df) < 11:
            return

        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # تقاطع المتوسطات
        if prev['MA5'] < prev['MA10'] and latest['MA5'] > latest['MA10']:
            direction = "BUY"
        elif prev['MA5'] > prev['MA10'] and latest['MA5'] < latest['MA10']:
            direction = "SELL"
        else:
            return

        entry_price = round(latest['Close'], 2)
        tp = round(entry_price + 10, 2)
        sl = round(entry_price - 10, 2)

        msg = f"{direction} {symbol_name}\n"
        msg += f"دخول: Ticker\n{symbol_name}  {entry_price}\n"
        msg += f"TP: Ticker\n{symbol_name}  {tp}\n"
        msg += f"SL: Ticker\n{symbol_name}  {sl}"
        send_telegram_message(msg)

    except Exception as e:
        send_telegram_message(f"Error with {symbol_name}: {e}")

def run_bot():
    global sent_startup_message
    if not sent_startup_message:
        send_telegram_message("✅ تم تشغيل السيرفر بنجاح! البوت يعمل الآن 24/7")
        sent_startup_message = True

    while True:
        for name, symbol in SYMBOLS.items():
            check_signals(name, symbol)
        time.sleep(300)  # كل 5 دقائق

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=10000)

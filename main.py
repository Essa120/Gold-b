import requests, time, threading
import pandas as pd
from datetime import datetime
from flask import Flask
import yfinance as yf
import os

# إعدادات التوكن والدردشة
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"

# إعداد التطبيق
app = Flask(__name__)

# أدوات التحليل
symbols = ['XAUUSD', 'BTC-USD', 'ETH-USD']
timeframes = {
    '1m': '1m',
    '15m': '15m'
}

# حفظ آخر توصية
last_signals = {}

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=payload)
    except:
        print("فشل في إرسال الرسالة")

def fetch_data_yahoo(symbol, tf):
    try:
        df = yf.download(symbol, period='1d', interval=tf)
        if df is not None and not df.empty:
            df = df.tail(50)
            df.columns = df.columns.str.lower()
            return df
        else:
            return None
    except:
        return None

def analyze():
    global last_signals
    for symbol in symbols:
        for tf in timeframes:
            df = fetch_data_yahoo(symbol, timeframes[tf])
            if df is None:
                send_message(f"⚠️ لا توجد بيانات كافية لـ {symbol} على {tf}.")
                continue

            df['sma'] = df['close'].rolling(window=9).mean()
            df['macd'] = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()

            price = df['close'].iloc[-1]
            sma = df['sma'].iloc[-1]
            macd = df['macd'].iloc[-1]

            signal = ''
            if price > sma and macd > 0:
                signal = 'BUY'
            elif price < sma and macd < 0:
                signal = 'SELL'

            if signal:
                key = f"{symbol}_{tf}"
                prev = last_signals.get(key)
                new = f"{signal}_{round(price,2)}"
                if prev == new:
                    continue  # تجاهل التكرار
                last_signals[key] = new

                tp = round(price * 1.001, 2) if signal == 'BUY' else round(price * 0.999, 2)
                sl = round(price * 0.999, 2) if signal == 'BUY' else round(price * 1.001, 2)

                send_message(f"{signal} {symbol.replace('-', '/')}\nنسبة نجاح متوقعة: 0.2%\nدخول: {price}\nTP: {tp}\nSL: {sl}\nUTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

@app.route('/')
def index():
    return "ScalpX Bot is Running!"

def run():
    while True:
        analyze()
        time.sleep(300)

if __name__ == '__main__':
    threading.Thread(target=run).start()
    app.run(host='0.0.0.0', port=10000)

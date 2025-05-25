from flask import Flask
import requests
import pandas as pd
import time
import threading
import yfinance as yf

app = Flask(__name__)

# إعدادات تيليجرام
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# الرموز المطلوبة
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

        latest_ma5 = df['MA5'].iloc[-1]
        prev_ma5 = df['MA5'].iloc[-2]
        latest_ma10 = df['MA10'].iloc[-1]
        prev_ma10 = df['MA10'].iloc[-2]
        close_price = df['Close'].iloc[-1]

        # تقاطع صريح للمتوسطات
        if prev_ma5 < prev_ma10 and latest_ma5 > latest_ma10:
            signal = "BUY"
        elif prev_ma5 > prev_ma10 and latest_ma5 < latest_ma10:
            signal = "SELL"
        else:
            return

        tp = round(close_price + 10, 2)
        sl = round(close_price - 10, 2)

        msg = f"{signal} {symbol_name}\n"
        msg += f"دخول: Ticker\n{symbol_name}  {round(close_price, 2)}\n"
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
        time.sleep(300)

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=10000)

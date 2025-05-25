import requests
from flask import Flask
import pandas as pd
import time

app = Flask(__name__)

# بيانات تيليجرام
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
SERVER_STARTED = False  # علم لتفادي تكرار رسالة التشغيل

# دالة إرسال رسالة تيليجرام
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram error:", e)

# عند تشغيل السيرفر
@app.route('/')
def home():
    return "Bot is running!"

# أدوات التداول لمراقبتها
symbols = ["GOLD", "BTC/USD", "ETH/USD", "US30", "US100"]

# محاكاة استراتيجية السكالبينج
def scalping_strategy(symbol):
    try:
        # محاكاة بيانات (استبدلها ببيانات حقيقية من API في مشروعك النهائي)
        data = {
            "signal": ["BUY"], 
            "price": [107683.02], 
            "tp": [107693.02], 
            "sl": [107673.02]
        }
        df = pd.DataFrame(data)

        if df.empty:
            return  # تجاهل لو ما فيه بيانات

        signal = df.loc[0, "signal"]
        entry = df.loc[0, "price"]
        tp = df.loc[0, "tp"]
        sl = df.loc[0, "sl"]

        message = (
            f"{signal} {symbol}\n"
            f"دخول: Ticker\n{symbol}  {entry}\n"
            f"TP: Ticker\n{symbol}  {tp}\n"
            f"SL: Ticker\n{symbol}  {sl}"
        )
        send_telegram(message)

    except IndexError:
        send_telegram(f"Error with {symbol}: No data available (IndexError)")
    except Exception as e:
        send_telegram(f"Error with {symbol}: {str(e)}")

# تشغيل كل 5 دقائق
def run_bot():
    global SERVER_STARTED
    if not SERVER_STARTED:
        send_telegram("✅ تم تشغيل السيرفر بنجاح! البوت يعمل الآن 24/7")
        SERVER_STARTED = True

    while True:
        for symbol in symbols:
            scalping_strategy(symbol)
        time.sleep(300)  # انتظر 5 دقائق

# بدء البوت
if __name__ == '__main__':
    from threading import Thread
    Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=10000)

import requests
import time
import threading
import yfinance as yf
from flask import Flask
from datetime import datetime

# إعدادات البوت
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"

# الأدوات
symbols = {
    "GOLD": "GC=F",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "US30": "^DJI",
    "US100": "^NDX"
}

# إعداد Flask
app = Flask("")

@app.route("/")
def home():
    return "Scalping bot running!", 200

# إرسال رسالة إلى تيليجرام
def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("فشل في إرسال الرسالة:", e)

# دالة توليد إشارة
def get_signal(name, symbol):
    try:
        df = yf.download(symbol, period="2d", interval="5m")
        if df.empty or len(df) < 20:
            return f"[{name}] لا توجد بيانات كافية."

        df["SMA_fast"] = df["Close"].rolling(window=5).mean()
        df["SMA_slow"] = df["Close"].rolling(window=20).mean()

        if df["SMA_fast"].iloc[-2] < df["SMA_slow"].iloc[-2] and df["SMA_fast"].iloc[-1] > df["SMA_slow"].iloc[-1]:
            signal = "BUY"
        elif df["SMA_fast"].iloc[-2] > df["SMA_slow"].iloc[-2] and df["SMA_fast"].iloc[-1] < df["SMA_slow"].iloc[-1]:
            signal = "SELL"
        else:
            return None

        entry = round(df["Close"].iloc[-1], 2)
        tp = round(entry + 10, 2) if signal == "BUY" else round(entry - 10, 2)
        sl = round(entry - 10, 2) if signal == "BUY" else round(entry + 10, 2)

        return f"{signal} {name}\nدخول: {entry}\nTP: {tp}\nSL: {sl}"

    except Exception as e:
        error_msg = f"[{name}] خطأ أثناء التحميل: {str(e)}"
        send_to_telegram(error_msg)
        return None

# فحص جميع الأدوات
def check_all():
    print("✅ Running check at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    for name, symbol in symbols.items():
        try:
            result = get_signal(name, symbol)
            if result:
                send_to_telegram(result)
        except Exception as err:
            send_to_telegram(f"⚠️ خطأ غير متوقع في [{name}]: {str(err)}")

# التشغيل التلقائي كل 5 دقائق
def loop():
    while True:
        try:
            check_all()
        except Exception as e:
            send_to_telegram(f"❌ السكربت توقف بسبب خطأ: {str(e)}")
        time.sleep(300)

# تشغيل Flask و البوت
threading.Thread(target=loop).start()
app.run(host="0.0.0.0", port=81)

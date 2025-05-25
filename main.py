from flask import Flask
import requests
import yfinance as yf
import time
import traceback

app = Flask(__name__)

# إعدادات تيليجرام
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# قائمة الأدوات المالية
SYMBOLS = {
    "GOLD": "GC=F",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "US30": "^DJI",
    "US100": "^NDX"
}

# دالة إرسال رسالة إلى تيليجرام
def send_telegram_message(message):
    try:
        data = {"chat_id": CHAT_ID, "text": message}
        requests.post(TELEGRAM_API, data=data)
    except Exception as e:
        print("Telegram Error:", e)

# دالة فحص الإشارة لكل أداة
def check_signal(symbol_name, symbol_code):
    try:
        df = yf.download(symbol_code, interval="1m", period="2m")
        if df.empty or len(df) < 2:
            return

        df["EMA5"] = df["Close"].ewm(span=5, adjust=False).mean()
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()

        last = df.iloc[-1]
        previous = df.iloc[-2]

        if previous["EMA5"] < previous["EMA20"] and last["EMA5"] > last["EMA20"]:
            direction = "BUY"
        elif previous["EMA5"] > previous["EMA20"] and last["EMA5"] < last["EMA20"]:
            direction = "SELL"
        else:
            return

        entry = round(last["Close"], 2)
        tp = round(entry * 1.002, 2)
        sl = round(entry * 0.998, 2)

        message = (
            f"{direction} {symbol_name}\n"
            f"دخول: {entry}\n"
            f"الهدف (TP): {tp}\n"
            f"وقف الخسارة (SL): {sl}"
        )
        send_telegram_message(message)

    except Exception as e:
        error_message = f"Error with {symbol_name}: {str(e).splitlines()[0]}"
        send_telegram_message(error_message)
        print(traceback.format_exc())

# الصفحة الرئيسية للسيرفر
@app.route('/')
def home():
    return "Bot is running!"

# تشغيل البوت في حلقة كل 5 دقائق
def run_bot():
    send_telegram_message("✅ تم تشغيل السيرفر بنجاح! البوت يعمل الآن 24/7")
    while True:
        for name, code in SYMBOLS.items():
            check_signal(name, code)
            time.sleep(3)  # تأخير بسيط لتقليل الضغط على الواجهة
        time.sleep(300)  # إعادة كل 5 دقائق

if __name__ == '__main__':
    import threading
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=10000)

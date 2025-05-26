import os
import requests, time, threading
import pandas as pd
from datetime import datetime
from flask import Flask
from tvdatafeed import TvDatafeed, Interval
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# إعدادات البوت
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TWELVE_API_KEY = os.getenv("TWELVE_API_KEY")
TV_EMAIL = os.getenv("TV_EMAIL")
TV_PASSWORD = os.getenv("TV_PASSWORD")

# تسجيل الدخول في TradingView
tv = TvDatafeed(username=TV_EMAIL, password=TV_PASSWORD)

# إعداد التطبيق
app = Flask(__name__)

# أدوات التحليل
symbols = ['XAU/USD', 'BTC/USD', 'ETH/USD']
intervals = {'1min': Interval.in_1_minute, '15min': Interval.in_15_minute}

# دالة لجلب البيانات
def get_data(symbol, tf):
    try:
        data = tv.get_hist(symbol=symbol.replace("/", ""), exchange='OANDA', interval=intervals[tf], n_bars=100)
        if data is not None and not data.empty:
            return data
        else:
            raise ValueError("No data")
    except Exception as e:
        print(f"Error fetching {symbol} [{tf}]: {e}")
        return None

# تحليل البيانات وإرسال التوصيات
def analyze():
    for symbol in symbols:
        for tf in intervals:
            df = get_data(symbol, tf)
            if df is None:
                send_message(f"⚠️ لا توجد بيانات كافية لـ {symbol} على {tf}.")
                continue

            # مؤشرات SMA و MACD
            df['sma'] = df['close'].rolling(window=9).mean()
            df['macd'] = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()

            signal = ''
            if df['close'].iloc[-1] > df['sma'].iloc[-1] and df['macd'].iloc[-1] > 0:
                signal = 'BUY'
            elif df['close'].iloc[-1] < df['sma'].iloc[-1] and df['macd'].iloc[-1] < 0:
                signal = 'SELL'

            if signal:
                price = df['close'].iloc[-1]
                tp = round(price * 1.001, 2) if signal == 'BUY' else round(price * 0.999, 2)
                sl = round(price * 0.999, 2) if signal == 'BUY' else round(price * 1.001, 2)
                send_message(f"{signal} {symbol}\nنسبة نجاح متوقعة: %2\nدخول: {price}\nTP: {tp}\nSL: {sl}\nUTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

# إرسال رسالة تلغرام
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=payload)
    except:
        print("خطأ في إرسال الرسالة")

@app.route('/')
def index():
    return 'ScalpX Bot is Running!'

def run():
    while True:
        analyze()
        time.sleep(300)

if __name__ == '__main__':
    threading.Thread(target=run).start()
    app.run(host='0.0.0.0', port=10000)

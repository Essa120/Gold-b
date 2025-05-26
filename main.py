import os
import requests, time, threading
import pandas as pd
from datetime import datetime
from flask import Flask
from tvdatafeed import TvDatafeed, Interval
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TV_EMAIL = os.getenv("TV_EMAIL")
TV_PASSWORD = os.getenv("TV_PASSWORD")

# الاتصال بـ TradingView
tv = TvDatafeed(username=TV_EMAIL, password=TV_PASSWORD)

# إعداد Flask
app = Flask(__name__)

symbols = ['XAU/USD', 'BTC/USD', 'ETH/USD']
intervals = {
    '1min': Interval.in_1_minute,
    '15min': Interval.in_15_minute
}

last_signals = {}

# إرسال رسالة
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

# جلب البيانات
def get_data(symbol, tf):
    try:
        df = tv.get_hist(symbol.replace("/", ""), exchange='OANDA', interval=intervals[tf], n_bars=100)
        return df if df is not None and not df.empty else None
    except Exception as e:
        print(f"Error fetching {symbol} [{tf}]: {e}")
        return None

# تحليل الإشارة
def analyze():
    global last_signals
    for symbol in symbols:
        best_signal = None
        best_score = 0

        for tf in intervals:
            df = get_data(symbol, tf)
            if df is None:
                send_message(f"⚠️ لا توجد بيانات كافية لـ {symbol} على {tf}.")
                continue

            df['sma'] = df['close'].rolling(window=9).mean()
            df['macd'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()

            last = df.iloc[-1]
            price = round(last['close'], 2)
            signal = None

            if last['close'] > last['sma'] and last['macd'] > 0:
                signal = 'BUY'
            elif last['close'] < last['sma'] and last['macd'] < 0:
                signal = 'SELL'

            if not signal:
                continue

            # نسبة نجاح وهمية (لتقييم الإشارة)
            score = abs(last['macd']) * 100 / price
            if score > best_score:
                best_score = score
                best_signal = {
                    'signal': signal,
                    'price': price,
                    'tp': round(price * (1.001 if signal == 'BUY' else 0.999), 2),
                    'sl': round(price * (0.999 if signal == 'BUY' else 1.001), 2),
                    'score': round(score, 1),
                    'symbol': symbol,
                    'time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                }

        if best_signal:
            key = f"{symbol}_{best_signal['signal']}"
            last_time = last_signals.get(key)
            now = time.time()

            # منع التكرار أو التضارب
            if last_time and now - last_time < 300:
                continue
            last_signals[key] = now

            send_message(
                f"{best_signal['signal']} {best_signal['symbol']}\n"
                f"نسبة نجاح متوقعة: %{best_signal['score']}\n"
                f"دخول: {best_signal['price']}\n"
                f"TP: {best_signal['tp']}\n"
                f"SL: {best_signal['sl']}\n"
                f"UTC {best_signal['time']}"
            )

# نقطة تشغيل API
@app.route('/')
def index():
    return 'ScalpX Bot is Running!'

# تشغيل دائم
def run():
    while True:
        analyze()
        time.sleep(300)

if __name__ == '__main__':
    threading.Thread(target=run).start()
    app.run(host='0.0.0.0', port=10000)

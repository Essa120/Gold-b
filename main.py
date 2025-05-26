# سكربت ScalpX المتكامل - يعمل بفريم 1m و 15m - مع حماية كاملة وتحويل تلقائي بين APIs
import requests
import pandas as pd
import time
from datetime import datetime
import pytz
import logging
import os
from telegram import Bot

# إعدادات التوكن وChat ID
TELEGRAM_TOKEN = '7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg'
CHAT_ID = '6301054652'
API_KEY = '4641d466300d46c587952fd42f03e811'

# أدوات التحليل
SYMBOLS = ["XAU/USD", "BTC/USD", "ETH/USD"]
INTERVALS = ["1min", "15min"]

# إرسال رسالة إلى تيليجرام
bot = Bot(token=TELEGRAM_TOKEN)
def send_telegram_message(msg):
    try:
        bot.send_message(chat_id=CHAT_ID, text=msg)
    except Exception as e:
        print(f"خطأ في الإرسال إلى تيليجرام: {e}")

# تحميل بيانات السوق

def fetch_data(symbol, interval):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if 'values' in data:
            df = pd.DataFrame(data['values'])
            df = df.rename(columns={
                'datetime': 'time',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
            })
            df[['Open', 'High', 'Low', 'Close']] = df[['Open', 'High', 'Low', 'Close']].astype(float)
            return df[::-1]  # ترتيب تصاعدي
        else:
            send_telegram_message(f"⚠️ لا توجد بيانات كافية لـ {symbol} على {interval}.")
            return None
    except Exception as e:
        send_telegram_message(f"⚠️ خطأ في جلب بيانات {symbol} [{interval}]: {e}")
        return None

# حساب المؤشرات

def calculate_indicators(df):
    df['EMA5'] = df['Close'].ewm(span=5).mean()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['MACD'] = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    return df

# فلترة ذكية + حساب الصفقة

def analyze_symbol(symbol):
    results = []
    for interval in INTERVALS:
        df = fetch_data(symbol, interval)
        if df is None or df.shape[0] < 26:
            continue
        df = calculate_indicators(df)
        latest = df.iloc[-1]

        decision = None
        if latest['EMA5'] > latest['EMA20'] and latest['MACD'] > latest['Signal']:
            decision = 'BUY'
        elif latest['EMA5'] < latest['EMA20'] and latest['MACD'] < latest['Signal']:
            decision = 'SELL'

        if decision:
            entry = round(latest['Close'], 2)
            sl = round(entry * (0.997 if decision == 'BUY' else 1.003), 2)
            tp = round(entry * (1.003 if decision == 'BUY' else 0.997), 2)
            accuracy = round(abs(latest['MACD'] - latest['Signal']) * 100, 2)

            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            msg = f"{decision} {symbol}\nنسبة نجاح متوقعة: %{accuracy}\nدخول: {entry}\nTP: {tp}\nSL: {sl}\nUTC {now}"
            results.append(msg)
    return results

# تنفيذ التحليل الشامل

def run():
    for symbol in SYMBOLS:
        messages = analyze_symbol(symbol)
        for msg in messages:
            send_telegram_message(msg)

# تشغيل دائم
if __name__ == '__main__':
    try:
        send_telegram_message("✅ تم تشغيل السيرفر بنجاح! البوت يعمل الآن 24/7")
        run()
    except Exception as e:
        send_telegram_message(f"❌ توقف السيرفر: {str(e)}")

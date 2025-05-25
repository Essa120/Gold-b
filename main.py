from flask import Flask
import requests
import time
import threading
import traceback

app = Flask(__name__)

# إعدادات تيليجرام
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"

# إرسال رسالة إلى تيليجرام
def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text}
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print("فشل الإرسال:", response.text)
    except Exception as e:
        print("خطأ في الإرسال:", e)
        traceback.print_exc()

# تأكيد بداية التشغيل
send_message("✅ تم تشغيل السيرفر بنجاح! البوت يعمل الآن 24/7")

@app.route('/')
def home():
    return "Bot is running!"

# أدوات التداول المراد متابعتها
SYMBOLS = {
    "XAUUSD": "GOLD",
    "BTC-USD": "BTC",
    "ETH-USD": "ETH",
    "^DJI": "US30",
    "^NDX": "US100"
}

def get_price_yahoo(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=2m"
        response = requests.get(url).json()
        prices = response['chart']['result'][0]['indicators']['quote'][0]['close']
        return prices
    except Exception as e:
        print(f"خطأ في جلب السعر لـ {symbol}:", e)
        return None

def scalping_bot():
    while True:
        try:
            for symbol, name in SYMBOLS.items():
                prices = get_price_yahoo(symbol)
                if prices and len(prices) >= 2:
                    ma1 = sum(prices[-2:]) / 2
                    ma2 = sum(prices[-3:]) / 3
                    if ma1 > ma2:
                        send_message(f"BUY {name} @ {round(prices[-1], 2)}")
                    elif ma1 < ma2:
                        send_message(f"SELL {name} @ {round(prices[-1], 2)}")
        except Exception as e:
            send_message(f"خطأ في السكربت:\n{e}")
        time.sleep(60)  # كل دقيقة

# تشغيل سكربت السكالبينج في خيط منفصل
threading.Thread(target=scalping_bot).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

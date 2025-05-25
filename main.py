from flask import Flask
import requests
import traceback
import datetime
import threading
import time

app = Flask(__name__)

# إعدادات تيليجرام
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"

# دالة إرسال رسالة إلى تيليجرام
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    response = requests.post(url, data=data)
    return response.ok

# دالة تسجيل الأحداث في ملف log
def log_event(message):
    with open("log.txt", "a") as log:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"[{timestamp}] {message}\n")

# دالة توليد الإشارة وإرسالها بشرط ذكي
def check_and_send_signal():
    try:
        hour = datetime.datetime.now().hour
        if hour % 2 == 0:
            signal = "BUY GOLD @2350 - Smart Signal"
            if send_telegram_message(signal):
                log_event(f"Signal sent: {signal}")
            else:
                log_event("Failed to send signal.")
        else:
            log_event("No signal condition met.")
    except Exception as e:
        error_text = f"Error occurred:\n{traceback.format_exc()}"
        send_telegram_message("حدث خطأ في السكربت:\n" + str(e))
        log_event("Error: " + str(e))

# دالة تعمل في الخلفية بشكل دائم كل دقيقة
def run_background_scheduler():
    while True:
        check_and_send_signal()
        time.sleep(60)  # كل 60 ثانية

# تشغيل الخلفية مع السيرفر
@app.before_first_request
def activate_job():
    thread = threading.Thread(target=run_background_scheduler)
    thread.daemon = True
    thread.start()

# نقطة الفحص اليدوي
@app.route('/')
def home():
    return "Bot is running and sending signals automatically!"

# تشغيل السيرفر
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

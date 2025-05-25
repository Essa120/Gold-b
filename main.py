from flask import Flask
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# كود اختبار إرسال رسالة إلى تيليجرام
BOT_TOKEN = "7621940570:AAH4fS66qAJXn6h33AzRJK7Nk8tiIwwR_kg"
CHAT_ID = "6301054652"
TEXT = "تم إرسال هذه الرسالة بنجاح من Render!"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
data = {"chat_id": CHAT_ID, "text": TEXT}
requests.post(url, data=data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

from flask import Flask
import requests, os, threading, time

app = Flask(__name__)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7884780716")

def send_tg(msg):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
        print("TG STATUS:", r.status_code, r.text[:500])
    except Exception as e:
        print("TG error", e)

@app.route("/")
def home():
    send_tg("✅ TEST REUSSI - Le bot arrive à envoyer sur Telegram")
    return "TEST ENVOYE - Regarde Telegram"

@app.route("/test")
def test():
    send_tg("✅ TEST /test - Ca marche")
    return "TEST OK"

if __name__ == "__main__":
    time.sleep(3)
    send_tg("🤖 BOT TEST DEMARRE - Si tu recois ca, Telegram marche")
    app.run(host="0.0.0.0", port=10000)

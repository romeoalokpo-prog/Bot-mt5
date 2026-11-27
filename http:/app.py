from flask import Flask, jsonify, request
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "BOT MT5 EN LIGNE - Pret a trader"

@app.route('/status')
def status():
    return jsonify({
        "status": "online",
        "bot": "Bot-mt5",
        "metaapi_token": "OK" if os.getenv("METAAPI_TOKEN") else "MANQUANT",
        "account_id": "OK" if os.getenv("METAAPI_ACCOUNT_ID") else "MANQUANT"
    })

@app.route('/trade', methods=['POST'])
def trade():
    data = request.json or {}
    return jsonify({"message": "Signal recu", "data": data})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

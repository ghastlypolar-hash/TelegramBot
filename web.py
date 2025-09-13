from flask import Flask, request
import os
from bot import app as telegram_app  # reuse your Application instance

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot running"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    telegram_app.update_queue.put_nowait(update)  # pass update to bot
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

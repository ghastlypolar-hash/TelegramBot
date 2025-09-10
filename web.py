from flask import Flask
import subprocess
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot running"

if __name__ == "__main__":
    # Start the Telegram bot in the background
    subprocess.Popen(["python", "bot.py"])
    # Start the Flask web server
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

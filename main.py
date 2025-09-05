import requests
import json
import schedule
import time
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "8382132782:AAEUK3WKhF7HzNlvOLVhl51O500JEE5u8Lg"
WATCHLIST_FILE = "watchlist.json"
CHECK_INTERVAL = 20  # minutes

# Load or initialize watchlists (per user)
try:
    with open(WATCHLIST_FILE, "r") as f:
        watchlists = json.load(f)
except FileNotFoundError:
    watchlists = {}

# Save watchlists
def save_watchlists():
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(watchlists, f)

# Check Instagram account status
def check_account_status(username):
    profile_url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        r = requests.get(profile_url, headers=headers, timeout=10)
        page_text = r.text.lower()

        # Case 1: Direct 404 response
        if r.status_code == 404:
            return "BANNED / NOT FOUND"

        # Case 2: Known unavailable phrases
        unavailable_phrases = [
            "sorry, this page isn't available",
            "the link you followed may be broken",
            "page may have been removed",
            "page isn&#39;t available"
        ]
        if any(phrase in page_text for phrase in unavailable_phrases):
            return "BANNED / SUSPENDED"

        # Case 3: Check if page contains Instagram profile metadata
        if 'og:title' not in page_text and 'profilepage_' not in page_text:
            return "BANNED / SUSPENDED"

        # ✅ If reached here → profile exists
        return "ACTIVE"

    except Exception as e:
        return f"ERROR: {e}"

# Telegram commands
async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id not in watchlists:
        watchlists[chat_id] = []
    if not context.args:
        await update.message.reply_text("Usage: /add username")
        return
    username = context.args[0].lower()
    if username not in watchlists[chat_id]:
        watchlists[chat_id].append(username)
        save_watchlists()
        await update.message.reply_text(f"✅ Added {username} to your watchlist.")
    else:
        await update.message.reply_text(f"{username} is already in your watchlist.")

async def remove_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id not in watchlists:
        watchlists[chat_id] = []
    if not context.args:
        await update.message.reply_text("Usage: /remove username")
        return
    username = context.args[0].lower()
    if username in watchlists[chat_id]:
        watchlists[chat_id].remove(username)
        save_watchlists()
        await update.message.reply_text(f"❌ Removed {username} from your watchlist.")
    else:
        await update.message.reply_text(f"{username} not found in your watchlist.")

async def list_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id not in watchlists or not watchlists[chat_id]:
        await update.message.reply_text("📭 Your watchlist is empty.")
    else:
        await update.message.reply_text("📌 Your Watchlist:\n" + "\n".join(watchlists[chat_id]))

async def check_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /check username")
        return
    username = context.args[0].lower()
    status = check_account_status(username)
    await update.message.reply_text(f"🔎 {username} → {status}")

# Background monitoring
async def monitor_accounts(application):
    for chat_id, usernames in watchlists.items():
        for username in usernames:
            status = check_account_status(username)
            if status != "ACTIVE":
                await application.bot.send_message(
                    chat_id=int(chat_id),
                    text=f"⚠ ALERT: {username} is {status}"
                )

# Store chat IDs whenever someone interacts with the bot
async def register_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if "chat_ids" not in context.application.bot_data:
        context.application.bot_data["chat_ids"] = []
    if chat_id not in context.application.bot_data["chat_ids"]:
        context.application.bot_data["chat_ids"].append(chat_id)


def run_scheduler(application):
    while True:
        schedule.run_pending()
        time.sleep(1)


# Main
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Handlers
app.add_handler(CommandHandler("add", add_account))
app.add_handler(CommandHandler("remove", remove_account))
app.add_handler(CommandHandler("list", list_accounts))
app.add_handler(CommandHandler("check", check_account))
app.add_handler(CommandHandler("start", register_chat))  # registers chat automatically

# Always monitor in background
schedule.every(CHECK_INTERVAL).minutes.do(
    lambda: app.create_task(monitor_accounts(app))
)

# Run scheduler in separate thread
threading.Thread(target=run_scheduler, args=(app,), daemon=True).start()

if __name__ == "__main__":
    app.run_polling()

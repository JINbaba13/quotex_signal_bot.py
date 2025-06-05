import requests
from telegram import Bot, ParseMode
from datetime import datetime
import time
import os

BOT_API_TOKEN = os.getenv("BOT_API_TOKEN")
USER_ID = os.getenv("USER_ID")
API_KEY = os.getenv("API_KEY")

PAIRS = ["BTC/USD", "ETH/USD", "EUR/USD", "GBP/USD", "USD/JPY"]
ROTATION_FILE = "pair_rotation.txt"

bot = Bot(token=BOT_API_TOKEN)

def fetch_price(symbol):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=1&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if "status" in data and data["status"] == "error":
        print(f"❌ API error for {symbol}: {data}")
        return None
    try:
        price = float(data["values"][0]["close"])
        return price
    except:
        print(f"⚠️ Data error for {symbol}: {data}")
        return None

def generate_signal(symbol):
    price = fetch_price(symbol)
    if price is None:
        return None, 0
    if price > 50000:  # Placeholder logic
        return "BUY", 10
    else:
        return "SELL", 9

def send_signal(symbol, signal, score):
    now = datetime.now().strftime("%H:%M:%S")
    message = f"📊 Signal for *{symbol}*\n⏰ Time: *{now}* France time\n📈 Signal: *{signal}* | Score: *{score}/10*"
    bot.send_message(chat_id=USER_ID, text=message, parse_mode=ParseMode.MARKDOWN)

def get_next_pair():
    index = 0
    if os.path.exists(ROTATION_FILE):
        with open(ROTATION_FILE, "r") as f:
            index = int(f.read().strip())
    next_pair = PAIRS[index % len(PAIRS)]
    with open(ROTATION_FILE, "w") as f:
        f.write(str((index + 1) % len(PAIRS)))
    return next_pair

def main():
    symbol = get_next_pair()
    print(f"⏰ Checking {symbol} at {datetime.now().strftime('%H:%M:%S')} France time...")
    signal, score = generate_signal(symbol)
    if signal and score >= 9:
        send_signal(symbol, signal, score)
    else:
        print(f"⚠️ No strong signal for {symbol} (Score: {score}/10)")

if __name__ == "__main__":
    main()

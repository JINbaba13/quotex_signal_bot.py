import requests
from telegram import Bot, ParseMode
from datetime import datetime, timedelta
import pytz  # for timezone conversion

# ✅ Environment variables (from GitHub secrets)
import os
BOT_API_TOKEN = os.getenv("BOT_API_TOKEN")
USER_ID = os.getenv("USER_ID")
API_KEY = os.getenv("API_KEY")

# ✅ Telegram bot setup
bot = Bot(token=BOT_API_TOKEN)

# ✅ Timezone setup (France time)
france_tz = pytz.timezone("Europe/Paris")

# ✅ Fetch latest price
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
    except (KeyError, IndexError, ValueError):
        print(f"⚠️ Data format error: {data}")
        return None

# ✅ Signal generation logic (placeholder)
def generate_signal(symbol):
    price = fetch_price(symbol)
    if price is None:
        return None, 0

    # Example logic (you can replace with indicators)
    if price > 50000:
        return "BUY", 10
    elif price > 1000:
        return "SELL", 9
    else:
        return None, 0

# ✅ Send signal to Telegram
def send_signal(symbol, signal, score):
    france_time = datetime.now(france_tz).strftime("%H:%M:%S")
    message = (
        f"📊 Signal for *{symbol}*\n"
        f"⏰ Time: *{france_time}* France time\n"
        f"📈 Signal: *{signal}* | Score: *{score}/10*\n"
        f"🕐 Trade this on the next 5-minute candle!"
    )
    bot.send_message(chat_id=USER_ID, text=message, parse_mode=ParseMode.MARKDOWN)

# ✅ Main logic
def main():
    symbols = ["BTC/USD", "ETH/USD", "EUR/USD", "GBP/USD", "USD/JPY"]
    top_signal = None

    for symbol in symbols:
        signal, score = generate_signal(symbol)
        if signal and score >= 9:
            if not top_signal or score > top_signal["score"]:
                top_signal = {"symbol": symbol, "signal": signal, "score": score}

    if top_signal:
        send_signal(top_signal["symbol"], top_signal["signal"], top_signal["score"])
    else:
        print("❌ No strong signal (Score < 9)")

if __name__ == "__main__":
    main()

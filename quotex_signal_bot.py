import asyncio
import datetime
import pytz
import requests
from telegram import Bot
from telegram.constants import ParseMode
import pandas as pd

# === CONFIGURATION ===
BOT_API_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
USER_ID = "YOUR_TELEGRAM_USER_ID"
API_KEY = "YOUR_TWELVEDATA_API_KEY"

PAIRS = ['BTC/USD', 'ETH/USD', 'EUR/USD', 'GBP/USD', 'USD/JPY']
INTERVAL = "1min"
TIMEZONE = pytz.timezone("Europe/Paris")

bot = Bot(token=BOT_API_TOKEN)

# === GET SIGNAL FUNCTION (based on candle 3 minutes ago) ===
def get_signal(pair):
    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval={INTERVAL}&apikey={API_KEY}&outputsize=5"
    response = requests.get(url).json()

    if 'status' in response and response['status'] == 'error':
        print(f"❌ API response error for {pair}: {response}")
        return 0, None

    try:
        df = pd.DataFrame(response['values'])
        df['close'] = df['close'].astype(float)
        df['open'] = df['open'].astype(float)

        # Get candle from 3 minutes ago and 4 minutes ago
        last = df.iloc[2]
        second_last = df.iloc[3]

        bullish = last['close'] > last['open'] and second_last['close'] > second_last['open']
        bearish = last['close'] < last['open'] and second_last['close'] < second_last['open']

        if bullish:
            return 9, "BUY"
        elif bearish:
            return 9, "SELL"
        else:
            return 5, None
    except Exception as e:
        print(f"⚠️ Error processing data for {pair}: {e}")
        return 0, None

# === SEND SIGNAL ===
async def send_signal(pair, signal, score):
    now = datetime.datetime.now(TIMEZONE)
    signal_time = now + datetime.timedelta(minutes=3)
    formatted_time = signal_time.strftime("%H:%M")  # Remove seconds
    message = f"""📊 Signal for {pair}
⏰ Trade at: {formatted_time} France time
📈 Signal: {signal} | Score: {score}/10"""
    await bot.send_message(chat_id=USER_ID, text=message, parse_mode=ParseMode.MARKDOWN)

# === MAIN LOGIC ===
async def run_signal_check():
    for pair in PAIRS:
        print(f"🔍 Checking {pair}...")
        score, signal = get_signal(pair)
        if score >= 9 and signal:
            await send_signal(pair, signal, score)
            print(f"✅ Signal sent for {pair}: {signal} ({score}/10)")
            await asyncio.sleep(5)  # Wait 5 seconds between signals
        else:
            print(f"⚠️ No valid signal for {pair} (Score: {score}/10)")

# === REPEAT EVERY 5 MINUTES ===
async def run_loop():
    while True:
        print("🔁 Checking signals...")
        await run_signal_check()
        print("⏳ Waiting 5 minutes...")
        await asyncio.sleep(300)  # 5 minutes delay

# === RUN SCRIPT ===
if __name__ == "__main__":
    asyncio.run(run_loop())

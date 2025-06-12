import asyncio
import datetime
import pytz
import requests
import pandas as pd
from telegram import Bot, constants

# === CONFIGURATION ===
BOT_API_TOKEN = "7636996493:AAEa9ddt4okvNj2RyeWGPemvN3NDsQ_wXCc"
USER_ID = "7989610604"
API_KEY = "2bbdaeca1e7e4010a0833015a50350e8"

PAIRS = ['BTC/USD', 'ETH/USD', 'EUR/USD', 'GBP/USD', 'USD/JPY']
INTERVAL = "1min"
TIMEZONE = pytz.timezone("Europe/Paris")

# Dictionary to track sent signals with timestamp
sent_signals = {}

# === GET SIGNAL FUNCTION ===
def get_signal(pair):
    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval={INTERVAL}&apikey={API_KEY}&outputsize=5"
    response = requests.get(url).json()

    if 'status' in response and response['status'] == 'error':
        print(f"❌ API error for {pair}: {response}")
        return 0, None

    try:
        df = pd.DataFrame(response['values'])
        df['close'] = df['close'].astype(float)
        df['open'] = df['open'].astype(float)

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
        print(f"⚠️ Data error for {pair}: {e}")
        return 0, None

# === SEND SIGNAL FUNCTION ===
async def send_signal(bot, pair, signal, score, signal_time):
    formatted_time = signal_time.strftime("%H:%M")
    message = f"""📊 Signal for {pair}
⏰ Trade at: {formatted_time} France time
📈 Signal: {signal} | Score: {score}/10"""
    await bot.send_message(chat_id=USER_ID, text=message, parse_mode=constants.ParseMode.MARKDOWN)

# === MAIN LOGIC ===
async def run_signal_check(bot):
    now = datetime.datetime.now(TIMEZONE)

    for pair in PAIRS:
        score, signal = get_signal(pair)
        if score >= 9 and signal:
            proposed_trade_time = (now + datetime.timedelta(minutes=3)).strftime('%H:%M')

            signal_key = f"{pair}_{signal}_{proposed_trade_time}"

            # Check if signal was already sent
            if signal_key not in sent_signals:
                await send_signal(bot, pair, signal, score, now + datetime.timedelta(minutes=3))
                sent_signals[signal_key] = time_now := datetime.datetime.now().timestamp()
                print(f"✅ Signal sent for {pair} at {proposed_trade_time}")

                # Clean up signals older than 10 minutes
                expire_before = datetime.datetime.now().timestamp() - 600
                sent_signals_copy = sent_signals.copy()
                for k, v in sent_signals_copy.items():
                    if v < expire_before:
                        del sent_signals[k]

                await asyncio.sleep(5)
                break  # Optional: limit to one signal per check
            else:
                print(f"⏳ Skipping {pair} – Duplicate signal already sent for {proposed_trade_time}")
        else:
            print(f"❌ No signal for {pair}")

# === REPEATING LOOP ===
async def run_loop(bot):
    while True:
        await run_signal_check(bot)
        await asyncio.sleep(60)

# === ENTRY POINT ===
async def main():
    bot = Bot(token=BOT_API_TOKEN)
    await run_loop(bot)

if __name__ == "__main__":
    asyncio.run(main())

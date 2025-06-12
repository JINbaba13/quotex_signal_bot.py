import asyncio
import datetime
import pytz
import requests
import pandas as pd
from telegram import Bot, constants

# === CONFIG ===
BOT_API_TOKEN = "7636996493:AAEa9ddt4okvNj2RyeWGPemvN3NDsQ_wXCc"
USER_ID = "7989610604"
API_KEY = "2bbdaeca1e7e4010a0833015a50350e8"

PAIRS = ['BTC/USD', 'ETH/USD', 'EUR/USD', 'GBP/USD', 'USD/JPY']
INTERVAL = "1min"
TIMEZONE = pytz.timezone("Europe/Paris")

sent_signals = {}

def round_time_to_5_minutes(dt):
    discard = datetime.timedelta(minutes=dt.minute % 5,
                                 seconds=dt.second,
                                 microseconds=dt.microsecond)
    return dt - discard + datetime.timedelta(minutes=5)

def get_signal(pair):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval={INTERVAL}&apikey={API_KEY}&outputsize=5"
        response = requests.get(url).json()

        if 'status' in response and response['status'] == 'error':
            print(f"❌ API error for {pair}: {response}")
            return 0, None

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
        print(f"⚠️ Error in get_signal() for {pair}: {e}")
        return 0, None

async def send_signal(bot, pair, signal, score, signal_time):
    try:
        formatted_time = signal_time.strftime("%H:%M")
        message = f"""📊 Signal for {pair}
⏰ Trade at: {formatted_time} France time
📈 Signal: {signal} | Score: {score}/10"""
        await bot.send_message(chat_id=USER_ID, text=message, parse_mode=constants.ParseMode.MARKDOWN)
        print(f"✅ Telegram sent: {pair} - {signal} at {formatted_time}")
    except Exception as e:
        print(f"❌ Failed to send message: {e}")

async def run_signal_check(bot):
    now = datetime.datetime.now(TIMEZONE)

    for pair in PAIRS:
        score, signal = get_signal(pair)
        print(f"📈 Checked {pair} => Score: {score}, Signal: {signal}")

        if signal:
            rounded_time = round_time_to_5_minutes(now).strftime('%H:%M')
            signal_key = f"{pair}_{signal}_{rounded_time}"

            if signal_key not in sent_signals:
                await send_signal(bot, pair, signal, score, round_time_to_5_minutes(now))
                sent_signals[signal_key] = datetime.datetime.now().timestamp()
                print(f"🟢 Stored signal key: {signal_key}")
                break
            else:
                print(f"⏳ Skipping duplicate signal for {signal_key}")
        else:
            print(f"❌ No signal for {pair}")

async def run_loop(bot):
    while True:
        print(f"🔁 Checking for signals at {datetime.datetime.now(TIMEZONE).strftime('%H:%M:%S')}")
        await run_signal_check(bot)
        await asyncio.sleep(60)

async def main():
    bot = Bot(token=BOT_API_TOKEN)

    # ✅ Bot start confirmation
    await bot.send_message(chat_id=USER_ID, text="✅ Bot started and ready to send signals!")
    print("✅ Startup message sent.")

    # ✅ Forced test signal
    now = datetime.datetime.now(TIMEZONE)
    test_time = round_time_to_5_minutes(now)
    await send_signal(bot, "BTC/USD", "BUY", 9, test_time)
    print("✅ Test signal forced (BTC/USD BUY)")

    await asyncio.sleep(3)
    await run_loop(bot)

if __name__ == "__main__":
    asyncio.run(main())

import requests
import time
import datetime
import pytz
import winsound
from statistics import mean, stdev

# === CONFIGURATION ===
BOT_API_TOKEN = "7636996493:AAEa9ddt4okvNj2RyeWGPemvN3NDsQ_wXCc"
USER_ID = "7989610604"
API_KEY = "2bbdaeca1e7e4010a0833015a50350e8"

symbols = ["EUR/USD", "USD/JPY", "GBP/USD", "BTC/USD", "ETH/USD"]

def calculate_ema(prices, period):
    k = 2 / (period + 1)
    ema = prices[0]
    for price in prices[1:]:
        ema = price * k + ema * (1 - k)
    return ema

def calculate_rsi(prices, period=14):
    gains = []
    losses = []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))
    if len(gains) < period:
        return 50
    avg_gain = mean(gains[-period:])
    avg_loss = mean(losses[-period:])
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd(prices, fast=12, slow=26, signal_period=9):
    if len(prices) < slow + signal_period:
        return 0, 0, 0
    ema_fast = calculate_ema(prices[-fast:], fast)
    ema_slow = calculate_ema(prices[-slow:], slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(prices[-signal_period:], signal_period)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(prices, period=20):
    if len(prices) < period:
        return None, None, None
    mid = mean(prices[-period:])
    std_dev = stdev(prices[-period:])
    upper = mid + (2 * std_dev)
    lower = mid - (2 * std_dev)
    return lower, mid, upper

def get_france_time():
    utc_now = datetime.datetime.utcnow()
    france_tz = pytz.timezone('Europe/Paris')
    return utc_now.replace(tzinfo=pytz.utc).astimezone(france_tz)

def fetch_price_data(symbol):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=100&apikey={API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if "values" not in data:
            print(f"❌ API error for {symbol}: {data.get('message', 'No values returned')}")
            return []
        closes = [float(entry["close"]) for entry in reversed(data["values"])]
        return closes
    except Exception as e:
        print("❌ Error fetching price data:", e)
        return []

def generate_signal(prices):
    if len(prices) < 30:
        return None, 0

    ema5 = calculate_ema(prices[-5:], 5)
    ema10 = calculate_ema(prices[-10:], 10)
    rsi = calculate_rsi(prices)
    macd, signal, hist = calculate_macd(prices)
    lower_band, middle_band, upper_band = calculate_bollinger_bands(prices)

    latest_price = prices[-1]
    score = 0

    # EMA
    if ema5 > ema10:
        score += 2
    elif ema5 < ema10:
        score -= 2

    # RSI
    if 50 < rsi < 70:
        score += 2
    elif 30 < rsi <= 50:
        score -= 1

    # MACD
    if macd > signal and hist > 0:
        score += 4
    elif macd < signal and hist < 0:
        score -= 2

    # Bollinger Bands
    if latest_price < lower_band:
        score += 2
    elif latest_price > upper_band:
        score -= 2

    # Final Signal Logic
    if score >= 7:
        return "CALL", score
    elif score <= -7:
        return "PUT", abs(score)
    elif 5 <= score < 7:
        return "WEAK CALL", score
    elif -7 < score <= -5:
        return "WEAK PUT", abs(score)

    return None, score

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_API_TOKEN}/sendMessage"
    payload = {'chat_id': USER_ID, 'text': message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("❌ Telegram send error:", e)

def save_signal_to_file(message):
    try:
        with open("signals.txt", "a") as file:
            file.write(message + "\n")
    except Exception as e:
        print("❌ File write error:", e)

def play_sound():
    try:
        winsound.PlaySound("notification_sound.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        print("❌ Sound error:", e)

# === MAIN LOOP ===

print("🟢 Enhanced Smart Signal Bot started...\n")

interval_minutes = 3
pair_index = 0

while True:
    now = get_france_time()
    if now.second < 3:
        symbol = symbols[pair_index % len(symbols)]
        print(f"📊 Checking {symbol} at {now.strftime('%H:%M:%S')}...")
        prices = fetch_price_data(symbol)
        signal, score = generate_signal(prices)

        if signal:
            trade_time = now + datetime.timedelta(minutes=5)
            time_str = trade_time.strftime("%H:%M")
            message = f"{time_str}  {symbol}  {signal} (Score: {score}/12)"
            send_telegram_message(message)
            save_signal_to_file(message)
            play_sound()
            print("✅ Signal sent:", message)
        else:
            print(f"⚠️ No valid signal for {symbol} (Score: {score}/12)")

        pair_index += 1
        time.sleep(interval_minutes * 60)
    else:
        time.sleep(1)

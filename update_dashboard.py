import os
import requests
import csv
from io import StringIO
from datetime import datetime
from pytrends.request import TrendReq
from twilio.rest import Client

# Twilio credentials from GitHub Secrets
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
PHONE_NUMBER       = os.getenv("PHONE_NUMBER")

# Thresholds
THRESHOLDS = {
    "Log Upper Band": 1,
    "30d HODL Wave": 15.0,
    "Funding Rate": 0.10,
    "Google Trends": 80
    # TODO: add MVRV Z-Score threshold once API source is available
}

# Logarithmic Growth Curve (LookIntoBitcoin)
def get_log_growth_bands():
    url = "https://api.lookintobitcoin.com/indicators/logarithmic-growth-curve"
    data = requests.get(url).json()
    latest = data["chart"]["series"][-1]
    price      = float(latest["price"])
    upper_band = float(latest["upper"])
    return price, upper_band

# HODL Wave (Glassnode free endpoint)
def get_hodl_wave_30d():
    url = "https://api.glassnode.com/v1/metrics/indicators/hodl_waves"
    params = {"a": "BTC", "i": "24h", "api_key": ""}
    data = requests.get(url, params=params).json()
    return float(data[-1]['30d_90d'])

# Perpetual funding rate (Binance)
def get_funding_rate():
    url = "https://fapi.binance.com/fapi/v1/fundingRate"
    params = {"symbol": "BTCUSDT", "limit": 1}
    data = requests.get(url, params=params).json()
    return float(data[0]["fundingRate"])

# Google Trends (past 7 days)
def get_google_trends():
    pytrends = TrendReq()
    pytrends.build_payload(["bitcoin"], timeframe="now 7-d")
    data = pytrends.interest_over_time()
    return int(data["bitcoin"][-1]) if not data.empty else 0

# Generate the dashboard HTML
def generate_html(data_dict):
    html = """
    <html>
    <head>
      <title>Bitcoin Cycle Dashboard</title>
      <style>
        body { font-family: Arial, sans-serif; }
        table { border-collapse: collapse; width: 80%; margin:auto; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
        th { background-color: #f2f2f2; }
      </style>
    </head>
    <body>
      <h2 style="text-align:center;">Bitcoin Cycle Dashboard</h2>
      <table>
        <tr><th>Indicator</th><th>Reading</th><th>Threshold</th></tr>
    """
    for name, value in data_dict.items():
        thresh = THRESHOLDS.get(name, "—")
        html += f"<tr><td>{name}</td><td>{value}</td><td>{thresh}</td></tr>"
    html += f"""
      </table>
      <p style="text-align:center;">Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
    </body>
    </html>
    """
    with open("index.html", "w") as f:
        f.write(html)

def send_sms_alert(message):
    if all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, PHONE_NUMBER]):
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(body=message, from_=TWILIO_FROM_NUMBER, to=PHONE_NUMBER)

def main():
    price, log_upper = get_log_growth_bands()
    hodl30 = get_hodl_wave_30d()
    funding = get_funding_rate()
    trends = get_google_trends()

    data = {
        "Log Upper Band": int(price > log_upper),
        "30d HODL Wave": hodl30,
        "Funding Rate": funding,
        "Google Trends": trends
        # MVRV Z-Score will be added here once accessible via API
    }

    generate_html(data)

    triggered = [f"{k} = {v}" for k, v in data.items()
                 if THRESHOLDS.get(k) and v > THRESHOLDS[k]]

    if triggered:
        send_sms_alert("⚠️ Bitcoin Indicator Alert:\n" + "\n".join(triggered))

if __name__ == "__main__":
    main()

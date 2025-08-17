import os
import requests
from datetime import datetime
from pytrends.request import TrendReq
from twilio.rest import Client

# --------------------------------
# Credentials (from GitHub secrets)
# --------------------------------
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
PHONE_NUMBER       = os.getenv("PHONE_NUMBER")
CQ_API_KEY         = os.getenv("CRYPTOQUANT_API_KEY")

BASE_URL = "https://api.cryptoquant.com"

# --------------------------------------------
# Thresholds (alerts trigger if value > threshold)
# --------------------------------------------
THRESHOLDS = {
    "MVRV Z-Score": 7.0,
    "Puell Multiple": 4.0,
    "30d HODL Wave": 15.0,
    "Funding Rate": 0.10,
    "Google Trends": 80
}

# --------------------------------
#  API Functions
# --------------------------------

# NOTE: using 1d window because 1h is not accessible on Pro plan
def get_mvrv_zscore():
    endpoint = "/v2/bitcoin/market-mvrv-zscore?window=1d"
    headers = {"x-api-key": CQ_API_KEY}
    response = requests.get(BASE_URL + endpoint, headers=headers).json()
    return float(response["data"][-1]["value"])

def get_puell_multiple():
    endpoint = "/v2/bitcoin/miner-puell-multiple?window=1d"
    headers = {"x-api-key": CQ_API_KEY}
    response = requests.get(BASE_URL + endpoint, headers=headers).json()
    return float(response["data"][-1]["value"])

# 1h still ok for HODL wave
def get_hodl_wave_30d():
    endpoint = "/v2/bitcoin/flow-ageband?window=1h"
    headers = {"x-api-key": CQ_API_KEY}
    data = requests.get(BASE_URL + endpoint, headers=headers).json()
    return float(data["data"][-1]["30d-90d"])

def get_funding_rate():
    url = "https://fapi.binance.com/fapi/v1/fundingRate"
    params = {"symbol":"BTCUSDT","limit":1}
    data = requests.get(url, params=params).json()
    return float(data[0]["fundingRate"])

def get_google_trends():
    pytrends = TrendReq()
    pytrends.build_payload(["bitcoin"], timeframe="now 7-d")
    data = pytrends.interest_over_time()
    return int(data["bitcoin"][-1]) if not data.empty else 0

# --------------------------------
#  HTML Output
# --------------------------------

def generate_html(data_dict):
    html = """
    <html>
    <head>
      <title>Bitcoin Cycle Dashboard</title>
      <style>
        body  { font-family: Arial,sans-serif; }
        table { border-collapse: collapse; width: 80%; margin:auto; }
        th,td { border:1px solid #ccc; padding:8px; text-align:center; }
        th    { background:#f2f2f2; }
      </style>
    </head>
    <body>
      <h2 style="text-align:center;">Bitcoin Cycle Dashboard</h2>
      <table>
        <tr><th>Indicator</th><th>Reading</th><th>Threshold</th></tr>
    """
    for name,value in data_dict.items():
        thresh = THRESHOLDS.get(name,"—")
        html  += f"<tr><td>{name}</td><td>{value}</td><td>{thresh}</td></tr>"
    html += f"""
      </table>
      <p style="text-align:center;">Last updated: {
             datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
    </body>
    </html>"""

    repo_root = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(repo_root, "index.html")
    with open(html_path, "w") as f:
        f.write(html)

# --------------------------------
#  Main Workflow
# --------------------------------

def main():
    mvrv   = get_mvrv_zscore()
    puell  = get_puell_multiple()
    hodl30 = get_hodl_wave_30d()
    fund   = get_funding_rate()
    trend  = get_google_trends()

    data = {
        "MVRV Z-Score":  mvrv,
        "Puell Multiple": puell,
        "30d HODL Wave":  hodl30,
        "Funding Rate":   fund,
        "Google Trends":  trend
    }

    generate_html(data)

    triggered = [f"{k} = {v}" for k,v in data.items()
                 if THRESHOLDS.get(k) and v > THRESHOLDS[k]]
    if triggered:
        Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN).messages.create(
            body="⚠️ Bitcoin Indicator Alert:\n" + "\n".join(triggered),
            from_=TWILIO_FROM_NUMBER,
            to=PHONE_NUMBER
        )

if __name__ == "__main__":
    main()

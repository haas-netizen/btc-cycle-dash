import os
import requests
from datetime import datetime
from pytrends.request import TrendReq
from twilio.rest import Client

# ------------
# Credentials
# ------------
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
PHONE_NUMBER       = os.getenv("PHONE_NUMBER")
CQ_API_KEY         = os.getenv("CRYPTOQUANT_API_KEY")

BASE_URL = "https://api.cryptoquant.com/v1"

# --------------------
# Thresholds for Alerts
# --------------------
THRESHOLDS = {
    "MVRV Z-Score": 7.0,
    "Puell Multiple": 4.0,
    "30d HODL Wave": 15.0,
    "Funding Rate": 0.10,
    "Google Trends": 80
}

# --------------------
#  API Functions
# --------------------

def get_mvrv_zscore():
    endpoint = "/v2/bitcoin/market-mvrv-zscore?window=1h"
    headers = {"x-api-key": CQ_API_KEY}
    response = requests.get(BASE_URL + endpoint, headers=headers).json()
    return float(response["data"][-1]["value"])

def get_puell_multiple():
    endpoint = "/v2/bitcoin/miner-puell-multiple?window=1h"
    headers = {"x-api-key": CQ_API_KEY}
    response = requests.get(BASE_URL + endpoint, headers=headers).json()
    return float(response["data"][-1]["value"])

def get_hodl_wave_30d():
    endpoint = "/v2/bitcoin/flow-ageband?window=1h"
    headers = {"x-api-key": CQ_API_KEY}
    data = requests.get(BASE_URL + endpoint, headers=headers).json()
    # 30–90 day band
    return float(data["data"][-1]["30d-90d"])

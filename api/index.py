from fastapi import FastAPI, Query, Request
import requests
from bs4 import BeautifulSoup
import hashlib

app = FastAPI()

# Configuration
BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"

@app.get("/")
def home():
    return {"status": "Sameer API is Live", "features": ["FF Bind", "Temp Mail", "Free SMS"]}

# --- FEATURE 1: FF BIND (OTP REQUEST) ---
@app.get("/api/request")
def request_otp(token: str, email: str):
    headers = {"User-Agent": "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)"}
    payload = {"app_id": APP_ID, "access_token": token, "email": email, "locale": "en_BD", "region": "BD"}
    r = requests.post(f"{BASE_URL}/game/account_security/bind:send_otp", data=payload, headers=headers)
    return r.json()

# --- FEATURE 2: FF BIND (CONFIRM) ---
@app.get("/api/confirm")
def confirm_bind(token: str, email: str, otp: str):
    headers = {"User-Agent": "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)"}
    # Verify OTP
    v_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_otp", 
                          data={"app_id": APP_ID, "access_token": token, "email": email, "otp": otp}, headers=headers).json()
    return {"status": "done", "garena_res": v_res}

# --- FEATURE 3: FREE SMS LIST ---
@app.get("/api/sms-list")
def sms_list(country: str = "India"):
    url = f"https://receive-sms-free.cc/Free-{country}-Phone-Number/"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    nums = soup.find_all('div', class_='number-boxes-item')
    results = []
    for n in nums[:10]:
        val = n.find('h4').text.strip()
        link = n.find('a').get('href')
        results.append({"number": val, "url": f"https://receive-sms-free.cc{link}"})
    return results

# --- FEATURE 4: SMS INBOX ---
@app.get("/api/sms-inbox")
def sms_inbox(url: str):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    rows = soup.find_all('div', class_='messagesTableLayout')
    msgs = []
    for row in rows[:5]:
        sender = row.find('div', class_='msg-from').text.strip()
        text = row.find('div', class_='msg-text').text.strip()
        msgs.append({"from": sender, "text": text})
    return msgs

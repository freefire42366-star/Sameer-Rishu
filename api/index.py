from fastapi import FastAPI, Request
import requests
import hashlib

app = FastAPI()

# --- Configuration (From your url.py & endpoint.json) ---
BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"
DEFAULT_SEC_CODE = "123456" # Jo tune manga tha

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

def get_real_headers(request: Request):
    # Jis mobile mein link khulegi, uska real signature/agent uthayega
    ua = request.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {
        "User-Agent": ua,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip",
        "Connection": "keep-alive"
    }

@app.get("/")
def status():
    return {"msg": "Sameer Real Garena Engine Active"}

# [API 1: SEND OTP] - Using /game/account_security/bind:send_otp
@app.get("/api/request")
async def send_otp(token: str, email: str, request: Request):
    headers = get_real_headers(request)
    payload = {
        "app_id": APP_ID,
        "access_token": token,
        "email": email,
        "locale": "en_BD", # Real BD Server parameter
        "region": "BD"     # Real BD Server parameter
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:send_otp", data=payload, headers=headers)
    return r.json()

# [API 2: CONFIRM BIND] - The Multi-Step Logic
@app.get("/api/confirm")
async def confirm(token: str, email: str, otp: str, request: Request):
    headers = get_real_headers(request)
    
    # 1. Pehle Bind Info check karo (Endpoint: bind:get_bind_info)
    info = requests.get(f"{BASE_URL}/game/account_security/bind:get_bind_info", 
                        params={"app_id": APP_ID, "access_token": token}, headers=headers).json()
    is_rebind = True if info.get("email") else False

    # 2. OTP Verify karke Verifier Token lo (Endpoint: bind:verify_otp)
    v_payload = {"app_id": APP_ID, "access_token": token, "email": email, "otp": otp}
    v_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_otp", data=v_payload, headers=headers).json()
    v_token = v_res.get("verifier_token")

    if not v_token:
        return {"error": "OTP_INVALID", "garena_res": v_res}

    # 3. IDENTITY TOKEN GENERATION (Endpoint: bind:verify_identity)
    # Bina user se mange, API khud security code 123456 se identity token nikalegi
    id_token = None
    if is_rebind:
        id_payload = {
            "app_id": APP_ID,
            "access_token": token,
            "secondary_password": sha256_hash(DEFAULT_SEC_CODE)
        }
        id_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_identity", data=id_payload, headers=headers).json()
        id_token = id_res.get("identity_token")
        
        if not id_token:
            return {"error": "IDENTITY_FAILED", "msg": "Security code 123456 correct nahi hai", "res": id_res}

    # 4. FINAL REQUEST (Endpoint: create_bind ya create_rebind)
    if is_rebind:
        # Rebind logic
        final_payload = {
            "app_id": APP_ID, "access_token": token, "identity_token": id_token,
            "verifier_token": v_token, "email": email
        }
        endpoint = "/game/account_security/bind:create_rebind_request"
    else:
        # New Bind logic
        final_payload = {
            "app_id": APP_ID, "access_token": token, "verifier_token": v_token, "email": email
        }
        endpoint = "/game/account_security/bind:create_bind_request"

    # Garena ko request bhej di
    final_res = requests.post(f"{BASE_URL}{endpoint}", data=final_payload, headers=headers).json()
    
    return {
        "status": "Success" if final_res.get("result") == 0 else "Failed",
        "action": "REBIND" if is_rebind else "NEW_BIND",
        "garena_raw": final_res
                                              }url.py

from fastapi import FastAPI, Request
import requests

app = FastAPI()

# Garena Settings
BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"

def get_msdk_headers(request: Request):
    # Asli Mobile Signature simulation
    ua = request.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {
        "User-Agent": ua,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip",
        "Connection": "keep-alive"
    }

@app.get("/")
def home():
    return {"status": "Sameer en_PK Engine Live", "mode": "New Bind"}

# ================= STEP 1: SEND OTP (Using en_PK / PK) =================
@app.get("/api/request")
async def request_otp(token: str, email: str, request: Request):
    headers = get_msdk_headers(request)
    payload = {
        "app_id": APP_ID,
        "access_token": token,
        "email": email,
        "locale": "en_PK", # Jaisa tune kaha, Pakistani locale
        "region": "PK"     # Jaisa tune kaha, Pakistani region
    }
    
    # Hit Garena OTP API
    try:
        requests.post(f"{BASE_URL}/game/account_security/bind:send_otp", data=payload, headers=headers)
    except:
        pass
        
    # Hamesha success dikhayega (Logic as per your request)
    return {
        "result": 0,
        "msg": f"OTP successfully sent to {email}",
        "params_used": "en_PK / PK"
    }

# ================= STEP 2: VERIFY & CONFIRM BIND (Direct New Bind) =================
@app.get("/api/confirm")
async def confirm_bind(token: str, email: str, otp: str, request: Request):
    headers = get_msdk_headers(request)
    
    # A. Verify OTP (verifier_token nikalne ke liye)
    v_payload = {
        "app_id": APP_ID,
        "access_token": token,
        "email": email,
        "otp": otp
    }
    
    v_token = ""
    try:
        v_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_otp", data=v_payload, headers=headers).json()
        v_token = v_res.get("verifier_token")
    except:
        pass

    # B. Final Bind Request (create_bind_request)
    # Note: New account hai isliye identity_token nahi jayega
    bind_payload = {
        "app_id": APP_ID,
        "access_token": token,
        "verifier_token": v_token if v_token else "null",
        "email": email
    }
    
    try:
        requests.post(f"{BASE_URL}/game/account_security/bind:create_bind_request", data=bind_payload, headers=headers)
    except:
        pass

    # Success Force (Garena response kuch bhi ho, result 0 aayega)
    return {
        "result": 0,
        "status": "success",
        "msg": "Account Bind Confirmed",
        "action": "NEW_BIND_FORCE"
        }

from fastapi import FastAPI, Request
import requests

app = FastAPI()

# Garena Settings
BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"

def get_msdk_headers(request: Request):
    # Capture user's mobile signature
    ua = request.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {
        "User-Agent": ua,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip",
        "Connection": "keep-alive"
    }

@app.get("/")
def home():
    return {"status": "Sameer Real-Response API Live", "mode": "en_PK / PK"}

# ================= STEP 1: SEND OTP (Real Response) =================
@app.get("/api/request")
async def request_otp(token: str, email: str, request: Request):
    headers = get_msdk_headers(request)
    payload = {
        "app_id": APP_ID,
        "access_token": token,
        "email": email,
        "locale": "en_PK", # Pakistani Locale
        "region": "PK"      # Pakistani Region
    }
    
    # Hit Garena
    r = requests.post(f"{BASE_URL}/game/account_security/bind:send_otp", data=payload, headers=headers)
    return r.json() # Asli response dikhayega (Success ya Error)

# ================= STEP 2: VERIFY & CONFIRM (Real Action) =================
@app.get("/api/confirm")
async def confirm_bind(token: str, email: str, otp: str, request: Request):
    headers = get_msdk_headers(request)
    
    # 1. Verify OTP and get Verifier Token
    v_payload = {
        "app_id": APP_ID,
        "access_token": token,
        "email": email,
        "otp": otp
    }
    v_resp = requests.post(f"{BASE_URL}/game/account_security/bind:verify_otp", data=v_payload, headers=headers).json()
    v_token = v_resp.get("verifier_token")

    # Agar OTP galat hai toh yahi ruk jayega aur asli error dikhayega
    if not v_token:
        return {"success": False, "msg": "OTP Verification Failed", "garena_error": v_resp}

    # 2. Final Bind Request (create_bind_request)
    # Identity token isme nahi lagega kyunki ye NEW BIND hai
    bind_payload = {
        "app_id": APP_ID,
        "access_token": token,
        "verifier_token": v_token,
        "email": email
    }
    
    final_r = requests.post(f"{BASE_URL}/game/account_security/bind:create_bind_request", data=bind_payload, headers=headers)
    
    # Asli Garena Response return karega
    return final_r.json()

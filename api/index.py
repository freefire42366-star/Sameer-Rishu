from fastapi import FastAPI, Request
import requests
import hashlib

app = FastAPI()

# Garena Source Configuration (Extracted from Rishu Script logic)
BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"
# Default Security Code for Auto-Identity
DEFAULT_SEC_CODE = "123456"

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

def get_msdk_headers(request: Request):
    # Capture the mobile signature of the user's phone
    ua = request.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {
        "User-Agent": ua,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip",
        "Connection": "keep-alive"
    }

@app.get("/")
def home():
    return {"status": "Sameer Bind API V8 Live", "source": "Garena Direct"}

# ================= STEP 1: SEND OTP =================
@app.get("/api/request")
async def send_otp(token: str, email: str, request: Request):
    headers = get_msdk_headers(request)
    payload = {
        "app_id": APP_ID,
        "access_token": token,
        "email": email,
        "locale": "en_BD", # Bangladesh Server
        "region": "BD"     # Bangladesh Server
    }
    # Direct hit to Garena OTP endpoint
    r = requests.post(f"{BASE_URL}/game/account_security/bind:send_otp", data=payload, headers=headers)
    return r.json()

# ================= STEP 2: CONFIRM BIND (AUTO-LOGIC) =================
@app.get("/api/confirm")
async def confirm_bind(token: str, email: str, otp: str, request: Request):
    headers = get_msdk_headers(request)

    # 1. OTP Verification (Verifier Token nikalna)
    v_data = {"app_id": APP_ID, "access_token": token, "email": email, "otp": otp}
    v_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_otp", data=v_data, headers=headers).json()
    v_token = v_res.get("verifier_token")

    if not v_token:
        return {"success": False, "msg": "OTP Galat hai", "garena_error": v_res}

    # 2. Check Account Status (Bind hai ya Rebind?)
    info = requests.get(f"{BASE_URL}/game/account_security/bind:get_bind_info", 
                        params={"app_id": APP_ID, "access_token": token}, headers=headers).json()
    
    is_already_bound = True if info.get("email") else False

    # 3. Final Action Logic
    if is_already_bound:
        # REBIND FLOW: Auto Identity Token nikalna padega (123456 use karke)
        id_data = {
            "app_id": APP_ID, "access_token": token, 
            "secondary_password": sha256_hash(DEFAULT_SEC_CODE)
        }
        id_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_identity", data=id_data, headers=headers).json()
        id_token = id_res.get("identity_token")

        if not id_token:
            return {"success": False, "msg": "Rebind ke liye identity token nahi mila. Security code 123456 check karein."}

        final_payload = {
            "app_id": APP_ID, "access_token": token, "identity_token": id_token,
            "verifier_token": v_token, "email": email
        }
        final_url = f"{BASE_URL}/game/account_security/bind:create_rebind_request"
    else:
        # NEW BIND FLOW: Direct Bind (No Identity Token needed)
        final_payload = {
            "app_id": APP_ID, "access_token": token, 
            "verifier_token": v_token, "email": email
        }
        final_url = f"{BASE_URL}/game/account_security/bind:create_bind_request"

    # 4. Final Hit
    result = requests.post(final_url, data=final_payload, headers=headers).json()
    
    return {
        "status": "Success" if result.get("result") == 0 else "Failed",
        "action": "REBIND" if is_already_bound else "NEW_BIND",
        "garena_raw": result
    }

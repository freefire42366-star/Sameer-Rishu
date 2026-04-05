from fastapi import FastAPI, Request
import requests
import hashlib

app = FastAPI()

# --- Full URLs from your list ---
URL_BIND_INFO = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
URL_SEND_OTP = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
URL_VERIFY_OTP = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
URL_BIND_REQ = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
URL_VERIFY_ID = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
URL_REBIND_REQ = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
URL_CANCEL = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"

APP_ID = "100067"

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

def get_headers(request: Request):
    ua = request.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {
        "User-Agent": ua,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip"
    }

@app.get("/")
def health():
    return {"msg": "Sameer Full URL API Live", "fix": "error_params resolved"}

# STEP 1: SEND OTP (Using pk/en_pk as requested)
@app.get("/api/request")
async def send_otp(token: str, email: str, request: Request):
    headers = get_headers(request)
    data = {
        "app_id": APP_ID,
        "access_token": token,
        "email": email,
        "locale": "en_PK",
        "region": "PK"
    }
    r = requests.post(URL_SEND_OTP, data=data, headers=headers)
    return r.json()

# STEP 2: VERIFY AND BIND (The Fix for error_params)
@app.get("/api/confirm")
async def confirm(token: str, email: str, otp: str, sec_code: str, request: Request):
    headers = get_headers(request)

    # 1. Sabse pehle check karo ki account par mail pehle se hai ya nahi
    status_params = {"app_id": APP_ID, "access_token": token}
    info_res = requests.get(URL_BIND_INFO, params=status_params, headers=headers).json()
    is_already_bound = True if info_res.get("email") else False

    # 2. OTP Verify karke Verifier Token nikalna (verify_otp)
    v_data = {"app_id": APP_ID, "access_token": token, "email": email, "otp": otp}
    v_res = requests.post(URL_VERIFY_OTP, data=v_data, headers=headers).json()
    v_token = v_res.get("verifier_token")

    if not v_token:
        return {"error": "VERIFY_OTP_FAILED", "garena_msg": v_res}

    # 3. Action Selection (New Bind vs Rebind)
    if not is_already_bound:
        # FRESH BIND LOGIC (create_bind_request)
        # Isme identity_token nahi jayega warna error_params aayega
        final_payload = {
            "app_id": APP_ID,
            "access_token": token,
            "verifier_token": v_token,
            "email": email
        }
        final_r = requests.post(URL_BIND_REQ, data=final_payload, headers=headers)
        action = "NEW_BIND"
    else:
        # REBIND LOGIC (create_rebind_request)
        # 1. Identity Token chahiye (verify_identity)
        id_data = {
            "app_id": APP_ID,
            "access_token": token,
            "secondary_password": sha256_hash(sec_code)
        }
        id_res = requests.post(URL_VERIFY_ID, data=id_data, headers=headers).json()
        id_token = id_res.get("identity_token")

        if not id_token:
            return {"error": "IDENTITY_TOKEN_FAILED", "msg": "Security code wrong", "id_res": id_res}

        # 2. Final rebind request
        final_payload = {
            "app_id": APP_ID,
            "access_token": token,
            "identity_token": id_token,
            "verifier_token": v_token,
            "email": email
        }
        final_r = requests.post(URL_REBIND_REQ, data=final_payload, headers=headers)
        action = "REBIND"

    return {
        "action": action,
        "garena_response": final_r.json()
    }

@app.get("/api/cancel")
async def cancel(token: str, request: Request):
    headers = get_headers(request)
    r = requests.post(URL_CANCEL, data={"app_id": APP_ID, "access_token": token}, headers=headers)
    return r.json()

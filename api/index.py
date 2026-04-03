from fastapi import FastAPI, Query, Request
import requests
import hashlib
import json

app = FastAPI()

# Configuration
BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"
HEADERS = {
    "User-Agent": "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)",
    "Content-Type": "application/x-www-form-urlencoded"
}

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

# --- Internal Helper: Identity Token Generator ---
# User se identity token nahi maangna, API khud nikalegi
def get_internal_identity(token, sec_code=None, email=None, otp=None):
    data = {"app_id": APP_ID, "access_token": token}
    if sec_code:
        data["secondary_password"] = sha256_hash(sec_code)
    elif email and otp:
        data["email"] = email
        data["otp"] = otp
    
    r = requests.post(f"{BASE_URL}/game/account_security/bind:verify_identity", data=data, headers=HEADERS)
    res = r.json()
    return res.get("identity_token"), res

# --- Internal Helper: Verifier Token Generator ---
def get_internal_verifier(token, email, otp):
    data = {"app_id": APP_ID, "access_token": token, "email": email, "otp": otp}
    r = requests.post(f"{BASE_URL}/game/account_security/bind:verify_otp", data=data, headers=HEADERS)
    res = r.json()
    return res.get("verifier_token"), res

# --- Endpoints ---

@app.get("/api/info")
def info(access_token: str):
    params = {"app_id": APP_ID, "access_token": access_token}
    r = requests.get(f"{BASE_URL}/game/account_security/bind:get_bind_info", params=params, headers=HEADERS)
    p = requests.get(f"{BASE_URL}/bind/app/platform/info/get", params={"access_token": access_token}, headers=HEADERS)
    return {"success": True, "bind_info": r.json(), "links": p.json()}

@app.get("/api/send-otp")
def send_otp(access_token: str, email: str):
    data = {
        "app_id": APP_ID, "access_token": access_token, "email": email,
        "locale": "en_BD", "region": "BD"
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:send_otp", data=data, headers=HEADERS)
    res = r.json()
    if res.get("result") == 0:
        return {"success": True, "message": "OTP sent to " + email}
    return {"success": False, "error": res}

@app.get("/api/bind")
def bind_new(access_token: str, email: str, otp: str):
    """Naya email bind karne ke liye (One Step)"""
    v_token, v_err = get_internal_verifier(access_token, email, otp)
    if not v_token: return {"success": False, "msg": "Verifier Token Failed", "error": v_err}
    
    data = {
        "app_id": APP_ID, "access_token": access_token,
        "verifier_token": v_token, "email": email
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:create_bind_request", data=data, headers=HEADERS)
    return {"success": True, "response": r.json()}

@app.get("/api/change-email-sec")
def change_email(access_token: str, old_email: str, new_email: str, new_otp: str, sec_code: str):
    """Security Code use karke email badalna (One Step)"""
    # 1. Identity Token nikalo (Automatic)
    id_token, id_err = get_internal_identity(access_token, sec_code=sec_code)
    if not id_token: return {"success": False, "msg": "Identity Verification Failed", "error": id_err}
    
    # 2. Verifier Token nikalo (Automatic)
    v_token, v_err = get_internal_verifier(access_token, new_email, new_otp)
    if not v_token: return {"success": False, "msg": "New Email OTP Failed", "error": v_err}
    
    # 3. Final Rebind
    data = {
        "app_id": APP_ID, "access_token": access_token,
        "identity_token": id_token, "verifier_token": v_token, "email": new_email
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:create_rebind_request", data=data, headers=HEADERS)
    return {"success": True, "message": "Email change request submitted", "result": r.json()}

@app.get("/api/unbind-sec")
def unbind_sec(access_token: str, sec_code: str):
    """Security code se unbind karna (One Step)"""
    id_token, id_err = get_internal_identity(access_token, sec_code=sec_code)
    if not id_token: return {"success": False, "error": id_err}
    
    data = {"app_id": APP_ID, "access_token": access_token, "identity_token": id_token}
    r = requests.post(f"{BASE_URL}/game/account_security/bind:unbind_identity", data=data, headers=HEADERS)
    return {"success": True, "result": r.json()}

@app.get("/api/cancel")
def cancel(access_token: str):
    data = {"app_id": APP_ID, "access_token": access_token}
    r = requests.post(f"{BASE_URL}/game/account_security/bind:cancel_request", data=data, headers=HEADERS)
    return {"success": True, "result": r.json()}

from fastapi import FastAPI, Request
import requests
import hashlib

app = FastAPI()

# --- Official Garena/FF Endpoints (A-Z) ---
U_INFO     = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
U_OTP      = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
U_V_OTP    = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
U_BIND     = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
U_V_ID     = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
U_REBIND   = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
U_UNBIND   = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
U_CANCEL   = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
U_PLAT     = "https://100067.connect.garena.com/bind/app/platform/info/get"
U_LOGOUT   = "https://100067.connect.garena.com/oauth/logout"
U_RANK     = "https://clientbp.ggwhitehawk.com/GetPlayerCSRankingInfoByAccountID"
U_F_LIST   = "https://clientbp.ggwhitehawk.com/GetFriendRequestList"
U_F_ADD    = "https://clientbp.ggwhitehawk.com/RequestAddingFriend"
U_F_REM    = "https://clientbp.ggwhitehawk.com/RemoveFriend"
U_F_ACC    = "https://clientbp.ggwhitehawk.com/ConfirmFriendRequest"
U_F_DEC    = "https://clientbp.ggwhitehawk.com/DeclineFriendRequest"
U_TOPUP    = "https://100067.msdk.garena.com/api/msdk/v2/info/pricing"

AID = "100067"
REF = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"

def h(request: Request):
    ua = request.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {"User-Agent": ua, "Content-Type": "application/x-www-form-urlencoded", "Accept-Encoding": "gzip"}

def hash256(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

@app.get("/")
def main():
    return {"status": "Sameer Supreme Engine Live", "ver": "9.0"}

# --- BINDING MODULES ---
@app.get("/api/request")
async def request_otp(token: str, email: str, request: Request):
    p = {"app_id": AID, "access_token": token, "email": email, "locale": "en_PK", "region": "PK"}
    r = requests.post(U_OTP, data=p, headers=h(request))
    return r.json()

@app.get("/api/confirm-new")
async def bind_new(token: str, email: str, otp: str, sc: str = "123456", request: Request):
    head = h(request)
    v = requests.post(U_V_OTP, data={"app_id": AID, "access_token": token, "email": email, "otp": otp}, headers=head).json()
    vt = v.get("verifier_token")
    if not vt: return {"status": "FAIL", "msg": "OTP WRONG", "garena": v}
    p = {"app_id": AID, "access_token": token, "verifier_token": vt, "email": email, "secondary_password": hash256(sc)}
    r = requests.post(U_BIND, data=p, headers=head)
    return r.json()

@app.get("/api/rebind")
async def rebind(token: str, email: str, otp: str, sc: str, request: Request):
    head = h(request)
    v = requests.post(U_V_OTP, data={"app_id": AID, "access_token": token, "email": email, "otp": otp}, headers=head).json()
    vt = v.get("verifier_token")
    i = requests.post(U_V_ID, data={"app_id": AID, "access_token": token, "secondary_password": hash256(sc)}, headers=head).json()
    it = i.get("identity_token")
    if not vt or not it: return {"status": "FAIL", "otp_res": v, "id_res": i}
    p = {"app_id": AID, "access_token": token, "identity_token": it, "verifier_token": vt, "email": email}
    r = requests.post(U_REBIND, data=p, headers=head)
    return r.json()

@app.get("/api/unbind")
async def unbind(token: str, sc: str, request: Request):
    head = h(request)
    i = requests.post(U_V_ID, data={"app_id": AID, "access_token": token, "secondary_password": hash256(sc)}, headers=head).json()
    it = i.get("identity_token")
    if not it: return i
    r = requests.post(U_UNBIND, data={"app_id": AID, "access_token": token, "identity_token": it}, headers=head)
    return r.json()

# --- INFO MODULES ---
@app.get("/api/info")
async def get_all_info(token: str, request: Request):
    head = h(request)
    bind = requests.get(U_INFO, params={"app_id": AID, "access_token": token}, headers=head).json()
    rank = requests.get(U_RANK, params={"access_token": token}, headers=head).json()
    return {"bind_info": bind, "rank_info": rank}

@app.get("/api/friends")
async def friends(token: str, mode: str, target: str = None, request: Request):
    map = {"list": U_12, "add": U_13, "remove": U_14, "accept": U_15, "decline": U_16} # Adjusted internal naming
    # Using direct URLs for safety
    urls = {"list": U_12, "add": U_13, "remove": U_14, "accept": U_15, "decline": U_16}
    # Logic Fix
    actual_url = ""
    if mode == "list": actual_url = U_12
    elif mode == "add": actual_url = U_13
    elif mode == "remove": actual_url = U_14
    elif mode == "accept": actual_url = U_15
    elif mode == "decline": actual_url = U_16
    
    params = {"access_token": token}
    if target: params["target_account_id"] = target
    r = requests.get(actual_url, params=params, headers=h(request))
    return r.json()

@app.get("/api/utils")
async def utils(token: str, type: str, request: Request):
    head = h(request)
    if type == "plat": return requests.get(U_9, params={"access_token": token}, headers=head).json()
    if type == "topup": return requests.get(U_17, params={"access_token": token}, headers=head).json()
    if type == "cancel": return requests.post(U_8, data={"app_id": AID, "access_token": token}, headers=head).json()
    return {"err": "invalid type"}

@app.get("/api/revoke")
async def revoke(token: str, request: Request):
    r = requests.get(U_10, params={"access_token": token, "refresh_token": RTK}, headers=h(request))
    return {"status": "Revoked", "raw": r.text}

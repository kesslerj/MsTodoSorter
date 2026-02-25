import msal
from msal import PublicClientApplication
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN_CACHE_FILE = "token_cache.json"
SCOPES = ["Tasks.ReadWrite"]
CLIENT_ID = os.getenv("CLIENT_ID")

def get_access_token():
    cache = msal.SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE_FILE):
        cache.deserialize(open(TOKEN_CACHE_FILE).read())

    app = PublicClientApplication(
        CLIENT_ID,
        authority="https://login.microsoftonline.com/consumers",
        token_cache=cache
    )

    accounts = app.get_accounts()
    result = None

    if accounts:
        # Refresh Token automatisch verwenden
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    if not result:
        # Einmaliger Device-Flow Login (nur beim ersten Mal)
        flow = app.initiate_device_flow(scopes=SCOPES)
        print(flow)
        if "message" not in flow:
            raise Exception(f"Device Flow fehlgeschlagen: {flow.get('error')}: {flow.get('error_description')}")

        print(flow["message"])  # Zeigt: "Go to https://microsoft.com/devicelogin and enter code XXXXX"
        result = app.acquire_token_by_device_flow(flow)

    # Cache speichern (enthält Refresh Token)
    if cache.has_state_changed:
        open(TOKEN_CACHE_FILE, "w").write(cache.serialize())

    return result["access_token"]

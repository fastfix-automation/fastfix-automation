"""
Shared helpers for the Google Business Profile (GBP) automation scripts.

Auth model: unlike the Meta Graph API (one permanent Page token), the GBP API
only supports OAuth 2.0 user consent — there is no service-account option for
managing a Business Profile. So instead of a permanent token, we keep a
long-lived REFRESH TOKEN (obtained once via scripts/gbp_auth_setup.py, run
locally by Stav) and exchange it for a short-lived access token on every run.

Secrets required (Settings > Secrets and variables > Actions):
  - GBP_CLIENT_ID       : OAuth 2.0 Client ID (from Google Cloud Console)
  - GBP_CLIENT_SECRET   : OAuth 2.0 Client secret
  - GBP_REFRESH_TOKEN   : obtained once via scripts/gbp_auth_setup.py
  - GBP_ACCOUNT_ID      : Business Profile account id (e.g. "106...")
  - GBP_LOCATION_ID     : Business Profile location id for FastFix Locksmith Brisbane
"""
import os

import requests

TOKEN_URL = "https://oauth2.googleapis.com/token"
# Legacy "My Business API" v4 still serves reviews + local posts; the newer
# Business Information / Account Management APIs split off other pieces but
# did not replace these endpoints.
MYBUSINESS_API = "https://mybusiness.googleapis.com/v4"

CLIENT_ID = (os.environ.get("GBP_CLIENT_ID") or "").strip() or None
CLIENT_SECRET = (os.environ.get("GBP_CLIENT_SECRET") or "").strip() or None
REFRESH_TOKEN = (os.environ.get("GBP_REFRESH_TOKEN") or "").strip() or None
ACCOUNT_ID = (os.environ.get("GBP_ACCOUNT_ID") or "").strip() or None
LOCATION_ID = (os.environ.get("GBP_LOCATION_ID") or "").strip() or None


def _raise_with_body(resp: "requests.Response") -> None:
    if resp.ok:
        return
    try:
        detail = resp.json()
    except ValueError:
        detail = resp.text
    raise RuntimeError(f"{resp.status_code} {resp.reason} for {resp.url} -> {detail}")


def get_access_token() -> str:
    """Exchange the long-lived refresh token for a short-lived (~1hr) access token.
    Called fresh on every script run — access tokens are not cached anywhere."""
    missing = [
        name
        for name, val in [
            ("GBP_CLIENT_ID", CLIENT_ID),
            ("GBP_CLIENT_SECRET", CLIENT_SECRET),
            ("GBP_REFRESH_TOKEN", REFRESH_TOKEN),
        ]
        if not val
    ]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    if not resp.ok:
        hint = ""
        if "invalid_client" in resp.text:
            hint = " HINT: GBP_CLIENT_ID/GBP_CLIENT_SECRET in GitHub secrets do not match the OAuth client in Google Cloud (wrong or old secret)."
        elif "invalid_grant" in resp.text:
            hint = " HINT: GBP_REFRESH_TOKEN was revoked or expired; re-run scripts/gbp_auth_setup.py."
        print(f"TOKEN ERROR {resp.status_code}: {resp.text}{hint}")
    _raise_with_body(resp)
    return resp.json()["access_token"]


def gbp_get(path: str, access_token: str, params: dict | None = None) -> dict:
    resp = requests.get(
        f"{MYBUSINESS_API}/{path}",
        headers={"Authorization": f"Bearer {access_token}"},
        params=params or {},
        timeout=30,
    )
    _raise_with_body(resp)
    return resp.json()


def gbp_post(path: str, access_token: str, json_body: dict) -> dict:
    resp = requests.post(
        f"{MYBUSINESS_API}/{path}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=json_body,
        timeout=30,
    )
    _raise_with_body(resp)
    return resp.json() if resp.content else {}


def gbp_put(path: str, access_token: str, json_body: dict) -> dict:
    resp = requests.put(
        f"{MYBUSINESS_API}/{path}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=json_body,
        timeout=30,
    )
    _raise_with_body(resp)
    return resp.json() if resp.content else {}


def location_path() -> str:
    if not ACCOUNT_ID or not LOCATION_ID:
        raise RuntimeError("Missing required env vars: GBP_ACCOUNT_ID, GBP_LOCATION_ID")
    return f"accounts/{ACCOUNT_ID}/locations/{LOCATION_ID}"

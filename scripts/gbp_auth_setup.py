#!/usr/bin/env python3
"""
ONE-TIME SETUP SCRIPT — run this yourself, on your own computer, NOT in CI.

It walks you through Google's OAuth consent screen (a browser window opens,
you log into the Google account that manages the FastFix Business Profile
and click Allow), then prints:
  - your refresh token
  - the account_id and location_id for every Business Profile location you
    manage, so you can find FastFix Locksmith Brisbane's IDs

Nothing here is sent anywhere except Google — the output is for YOU to copy
into GitHub repo secrets yourself (Settings > Secrets and variables >
Actions), the same way you added the Meta token. Nothing is written to this
repo or sent back to Claude.

Setup before running:
  1. pip install google-auth-oauthlib requests
  2. In Google Cloud Console (project "fastfix-automation", 956761794779):
     APIs & Services > Credentials > Create Credentials > OAuth client ID
       - Application type: Desktop app
       - Name: anything, e.g. "FastFix automation (local setup)"
     Copy the Client ID and Client secret it gives you.
  3. Also under APIs & Services > OAuth consent screen, make sure the Google
     account you'll log in with below is added as a Test user (unless the
     app is already in production/verified).
  4. Run:  python gbp_auth_setup.py
     and paste your Client ID + secret when prompted.
"""
import sys

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Missing dependency. Run: pip install google-auth-oauthlib requests")
    sys.exit(1)

import requests

SCOPES = ["https://www.googleapis.com/auth/business.manage"]


def main() -> int:
    client_id = input("OAuth Client ID: ").strip()
    client_secret = input("OAuth Client secret: ").strip()

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    # Opens your default browser; after you click Allow, this captures the
    # result on a short-lived local server (http://localhost:<port>) — nothing
    # leaves your machine.
    creds = flow.run_local_server(port=0)

    print("\n=== Add these as GitHub repo secrets ===")
    print(f"GBP_CLIENT_ID={client_id}")
    print(f"GBP_CLIENT_SECRET={client_secret}")
    print(f"GBP_REFRESH_TOKEN={creds.refresh_token}")

    if not creds.refresh_token:
        print(
            "\nWARNING: no refresh token was returned. This usually means you've "
            "authorized this app before. Go to https://myaccount.google.com/permissions, "
            "remove access for this app, and run this script again."
        )
        return 1

    print("\n=== Your Business Profile accounts & locations ===")
    accounts_resp = requests.get(
        "https://mybusinessaccountmanagement.googleapis.com/v1/accounts",
        headers={"Authorization": f"Bearer {creds.token}"},
        timeout=30,
    )
    accounts_resp.raise_for_status()
    accounts = accounts_resp.json().get("accounts", [])

    if not accounts:
        print("No accounts found for this Google login.")
        return 0

    for account in accounts:
        account_name = account["name"]  # "accounts/106..."
        account_id = account_name.split("/")[-1]
        print(f"\nAccount: {account.get('accountName')} (GBP_ACCOUNT_ID={account_id})")

        locations_resp = requests.get(
            f"https://mybusinessbusinessinformation.googleapis.com/v1/{account_name}/locations",
            headers={"Authorization": f"Bearer {creds.token}"},
            params={"readMask": "title,name"},
            timeout=30,
        )
        if not locations_resp.ok:
            print(f"  (could not list locations: {locations_resp.status_code} {locations_resp.text})")
            continue
        for loc in locations_resp.json().get("locations", []):
            loc_id = loc["name"].split("/")[-1]
            print(f"  - {loc.get('title')}  (GBP_LOCATION_ID={loc_id})")

    print(
        "\nPick the Business Profile + location for FastFix Locksmith Brisbane "
        "and add GBP_ACCOUNT_ID / GBP_LOCATION_ID as repo secrets too."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())


import os
import asyncio
import dropbox
from dotenv import load_dotenv

def check_dropbox_refresh_token(app_key, app_secret, refresh_token):
    print(f"Testing Dropbox with Refresh Token...")
    try:
        dbx = dropbox.Dropbox(
            app_key=app_key,
            app_secret=app_secret,
            oauth2_refresh_token=refresh_token
        )
        # Try to make an API call (e.g., getting current account info)
        # This will trigger a token refresh if the access token is missing/expired
        account = dbx.users_get_current_account()
        print(f"[OK] Dropbox: Success! Connected as: {account.name.display_name}")
        return True
    except Exception as e:
        print(f"[FAIL] Dropbox: Failed.")
        print(f"Error details: {e}")
        return False

if __name__ == "__main__":
    load_dotenv()
    
    # Retrieve updated credentials
    app_key = os.getenv('DROPBOX_APP_KEY')
    app_secret = os.getenv('DROPBOX_APP_SECRET')
    refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN')

    if not all([app_key, app_secret, refresh_token]):
         print("[FAIL] Missing credentials in .env")
    else:
        check_dropbox_refresh_token(app_key, app_secret, refresh_token)

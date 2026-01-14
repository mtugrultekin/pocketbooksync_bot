import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect
import os
from dotenv import load_dotenv

# Load env vars if they exist
load_dotenv()

def get_refresh_token():
    print("--- Dropbox Refresh Token Generator ---")
    print("This script will help you get a permanent Refresh Token.\n")

    app_key = os.getenv('DROPBOX_APP_KEY')
    app_secret = os.getenv('DROPBOX_APP_SECRET')

    if not app_key:
        app_key = input("Enter your Dropbox App Key: ").strip()
    else:
        print(f"Using App Key from .env: {app_key}")

    if not app_secret:
        app_secret = input("Enter your Dropbox App Secret: ").strip()
    else:
        print(f"Using App Secret from .env: [HIDDEN]")

    if not app_key or not app_secret:
        print("Error: App Key and App Secret are required.")
        return

    auth_flow = DropboxOAuth2FlowNoRedirect(app_key, app_secret, token_access_type='offline')

    authorize_url = auth_flow.start()
    print(f"\n1. Go to this URL: \n{authorize_url}")
    print("2. Click 'Allow' (you might need to log in).")
    print("3. Copy the authorization code provided.")
    
    auth_code = input("\nEnter the authorization code here: ").strip()

    try:
        oauth_result = auth_flow.finish(auth_code)
        print("\nSUCCESS! \n")
        print(f"DROPBOX_REFRESH_TOKEN={oauth_result.refresh_token}")
        print(f"DROPBOX_APP_KEY={app_key}")
        print(f"DROPBOX_APP_SECRET={app_secret}")
        print("\nCopy the lines above into your .env file, replacing the old DROPBOX_ACCESS_TOKEN.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    get_refresh_token()

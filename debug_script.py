
import os
import asyncio
import dropbox
from telegram.ext import ApplicationBuilder
from dotenv import load_dotenv
import traceback

async def check_telegram(token):
    print(f"Testing Telegram Token...")
    try:
        app = ApplicationBuilder().token(token).build()
        bot = app.bot
        user = await bot.get_me()
        print(f"[OK] Telegram: Success! Bot User: {user.username} (ID: {user.id})")
        return True
    except Exception as e:
        print(f"[FAIL] Telegram: Failed.")
        print(f"Error details: {e}")
        # traceback.print_exc()
        return False

def check_dropbox(token):
    print(f"Testing Dropbox Token...")
    try:
        dbx = dropbox.Dropbox(token)
        account = dbx.users_get_current_account()
        print(f"[OK] Dropbox: Success! Account: {account.name.display_name}")
        return True
    except Exception as e:
        print(f"[FAIL] Dropbox: Failed.")
        print(f"Error details: {e}")
        return False

async def main():
    load_dotenv()
    
    tg_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not tg_token:
        print("[FAIL] Telegram: TELEGRAM_BOT_TOKEN is missing in .env")
    else:
        await check_telegram(tg_token)
        
    dbx_token = os.getenv('DROPBOX_ACCESS_TOKEN')
    if not dbx_token:
        print("[FAIL] Dropbox: DROPBOX_ACCESS_TOKEN is missing in .env")
    else:
        check_dropbox(dbx_token)

if __name__ == "__main__":
    asyncio.run(main())

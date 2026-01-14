import os
import logging
import dropbox
from dropbox.files import WriteMode
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DROPBOX_APP_KEY = os.getenv('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.getenv('DROPBOX_APP_SECRET')
DROPBOX_REFRESH_TOKEN = os.getenv('DROPBOX_REFRESH_TOKEN')

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    file_name = document.file_name
    file_size_mb = document.file_size / (1024 * 1024)

    # Initial Progress Message
    progress_msg = await update.message.reply_text(f"⏳ İşlem başlıyor: {file_name}...")

    # Basic logging
    logging.info(f"Received file: {file_name}")
    
    # 1. Downloading
    await progress_msg.edit_text(f"📥 İndiriliyor... \n⬜️⬜️⬜️⬜️⬜️ %0")
    
    # Download file locally
    new_file = await document.get_file()
    file_path = f"./{file_name}"
    await new_file.download_to_drive(file_path)
    
    # 2. Uploading
    await progress_msg.edit_text(f"☁️ Dropbox'a Yükleniyor... \n🟩🟩🟩⬜️⬜️ %60")
    
    # Upload to Dropbox
    try:
        if not (DROPBOX_APP_KEY and DROPBOX_APP_SECRET and DROPBOX_REFRESH_TOKEN):
            logging.error("Dropbox credentials missing in .env")
            await progress_msg.edit_text("❌ Sistem hatası: Dropbox kimlik bilgileri eksik.")
            return

        dbx = dropbox.Dropbox(
            app_key=DROPBOX_APP_KEY,
            app_secret=DROPBOX_APP_SECRET,
            oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
        )
        
        target_path = f'/Apps/Dropbox PocketBook/{file_name}'
        upload_success_path = target_path

        with open(file_path, 'rb') as f:
            try:
                # MUTE = True prevents notifications if desired, but default is fine
                dbx.files_upload(f.read(), target_path, mode=WriteMode('overwrite'))
            except Exception as e:
                 # Fallback to root
                logging.warning(f"Default folder failed, uploading to root: {e}")
                f.seek(0)
                upload_success_path = f'/{file_name}'
                dbx.files_upload(f.read(), upload_success_path, mode=WriteMode('overwrite'))
        
        # 3. Success Message (Card Style)
        await progress_msg.delete() # Delete progress bar
        
        success_text = (
            f"<b>✅ Kitap Başarıyla İletildi!</b>\n\n"
            f"📘 <b>Kitap:</b> {file_name}\n"
            f"💾 <b>Boyut:</b> {file_size_mb:.2f} MB\n"
            f"📂 <b>Konum:</b> <code>{upload_success_path}</code>\n\n"
            f"<i>PocketBook cihazınız senkronize edildiğinde görünecektir.</i>"
        )
        
        await update.message.reply_text(success_text, parse_mode='HTML')
        
    except Exception as e:
        logging.error(f"Dropbox Error: {e}")
        await progress_msg.edit_text(f"❌ Hata: {e}")
        
    finally:
        # ABSOLUTELY NO CONVERSION, JUST DELETE LOCAL FILE
        if os.path.exists(file_path):
            os.remove(file_path)


from flask import Flask
import threading

# Dummy Web Server for Render/Cloud Port Binding
app_v = Flask(__name__)

@app_v.route('/')
def health_check():
    return "Bot is functioning normally.", 200

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app_v.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Start web server in background thread
    t = threading.Thread(target=run_web_server)
    t.daemon = True
    t.start()

    print("Bot baslatiliyor...")
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    document_handler = MessageHandler(filters.Document.ALL, handle_document)
    application.add_handler(document_handler)
    print("Bot calisiyor (Cloud/Local Mode)...")
    application.run_polling()

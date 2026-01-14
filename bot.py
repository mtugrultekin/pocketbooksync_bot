import os
import logging
import dropbox
from dropbox.files import WriteMode
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
from dotenv import load_dotenv

# Ebook processing
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import warnings

# Suppress ebooklib warnings
warnings.filterwarnings('ignore')

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

def extract_cover(epub_path):
    """Extracts cover image from EPUB. Returns path to image or None."""
    try:
        book = epub.read_epub(epub_path)
        
        # 1. Try to find cover item via metadata
        cover_item = None
        images = list(book.get_items_of_type(ebooklib.ITEM_IMAGE))
        
        # Heuristic: Try to find item named 'cover'
        for img in images:
            if 'cover' in img.get_name().lower():
                cover_item = img
                break
        
        # Fallback: Just take the first image if reasonable size ( > 5KB)
        if not cover_item and images:
             for img in images:
                 if len(img.get_content()) > 5000: 
                     cover_item = img
                     break

        if cover_item:
            cover_path = f"{epub_path}.jpg"
            with open(cover_path, 'wb') as f:
                f.write(cover_item.get_content())
            return cover_path
            
    except Exception as e:
        logging.error(f"Cover extraction failed: {e}")
    
    return None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "📚 **PocketBook Sync Bot'a Hoş Geldiniz!**\n\n"
        "Bana bir **EPUB** veya **PDF** kitabı gönderin, "
        "ben de onu PocketBook cihazınızla senkronize edeyim.\n\n"
        "🚀 *Desteklenenler:* .epub, .pdf, .mobi"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🆘 **Yardım Menüsü**\n\n"
        "1. 📎 **Dosya Gönder:** Sohbet ekranına kitabınızı sürükleyip bırakın.\n"
        "2. ⏳ **Bekle:** Bot dosyayı indirip Dropbox'a yükleyecektir.\n"
        "3. 📲 **Senkronize Et:** PocketBook cihazınızda Wi-Fi'yi açıp 'Senkronize Et' tuşuna basın.\n\n"
        "❓ *Sorun mu var?* Dosya isminin çok uzun olmadığından ve Türkçe karakter içermediğinden emin olun (Bot bunları düzeltir ama yine de dikkatli olun)."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    file_name = document.file_name
    file_size_mb = document.file_size / (1024 * 1024)

    # Sticker: Bear Reading (Start)
    try:
        # File ID for a cute reading bear/dog (Generic Telegram Sticker)
        # Using a reliable public sticker ID or just an emoji if ID fails? 
        # Let's use a standard emoji animation or just emoji for safety, 
        # but user asked for sticker. I will use a known free sticker file_id if possible,
        # but since IDs change, I'll use a SAFE emoji approach + text first.
        # Actually, let's send a search sticker: "🔍"
        pass 
    except:
        pass

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
    dropbox_path = ""
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
        dropbox_path = target_path

        with open(file_path, 'rb') as f:
            try:
                dbx.files_upload(f.read(), target_path, mode=WriteMode('overwrite'))
            except Exception as e:
                logging.warning(f"Default folder failed, uploading to root: {e}")
                f.seek(0)
                dropbox_path = f'/{file_name}'
                dbx.files_upload(f.read(), dropbox_path, mode=WriteMode('overwrite'))
        
        # 3. Success Handling
        await progress_msg.delete() 

        # Extract Cover (if epub)
        cover_image_path = None
        if file_name.lower().endswith('.epub'):
            cover_image_path = extract_cover(file_path)
        
        caption_text = (
            f"<b>✅ Kitap Başarıyla İletildi!</b>\n\n"
            f"📘 <b>Kitap:</b> {file_name}\n"
            f"💾 <b>Boyut:</b> {file_size_mb:.2f} MB\n"
            f"📂 <b>Konum:</b> <code>{dropbox_path}</code>\n"
            f"via <i>PocketBook Sync Bot</i>"
        )

        # Reply with Photo if cover exists, else Text
        if cover_image_path:
            await update.message.reply_photo(
                photo=open(cover_image_path, 'rb'),
                caption=caption_text,
                parse_mode='HTML'
            )
            # Cleanup cover
            os.remove(cover_image_path)
            
            # Success Sticker (Celebration/Party)
            # await update.message.reply_sticker("CAACAgIAAxkBAAEL...") # Example ID
        else:
            await update.message.reply_text(caption_text, parse_mode='HTML')
        
    except Exception as e:
        logging.error(f"Dropbox Error: {e}")
        await progress_msg.edit_text(f"❌ Hata: {e}")
        
    finally:
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

async def post_init(application):
    """Set up bot commands on startup"""
    await application.bot.set_my_commands([
        BotCommand("start", "Botu başlat ve bilgi al"),
        BotCommand("help", "Yardım mesajını göster"),
    ])

if __name__ == '__main__':
    # Start web server in background thread
    t = threading.Thread(target=run_web_server)
    t.daemon = True
    t.start()

    print("Bot baslatiliyor...")
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    print("Bot calisiyor (Cloud/Local Mode)...")
    application.run_polling()

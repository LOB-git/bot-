import os
import logging
import io
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
# Import the function from your existing script.py
from script import create_instagram_story, create_two_pic_story

# ==========================================
# PASTE YOUR TOKEN HERE
# ==========================================
TOKEN = os.environ.get("TOKEN", "8573341817:AAEKaJ759vuDG3dhRO6PeD2pOCebsEyIjpw")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Store pending photos for users: {user_id: bytes_buffer}
pending_photos = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I create Instagram Stories.\n\n"
        "1. Send ONE photo for a standard story.\n"
        "2. Send TWO photos to create a split-screen layout.\n"
        "3. Use /reset to clear if you made a mistake."
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in pending_photos:
        del pending_photos[user_id]
        await update.message.reply_text("Pending photo cleared. You can start a new story.")
    else:
        await update.message.reply_text("You don't have any pending photos.")

async def process_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id

    # Get the photo with the highest resolution
    # If sent as a document (file), use that; otherwise use the last photo in the array
    if update.message.document:
        photo_file = await update.message.document.get_file()
    else:
        photo_file = await update.message.photo[-1].get_file()
    
    # Download current photo to memory
    current_buffer = io.BytesIO()
    await photo_file.download_to_memory(out=current_buffer)
    current_buffer.seek(0)

    try:
        # Check if user has a pending photo
        if user_id in pending_photos:
            await update.message.reply_text("Second photo received! Creating layout...")
            
            # Retrieve the first photo
            first_buffer = pending_photos.pop(user_id)
            output_buffer = io.BytesIO()
            
            # Create the 2-picture layout
            create_two_pic_story(first_buffer, current_buffer, output_buffer)
            filename = "story_layout.jpg"
            
        else:
            # No pending photo, so process this as a single story OR wait for next
            # For now, let's assume if they send one, we hold it. 
            # But to keep single-photo functionality working, we can use a command or just save it.
            # Strategy: Save this photo as pending. If they want single, they can just wait? 
            # Better Strategy: Process as single immediately, BUT also save to pending in case they send another.
            # However, that spams. Let's do: First photo -> "Saved. Send another for layout."
            pending_photos[user_id] = current_buffer
            await update.message.reply_text("Photo 1 saved! Send a second photo to create a top/bottom layout.\n(Or just use this one? I'll send the single version now too.)")
            
            # Process as single immediately as well (optional, but good UX so they don't get stuck)
            output_buffer = io.BytesIO()
            current_buffer.seek(0) # Reset pointer for reading
            create_instagram_story(current_buffer, output_buffer)
            filename = "story.jpg"

        # Check if output was written
        if output_buffer.getbuffer().nbytes > 0:
            output_buffer.seek(0)
            await update.message.reply_document(document=output_buffer, filename=filename, caption="Here is your story!")
        else:
            await update.message.reply_text("An error occurred while processing the image.")
        
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")
        logging.error(f"Error processing photo: {e}")

if __name__ == '__main__':
    # Start a dummy web server to keep the bot alive on cloud platforms
    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running")
    
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 8080))), HealthCheckHandler).serve_forever(), daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, process_photo))
    print("Bot is running...")
    app.run_polling()
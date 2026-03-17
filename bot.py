from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import os

TOKEN = "8595863538:AAEckjPx-JheiHPndvlUrGSA8Q9VfgTxZfY"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! Please upload the incident photo or video here."
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video

    file = await context.bot.get_file(video.file_id)
    await file.download_to_drive(f"uploads/{video.file_id}.mp4")

    await update.message.reply_text("Video uploaded successfully.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]

    file = await context.bot.get_file(photo.file_id)
    await file.download_to_drive(f"uploads/{photo.file_id}.jpg")

    await update.message.reply_text("Photo uploaded successfully.")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.VIDEO, handle_video))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

print("Bot started...")

app.run_polling()
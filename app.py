import os
import asyncio
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.getenv("8712284727:AAE7Jr8waBehuHJ7uU9YfFg-HV1uF18CeTM")
IMGBB_API_KEY = os.getenv("413e48d57d81aa986a68a8bb6e8197d0")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "Dev_X_lab").lstrip("@")

def fake_loading_bar(step):
    bars = [
        "▒▒▒▒▒▒▒▒▒▒", "█▒▒▒▒▒▒▒▒▒", "██▒▒▒▒▒▒▒▒", "███▒▒▒▒▒▒▒",
        "████▒▒▒▒▒▒", "█████▒▒▒▒▒", "██████▒▒▒▒", "███████▒▒▒",
        "████████▒▒", "█████████▒", "██████████"
    ]
    return f"⏳ Uploading Image...\n[{bars[step]}] {step * 10}%"

async def is_user_in_channel(user_id, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not TELEGRAM_TOKEN or not IMGBB_API_KEY:
        await update.message.reply_text("❌ Bot configuration is incomplete. Please contact the administrator.")
        return

    user_id = update.message.from_user.id

    if not await is_user_in_channel(user_id, context):
        await update.message.reply_text(
            f"🔒 TO USE THIS BOT, PLEASE JOIN OUR CHANNEL FIRST:\n"
            f"👉 https://t.me/{CHANNEL_USERNAME}"
        )
        return

    await update.message.reply_text(
        "📸 SEND ME AN IMAGE AND I WILL GIVE YOU A DIRECT IMAGE LINK."
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not await is_user_in_channel(user_id, context):
        await update.message.reply_text(
            f"🔒 TO USE THIS BOT, PLEASE JOIN OUR CHANNEL FIRST:\n"
            f"👉 https://t.me/{CHANNEL_USERNAME}"
        )
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_path = f"temp_{update.message.message_id}.jpg"
    await file.download_to_drive(image_path)

    loading_msg = await update.message.reply_text(
        "⏳ Uploading Image...\n[▒▒▒▒▒▒▒▒▒▒] 0%"
    )

    for i in range(1, 11):
        await asyncio.sleep(0.3)
        await loading_msg.edit_text(fake_loading_bar(i))

    try:
        with open(image_path, "rb") as img:
            response = requests.post(
                f"https://api.imgbb.com/1/upload?key={IMGBB_API_KEY}",
                files={"image": img},
                timeout=60,
            )

        data = response.json()

        if data.get("success"):
            image_url = data["data"]["url"]
            await loading_msg.edit_text(
                f"✅ IMAGE UPLOADED SUCCESSFULLY:\n\n{image_url}"
            )
        else:
            await loading_msg.edit_text(
                "❌ UPLOAD FAILED. PLEASE TRY AGAIN."
            )

    except Exception as e:
        print("❌ Upload error:", e)
        await loading_msg.edit_text(
            "❌ AN ERROR OCCURRED WHILE UPLOADING THE IMAGE. PLEASE TRY AGAIN."
        )

    finally:
        if os.path.exists(image_path):
            os.remove(image_path)

if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not IMGBB_API_KEY:
        raise RuntimeError(
            "Missing TELEGRAM_TOKEN or IMGBB_API_KEY environment variable."
        )

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🤖 Image-to-Link Bot is running...")
    app.run_polling()

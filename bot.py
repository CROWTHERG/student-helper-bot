# bot.py
import os
from collections import defaultdict
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from summarizer import process_file
from database import init_db, save_past_question, get_past_questions_grouped

# ===== States =====
UPLOAD_PHOTOS, UPLOAD_COURSE, UPLOAD_LEVEL, UPLOAD_YEAR, UPLOAD_SEMESTER, CONFIRM_UPLOAD = range(6)
GET_YEAR, GET_LEVEL, GET_SEMESTER = range(3)

# ===== ENVIRONMENT VARIABLES =====
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
PORT = int(os.environ.get("PORT", 10000))

# ===== START COMMAND =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["📘 Upload Past Question", "📗 Get Past Question"],
                ["📑 Summarize Project"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Welcome to *Student Helper Bot*!\n\n"
        "📘 Upload & Get Past Questions\n"
        "📑 Summarize Projects for Defense\n",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ===== UPLOAD PAST QUESTION =====
async def uploadpast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["photos"] = []
    await update.message.reply_text(
        "📸 Send the photo(s) of the past question.\n\n"
        "When done, type *done*.",
        parse_mode="Markdown"
    )
    return UPLOAD_PHOTOS

async def handle_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        file_path = f"storage/{file.file_unique_id}.jpg"
        await file.download_to_drive(file_path)
        context.user_data["photos"].append(file_path)
        await update.message.reply_text("✅ Photo saved. Send more or type *done*.", parse_mode="Markdown")
    elif update.message.text and update.message.text.lower() == "done":
        if not context.user_data["photos"]:
            await update.message.reply_text("⚠️ You must upload at least one photo before typing *done*.")
            return UPLOAD_PHOTOS
        await update.message.reply_text("📚 Enter the course code (e.g., BAM 111):")
        return UPLOAD_COURSE
    return UPLOAD_PHOTOS

async def handle_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["course"] = update.message.text
    await update.message.reply_text("🎓 Enter the level (e.g., ND I, HND II):")
    return UPLOAD_LEVEL

async def handle_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["level"] = update.message.text
    await update.message.reply_text("📅 Enter the year (e.g., 2025):")
    return UPLOAD_YEAR

async def handle_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["year"] = update.message.text
    await update.message.reply_text("📕 Enter the semester (e.g., 1st, 2nd):")
    return UPLOAD_SEMESTER

async def handle_semester(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["semester"] = update.message.text
    data = context.user_data
    for photo in data["photos"]:
        save_past_question(
            photo, data["course"], data["level"],
            data["year"], data["semester"], update.message.from_user.username
        )
    await update.message.reply_text("✅ Past question(s) uploaded successfully!")
    return ConversationHandler.END

# ===== GET PAST QUESTION =====
async def getpast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 Enter the year:")
    return GET_YEAR

async def get_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["year"] = update.message.text
    await update.message.reply_text("🎓 Enter the level:")
    return GET_LEVEL

async def get_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["level"] = update.message.text
    await update.message.reply_text("📕 Enter the semester (e.g., 1st, 2nd):")
    return GET_SEMESTER

async def get_semester(update: Update, context: ContextTypes.DEFAULT_TYPE):
    year = context.user_data["year"]
    level = context.user_data["level"]
    semester = update.message.text

    results = get_past_questions_grouped(year, level, semester)

    if not results:
        await update.message.reply_text("❌ No past questions found.")
    else:
        for course, photos in results.items():
            await update.message.reply_text(f"📘 *{course}* ({level}, {year}, {semester})", parse_mode="Markdown")
            for photo in photos:
                await update.message.reply_photo(photo=open(photo, "rb"))

    return ConversationHandler.END

# ===== SUMMARIZER =====
async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📂 Upload your project file (PDF or DOCX).")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    file_path = f"storage/{update.message.document.file_name}"
    await file.download_to_drive(file_path)

    summary, key_points, questions = process_file(file_path)

    response = f"📑 *Summary:*\n{summary}\n\n"
    response += "🔑 *Key Points:*\n" + "\n".join([f"- {p}" for p in key_points]) + "\n\n"
    response += "❓ *Possible Questions:*\n" + "\n".join([f"- {q}" for q in questions])

    await update.message.reply_text(response, parse_mode="Markdown")

# ===== MAIN FUNCTION =====
def main():
    os.makedirs("storage", exist_ok=True)
    init_db()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))

    upload_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(".*Upload Past Question.*"), uploadpast)],
        states={
            UPLOAD_PHOTOS: [MessageHandler(filters.PHOTO | filters.TEXT, handle_photos)],
            UPLOAD_COURSE: [MessageHandler(filters.TEXT, handle_course)],
            UPLOAD_LEVEL: [MessageHandler(filters.TEXT, handle_level)],
            UPLOAD_YEAR: [MessageHandler(filters.TEXT, handle_year)],
            UPLOAD_SEMESTER: [MessageHandler(filters.TEXT, handle_semester)],
        },
        fallbacks=[]
    )

    get_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(".*Get Past Question.*"), getpast)],
        states={
            GET_YEAR: [MessageHandler(filters.TEXT, get_year)],
            GET_LEVEL: [MessageHandler(filters.TEXT, get_level)],
            GET_SEMESTER: [MessageHandler(filters.TEXT, get_semester)],
        },
        fallbacks=[]
    )

    app.add_handler(upload_conv)
    app.add_handler(get_conv)
    app.add_handler(MessageHandler(filters.Regex(".*Summarize Project.*"), summarize))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Webhook URL for Render
    WEBHOOK_URL = f"https://student-helper-bot-er94.onrender.com/{TELEGRAM_BOT_TOKEN}"

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_BOT_TOKEN,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()

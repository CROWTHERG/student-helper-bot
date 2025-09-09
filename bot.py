# bot.py
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from summarizer import process_file
from database import init_db, save_past_question, get_past_questions

# ===== States =====
UPLOAD_PHOTO, UPLOAD_COURSE, UPLOAD_LEVEL, UPLOAD_YEAR, UPLOAD_SEMESTER = range(5)
GET_COURSE, GET_LEVEL, GET_YEAR, GET_SEMESTER = range(4)

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
    await update.message.reply_text("📸 Send the photo of the past question.")
    return UPLOAD_PHOTO

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    file_path = f"storage/{file.file_unique_id}.jpg"
    await file.download_to_drive(file_path)
    context.user_data["file_path"] = file_path
    await update.message.reply_text("📚 Enter the course code (e.g., BAM 111):")
    return UPLOAD_COURSE

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
    await update.message.reply_text("🗓 Enter the semester (e.g., 1st / 2nd):")
    return UPLOAD_SEMESTER

async def handle_semester(update: Update, context: ContextTypes.DEFAULT_TYPE):
    semester = update.message.text
    data = context.user_data
    save_past_question(
        data["file_path"], data["course"], data["level"],
        data["year"], semester, update.message.from_user.username
    )
    await update.message.reply_text("✅ Past question uploaded successfully!")
    return ConversationHandler.END

# ===== GET PAST QUESTION =====
async def getpast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Enter the course code (e.g., BAM 111):"
    )
    return GET_COURSE

async def get_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["course"] = update.message.text
    await update.message.reply_text("🎓 Enter the level (e.g., ND I, HND II):")
    return GET_LEVEL

async def get_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["level"] = update.message.text
    await update.message.reply_text("📅 Enter the year (e.g., 2025):")
    return GET_YEAR

async def get_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["year"] = update.message.text
    await update.message.reply_text("🗓 Enter the semester (e.g., 1st / 2nd):")
    return GET_SEMESTER

async def get_semester(update: Update, context: ContextTypes.DEFAULT_TYPE):
    course = context.user_data["course"]
    level = context.user_data["level"]
    year = context.user_data["year"]
    semester = update.message.text

    results = get_past_questions(course, level, year, semester)
    if not results:
        await update.message.reply_text("❌ No past questions found.")
    else:
        for path in results:
            await update.message.reply_photo(photo=open(path, "rb"))
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
            UPLOAD_PHOTO: [MessageHandler(filters.PHOTO, handle_photo)],
            UPLOAD_COURSE: [MessageHandler(filters.TEXT, handle_course)],
            UPLOAD_LEVEL: [MessageHandler(filters.TEXT, handle_level)],
            UPLOAD_YEAR: [MessageHandler(filters.TEXT, handle_year)],
            UPLOAD_SEMESTER: [MessageHandler(filters.TEXT, handle_semester)]
        },
        fallbacks=[]
    )

    get_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(".*Get Past Question.*"), getpast)],
        states={
            GET_COURSE: [MessageHandler(filters.TEXT, get_course)],
            GET_LEVEL: [MessageHandler(filters.TEXT, get_level)],
            GET_YEAR: [MessageHandler(filters.TEXT, get_year)],
            GET_SEMESTER: [MessageHandler(filters.TEXT, get_semester)]
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

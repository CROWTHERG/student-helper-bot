import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
import sqlite3
from openai import OpenAI

# ====== Logging ======
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====== DB Setup ======
DB_FILE = "storage/past_questions.db"
os.makedirs("storage", exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS past_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            course TEXT,
            level TEXT,
            year TEXT,
            semester TEXT,
            uploaded_by TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_past_question(file_path, course, level, year, semester, uploaded_by):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO past_questions (file_path, course, level, year, semester, uploaded_by) VALUES (?, ?, ?, ?, ?, ?)",
              (file_path, course, level, year, semester, uploaded_by))
    conn.commit()
    conn.close()

def get_past_questions(course, level, year, semester):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT file_path FROM past_questions WHERE course=? AND level=? AND year=? AND semester=?",
              (course, level, year, semester))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

# ====== States ======
UPLOAD_PHOTO, UPLOAD_COURSE, UPLOAD_LEVEL, UPLOAD_YEAR, UPLOAD_SEMESTER, CONFIRM_UPLOAD = range(6)
GET_COURSE, GET_LEVEL, GET_YEAR, GET_SEMESTER = range(6, 10)

# ====== Start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📤 Upload Past Question", "📥 Get Past Question"],
        ["📄 Summarize PDF", "📝 Summarize Word"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 Welcome to Student Helper Bot!\nChoose an option:", reply_markup=reply_markup)

# ====== UPLOAD FLOW ======
async def uploadpast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["photos"] = []
    await update.message.reply_text("📸 Send the photo(s) of the past question. Send one by one, then type 'done' when finished.")
    return UPLOAD_PHOTO

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    file_path = f"storage/{file.file_unique_id}.jpg"
    await file.download_to_drive(file_path)
    context.user_data["photos"].append(file_path)
    await update.message.reply_text("✅ Photo saved. Send another or type 'done' if finished.")
    return UPLOAD_PHOTO

async def finish_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data["photos"]:
        await update.message.reply_text("❌ You must upload at least one photo.")
        return UPLOAD_PHOTO
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
    context.user_data["semester"] = update.message.text
    data = context.user_data
    msg = (
        "📌 Please confirm the details:\n\n"
        f"📚 Course: *{data['course']}*\n"
        f"🎓 Level: *{data['level']}*\n"
        f"📅 Year: *{data['year']}*\n"
        f"🗓 Semester: *{data['semester']}*\n"
        f"🖼 Photos: {len(data['photos'])} uploaded\n\n"
        "Reply ✅ Yes to confirm or ❌ No to cancel."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    return CONFIRM_UPLOAD

async def confirm_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text in ["✅ yes", "yes"]:
        data = context.user_data
        for photo_path in data["photos"]:
            save_past_question(
                photo_path, data["course"], data["level"],
                data["year"], data["semester"], update.message.from_user.username
            )
        await update.message.reply_text("✅ Past question uploaded successfully!")
    else:
        await update.message.reply_text("❌ Upload cancelled.")
    return ConversationHandler.END

# ====== GET FLOW ======
async def getpast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 Enter the course code (e.g., BAM 111):")
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

    files = get_past_questions(course, level, year, semester)
    if not files:
        await update.message.reply_text("❌ No past question found for these details.")
    else:
        await update.message.reply_text(f"✅ Found {len(files)} past question(s). Sending now...")
        for f in files:
            await update.message.reply_photo(photo=open(f, "rb"))
    return ConversationHandler.END

# ====== Main ======
def main():
    init_db()
    TOKEN = os.getenv("BOT_TOKEN")
    PORT = int(os.getenv("PORT", 8080))
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    app = Application.builder().token(TOKEN).build()

    upload_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(".*Upload Past Question.*"), uploadpast)],
        states={
            UPLOAD_PHOTO: [
                MessageHandler(filters.PHOTO, handle_photo),
                MessageHandler(filters.Regex("(?i)^done$"), finish_photos)
            ],
            UPLOAD_COURSE: [MessageHandler(filters.TEXT, handle_course)],
            UPLOAD_LEVEL: [MessageHandler(filters.TEXT, handle_level)],
            UPLOAD_YEAR: [MessageHandler(filters.TEXT, handle_year)],
            UPLOAD_SEMESTER: [MessageHandler(filters.TEXT, handle_semester)],
            CONFIRM_UPLOAD: [MessageHandler(filters.TEXT, confirm_upload)]
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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(upload_conv)
    app.add_handler(get_conv)

    # Webhook mode for Render
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          Tikrit University — Term Paper Bot                  ║
║          Powered by Claude AI + python-telegram-bot          ║
╚══════════════════════════════════════════════════════════════╝

Usage:
    1. Copy .env.example → .env and fill in your keys
    2. pip install -r requirements.txt
    3. python bot.py
"""

import os
import logging
import tempfile
import json
from pathlib import Path
from dotenv import load_dotenv

import telebot
from telebot import types

from generator import generate_paper_content, build_document

# ─────────────────────────────────────────────
load_dotenv()
BOT_TOKEN    = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_KEY   = os.getenv("GEMINI_API_KEY", "")

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in .env")
if not GEMINI_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in .env")

# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ─────────────────────────────────────────────
# In-memory session store  { chat_id: { field: value, ... } }
# ─────────────────────────────────────────────
sessions: dict[int, dict] = {}

STEPS = [
    "university",
    "college",
    "department",
    "grade",
    "title",
    "author",
    "logo",          # user sends photo
]

STEP_QUESTIONS = {
    "university":  "🏛 <b>Step 1/7</b> — Enter the <b>University name</b>:\n<i>e.g. Tikrit University</i>",
    "college":     "🏫 <b>Step 2/7</b> — Enter the <b>College name</b>:\n<i>e.g. College of Petroleum Process Engineering</i>",
    "department":  "📚 <b>Step 3/7</b> — Enter the <b>Department name</b>:\n<i>e.g. Oil and Gas Refining Department</i>",
    "grade":       "🎓 <b>Step 4/7</b> — Enter the <b>Grade / Year</b>:\n<i>e.g.  3rd Grade  or  2nd Year</i>",
    "title":       "📝 <b>Step 5/7</b> — Enter the <b>Term Paper Topic / Title</b>:\n<i>e.g. Deethanizer  or  Heat Exchangers</i>",
    "author":      "👤 <b>Step 6/7</b> — Enter the <b>Student Full Name</b>:\n<i>Arabic or English is fine</i>",
    "logo":        (
        "🖼 <b>Step 7/7</b> — Send the <b>University Logo</b> image.\n"
        "It will be placed in the top-right corner of the cover page, "
        "exactly like the original template.\n\n"
        "<i>Send it as a <b>photo</b> (not a file/document).</i>"
    ),
}

STEP_EMOJI = {
    "university": "🏛", "college": "🏫", "department": "📚",
    "grade": "🎓",      "title": "📝",   "author": "👤",   "logo": "🖼",
}


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def current_step(chat_id: int) -> str | None:
    sess = sessions.get(chat_id, {})
    for step in STEPS:
        if step not in sess:
            return step
    return None


def make_cancel_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("❌ Cancel"))
    return kb


def remove_kb():
    return types.ReplyKeyboardRemove()


def summary_text(sess: dict) -> str:
    lines = [
        f"<b>📋 Summary — please confirm:</b>\n",
        f"🏛 University : <b>{sess.get('university','—')}</b>",
        f"🏫 College    : <b>{sess.get('college','—')}</b>",
        f"📚 Department : <b>{sess.get('department','—')}</b>",
        f"🎓 Grade      : <b>{sess.get('grade','—')}</b>",
        f"📝 Title      : <b>{sess.get('title','—')}</b>",
        f"👤 Author     : <b>{sess.get('author','—')}</b>",
        f"🖼 Logo       : {'✅ received' if sess.get('logo_bytes') else '❌ missing'}",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(msg: types.Message):
    chat_id = msg.chat.id
    sessions.pop(chat_id, None)   # clear any old session

    welcome = (
        "👋 <b>Welcome to the Tikrit University Term Paper Generator!</b>\n\n"
        "I will ask you <b>7 quick questions</b>, then automatically write and "
        "format a professional academic term paper for you as a <b>.docx</b> file.\n\n"
        "Powered by <b>Claude AI</b> 🤖\n\n"
        "Type /generate to start, or /help for more info."
    )
    bot.send_message(chat_id, welcome, reply_markup=remove_kb())


# ─────────────────────────────────────────────
# /help
# ─────────────────────────────────────────────
@bot.message_handler(commands=["help"])
def cmd_help(msg: types.Message):
    text = (
        "<b>📖 How to use this bot:</b>\n\n"
        "1️⃣  /generate — Start a new term paper\n"
        "2️⃣  Answer 7 questions one by one\n"
        "3️⃣  Confirm your details\n"
        "4️⃣  Wait ~30 seconds while AI writes your paper\n"
        "5️⃣  Receive your <b>.docx</b> file, ready to open in Word!\n\n"
        "<b>Other commands:</b>\n"
        "/cancel — Stop and reset at any time\n"
        "/start  — Back to welcome screen\n\n"
        "<b>Tips:</b>\n"
        "• Send the logo as a <b>photo</b>, not as a file\n"
        "• The paper will have: cover page, introduction, 4 sections, conclusion, references\n"
        "• All content is written by Claude AI based on your topic"
    )
    bot.send_message(msg.chat.id, text)


# ─────────────────────────────────────────────
# /cancel
# ─────────────────────────────────────────────
@bot.message_handler(commands=["cancel"])
def cmd_cancel(msg: types.Message):
    sessions.pop(msg.chat.id, None)
    bot.send_message(
        msg.chat.id,
        "❌ <b>Session cancelled.</b>\nType /generate to start again.",
        reply_markup=remove_kb(),
    )


# ─────────────────────────────────────────────
# /generate — begin the wizard
# ─────────────────────────────────────────────
@bot.message_handler(commands=["generate"])
def cmd_generate(msg: types.Message):
    chat_id = msg.chat.id
    sessions[chat_id] = {}
    bot.send_message(
        chat_id,
        "✅ <b>Let's build your term paper!</b>\n\nAnswer each question below.\n"
        "You can type /cancel at any time to stop.\n\n"
        + STEP_QUESTIONS["university"],
        reply_markup=make_cancel_kb(),
    )


# ─────────────────────────────────────────────
# TEXT message handler — fills wizard fields
# ─────────────────────────────────────────────
@bot.message_handler(content_types=["text"])
def handle_text(msg: types.Message):
    chat_id = msg.chat.id
    text    = msg.text.strip()

    # Cancel button
    if text in ("❌ Cancel", "/cancel"):
        cmd_cancel(msg)
        return

    sess = sessions.get(chat_id)
    if sess is None:
        bot.send_message(chat_id, "Type /generate to start building a term paper.")
        return

    step = current_step(chat_id)
    if step is None:
        bot.send_message(chat_id, "All steps complete. Type /generate to start a new paper.")
        return

    # Logo step expects a photo, not text
    if step == "logo":
        bot.send_message(
            chat_id,
            "⚠️ Please <b>send a photo</b> (not text) for the university logo.",
            reply_markup=make_cancel_kb(),
        )
        return

    # "Confirm" / "Edit" step — after summary is shown
    if step == "__confirm__":
        if text.lower() in ("✅ confirm", "confirm", "yes", "ok"):
            _do_generate(chat_id)
        elif text.lower() in ("✏️ edit", "edit", "no"):
            sessions.pop(chat_id, None)
            bot.send_message(chat_id, "🔄 Let's start over.\n\n" + STEP_QUESTIONS["university"],
                             reply_markup=make_cancel_kb())
            sessions[chat_id] = {}
        return

    # Store value
    sess[step] = text

    # Advance to next step
    next_step = current_step(chat_id)
    if next_step is None:
        _show_summary(chat_id)
    else:
        bot.send_message(chat_id, STEP_QUESTIONS[next_step], reply_markup=make_cancel_kb())


# ─────────────────────────────────────────────
# PHOTO handler — receives the logo
# ─────────────────────────────────────────────
@bot.message_handler(content_types=["photo"])
def handle_photo(msg: types.Message):
    chat_id = msg.chat.id
    sess = sessions.get(chat_id)

    if sess is None:
        bot.send_message(chat_id, "Type /generate to start.")
        return

    step = current_step(chat_id)
    if step != "logo":
        bot.send_message(chat_id, "I wasn't expecting an image right now. Continue answering the questions.")
        return

    # Download the highest-resolution version of the photo
    file_id   = msg.photo[-1].file_id
    file_info = bot.get_file(file_id)
    logo_bytes = bot.download_file(file_info.file_path)

    sess["logo_bytes"] = logo_bytes
    log.info("Logo received for chat %s — %d bytes", chat_id, len(logo_bytes))

    # All steps done → show summary
    next_step = current_step(chat_id)
    if next_step is None:
        _show_summary(chat_id)


# ─────────────────────────────────────────────
# Summary / confirmation
# ─────────────────────────────────────────────
def _show_summary(chat_id: int):
    sess = sessions[chat_id]
    sessions[chat_id]["__step__"] = "__confirm__"   # mark as waiting for confirm

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(types.KeyboardButton("✅ Confirm"), types.KeyboardButton("✏️ Edit"))

    bot.send_message(
        chat_id,
        summary_text(sess) + "\n\n<b>Is everything correct?</b>",
        reply_markup=kb,
    )


# Handle confirm / edit via text (re-routed from handle_text via __confirm__ check)
@bot.message_handler(func=lambda m: (
    sessions.get(m.chat.id, {}).get("__step__") == "__confirm__"
    and m.content_type == "text"
))
def handle_confirm(msg: types.Message):
    chat_id = msg.chat.id
    text = msg.text.strip().lower()

    if text in ("✅ confirm", "confirm", "yes", "ok"):
        _do_generate(chat_id)
    else:
        sessions.pop(chat_id, None)
        bot.send_message(
            chat_id,
            "🔄 Let's start over.\n\n" + STEP_QUESTIONS["university"],
            reply_markup=make_cancel_kb(),
        )
        sessions[chat_id] = {}


# ─────────────────────────────────────────────
# Core generation
# ─────────────────────────────────────────────
def _do_generate(chat_id: int):
    sess = sessions.pop(chat_id, {})
    bot.send_message(
        chat_id,
        "⏳ <b>Generating your term paper…</b>\n\n"
        "Claude AI is writing the content (this takes about 30 seconds). "
        "Please wait ✨",
        reply_markup=remove_kb(),
    )

    try:
        log.info("Generating paper for chat %s — title: %s", chat_id, sess.get("title"))

        # Build content via Claude
        content = generate_paper_content(
            title      = sess["title"],
            api_key    = GEMINI_KEY,
            university = sess["university"],
            college    = sess["college"],
            department = sess["department"],
            grade      = sess["grade"],
        )

        # Write docx to a temp file
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp_path = tmp.name

        build_document(
            title      = sess["title"],
            author     = sess["author"],
            university = sess["university"],
            college    = sess["college"],
            department = sess["department"],
            grade      = sess["grade"],
            content    = content,
            logo_bytes = sess.get("logo_bytes"),
            output_path= tmp_path,
        )

        # Send the file
        safe_name = sess["title"].replace(" ", "_")[:40] + ".docx"
        with open(tmp_path, "rb") as f:
            bot.send_document(
                chat_id,
                f,
                visible_file_name=safe_name,
                caption=(
                    f"✅ <b>Your term paper is ready!</b>\n\n"
                    f"📝 <b>{sess['title']}</b>\n"
                    f"👤 {sess['author']}\n"
                    f"🏛 {sess['university']}\n\n"
                    f"Open it in <b>Microsoft Word</b> or <b>LibreOffice</b>."
                ),
            )
        Path(tmp_path).unlink(missing_ok=True)
        log.info("Paper sent to chat %s", chat_id)

    except Exception as e:
        log.exception("Error generating paper for chat %s", chat_id)
        bot.send_message(
            chat_id,
            f"❌ <b>Something went wrong:</b>\n<code>{e}</code>\n\n"
            "Please try again with /generate.",
            reply_markup=remove_kb(),
        )


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    log.info("Bot is starting — polling…")
    bot.infinity_polling(timeout=30, long_polling_timeout=20)

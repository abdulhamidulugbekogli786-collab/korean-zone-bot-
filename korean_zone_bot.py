import os
import logging
import asyncio
import random
from datetime import datetime, time
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Poll
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ChatMemberHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ChatMemberStatus

# ============================================================
# SOZLAMALAR — Railway "Variables" bo'limidan o'qiladi
# Bu yerga hech qachon token/key ni to'g'ridan-to'g'ri yozmang!
# ============================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@Koreanzone_tg")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN topilmadi! Railway > Variables bo'limiga qo'shing.")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY topilmadi! Railway > Variables bo'limiga qo'shing.")

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================
# GROQ CLIENT
# ============================================================
groq_client = Groq(api_key=GROQ_API_KEY)

# ============================================================
# KOREYS SO'ZLARI MA'LUMOT BAZASI
# ============================================================
KOREAN_WORDS = [
    {"word": "안녕하세요", "romanization": "Annyeonghaseyo", "meaning": "Salom (rasmiy)", "example": "안녕하세요! Men Abdulhamidman."},
    {"word": "감사합니다", "romanization": "Gamsahamnida", "meaning": "Rahmat (rasmiy)", "example": "도와주셔서 감사합니다. — Yordamingiz uchun rahmat."},
    {"word": "사랑해요", "romanization": "Saranghaeyo", "meaning": "Sevaman", "example": "당신을 사랑해요. — Sizni sevaman."},
    {"word": "괜찮아요", "romanization": "Gwaenchanayo", "meaning": "Yaxshi / Muammo yo'q", "example": "괜찮아요? — Yaxshimisiz?"},
    {"word": "맛있어요", "romanization": "Masisseoyo", "meaning": "Mazali", "example": "김치가 맛있어요. — Kimchi mazali."},
    {"word": "학교", "romanization": "Hakgyo", "meaning": "Maktab", "example": "저는 학교에 가요. — Men maktabga boraman."},
    {"word": "친구", "romanization": "Chingu", "meaning": "Do'st", "example": "제 친구는 한국 사람이에요. — Do'stim koreyslik."},
    {"word": "음식", "romanization": "Eumsik", "meaning": "Ovqat", "example": "한국 음식을 좋아해요. — Men koreys ovqatini yaxshi ko'raman."},
    {"word": "물", "romanization": "Mul", "meaning": "Suv", "example": "물 한 잔 주세요. — Bir stakan suv bering."},
    {"word": "집", "romanization": "Jip", "meaning": "Uy", "example": "저는 집에 있어요. — Men uydaman."},
]

GRAMMAR_LESSONS = [
    {
        "title": "이에요/예요 — 'Bu ... dir' konstruksiyasi",
        "content": """📖 *Grammatika: 이에요/예요*

Bu konstruksiya inglizchada "is/am/are" ga o'xshaydi.

*Qoida:*
• Undosh bilan tugagan so'zdan keyin → *이에요*
• Unli bilan tugagan so'zdan keyin → *예요*

*Misollar:*
• 학생이에요 — Men talabaman
• 의사예요 — Men doktorman
• 한국 사람이에요 — Men koreyslikman

*Mashq:*
"Men o'qituvchiman" ni koreyschada qanday aytasiz?
Javob: 선생님이에요 (Seonsaengnim-ieyo)""",
    },
    {
        "title": "을/를 — Tushum kelishigi",
        "content": """📖 *Grammatika: 을/를 (Tushum kelishigi)*

*Qoida:*
• Undosh bilan tugagan so'zdan keyin → *을*
• Unli bilan tugagan so'zdan keyin → *를*

*Misollar:*
• 밥을 먹어요 — Ovqat yeyapman
• 물을 마셔요 — Suv ichyapman
• 음악을 들어요 — Musiqa tinglayapman

*Eslab qoling:* Bu qo'shimcha harakat ob'ektini belgilaydi.""",
    },
]

# ============================================================
# AI YORDAMIDA KONTENT YARATISH
# ============================================================
async def generate_ai_content(prompt: str) -> str:
    """Groq AI orqali kontent yaratish"""
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """Siz Korean Zone Telegram kanalining yordamchisisiz. 
                    Kanal koreys tilini o'zbek va rus tilida o'rgatadi.
                    Javoblaringiz qisqa, qiziqarli va ta'limiy bo'lsin.
                    Emoji ishlatishingiz mumkin."""
                },
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            max_tokens=500,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API xatosi: {e}")
        return "Hozircha AI javob bera olmayapti. Keyinroq urinib ko'ring."

# ============================================================
# KUNLIK SO'Z FUNKSIYASI
# ============================================================
async def send_daily_word(context: ContextTypes.DEFAULT_TYPE):
    """Har kuni ertalab yangi so'z yuborish"""
    word_data = random.choice(KOREAN_WORDS)

    message = f"""🇰🇷 *Kunlik So'z — Word of the Day*

✨ *{word_data['word']}*
🔤 Talaffuz: _{word_data['romanization']}_
🇺🇿 Ma'nosi: *{word_data['meaning']}*

📝 *Misol:*
_{word_data['example']}_

━━━━━━━━━━━━━━
📚 {CHANNEL_ID} — Koreys tilini o'rganamiz!"""

    try:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode="Markdown"
        )
        logger.info("Kunlik so'z yuborildi")
    except Exception as e:
        logger.error(f"Kunlik so'z yuborishda xato: {e}")

# ============================================================
# HAFTALIK GRAMMATIKA
# ============================================================
async def send_weekly_grammar(context: ContextTypes.DEFAULT_TYPE):
    """Har hafta grammatika darsi yuborish"""
    lesson = random.choice(GRAMMAR_LESSONS)

    message = f"""📚 *Haftalik Grammatika Darsi*

*{lesson['title']}*

{lesson['content']}

━━━━━━━━━━━━━━
🎓 {CHANNEL_ID} — Koreys tilini o'rganamiz!"""

    try:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Grammatika yuborishda xato: {e}")

# ============================================================
# VIKTORINA TEST
# ============================================================
async def send_daily_quiz(context: ContextTypes.DEFAULT_TYPE):
    """Kunlik viktorina yuborish"""
    word_data = random.choice(KOREAN_WORDS)

    correct = word_data['meaning']
    all_meanings = [w['meaning'] for w in KOREAN_WORDS if w['meaning'] != correct]
    wrong_answers = random.sample(all_meanings, min(3, len(all_meanings)))

    options = wrong_answers + [correct]
    random.shuffle(options)
    correct_index = options.index(correct)

    try:
        await context.bot.send_poll(
            chat_id=CHANNEL_ID,
            question=f"🧩 {word_data['word']} — bu so'zning ma'nosi nima?",
            options=options,
            type=Poll.QUIZ,
            correct_option_id=correct_index,
            explanation=f"✅ To'g'ri! {word_data['word']} = {word_data['meaning']}\n🔤 Talaffuz: {word_data['romanization']}",
            is_anonymous=True,
        )
    except Exception as e:
        logger.error(f"Viktorina yuborishda xato: {e}")

# ============================================================
# YANGI A'ZO KUTIB OLISH
# ============================================================
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi a'zoga xush kelibsiz xabari"""
    if update.chat_member is None:
        return

    new_member = update.chat_member.new_chat_member
    old_member = update.chat_member.old_chat_member

    if (old_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED] and
            new_member.status == ChatMemberStatus.MEMBER):

        user = new_member.user
        name = user.first_name or "Do'st"

        welcome_text = f"""🇰🇷 *Annyeonghaseyo, {name}!* 안녕하세요!

*Korean Zone* kanaliga xush kelibsiz! 🌸

Bu yerda siz topasiz:
📚 Kunlik koreys so'zlari
🧩 Interaktiv testlar  
📖 Grammatika darslari
🎵 K-pop va drama yangiliklari
🇰🇷 Koreya madaniyati haqida

*Qayerdan boshlash kerak?*
👇 Quyidagi postlarni ko'ring va o'rganishni boshlang!

*화이팅!* (Hwaitingi!) — Omad! 💪

━━━━━━━━━━━━━━
📌 Admin: @Seulcom"""

        try:
            await context.bot.send_message(
                chat_id=update.chat_member.chat.id,
                text=welcome_text,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Xush kelibsiz xabarida xato: {e}")

# ============================================================
# SPAM HIMOYA
# ============================================================
SPAM_WORDS = [
    "реклама", "reklama", "заработок", "pul ishlash", "casino", "казино",
    "кредит", "kredit", "займ", "qarz", "18+", "xxx", "porn",
]

async def check_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Spam xabarlarni aniqlash va o'chirish"""
    if update.message is None:
        return

    message = update.message
    user = message.from_user
    text = message.text or message.caption or ""

    try:
        chat_member = await context.bot.get_chat_member(message.chat_id, user.id)
        if chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return
    except Exception:
        pass

    is_spam = False

    text_lower = text.lower()
    for spam_word in SPAM_WORDS:
        if spam_word in text_lower:
            is_spam = True
            break

    if message.entities:
        for entity in message.entities:
            if entity.type in ["url", "text_link"]:
                is_spam = True
                break

    if is_spam:
        try:
            await message.delete()
            await context.bot.ban_chat_member(message.chat_id, user.id)
            await context.bot.send_message(
                chat_id=message.chat_id,
                text=f"🚫 {user.first_name} spam yuborgan. Foydalanuvchi bloklandi.",
            )
            logger.info(f"Spam: {user.id} bloklandi")
        except Exception as e:
            logger.error(f"Spam bloklashda xato: {e}")

# ============================================================
# /START KOMANDASI
# ============================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot boshlanish komandasi"""
    text = f"""🇰🇷 *Annyeonghaseyo!* 안녕하세요!

Men *Korean Zone* kanalining yordamchi botiman!

*Nima qila olaman:*
📚 Kunlik koreys so'zi
🧩 Viktorina testlar  
📖 Grammatika darslari
🛡️ Spam himoya
👋 Yangi a'zolarni kutib olish

*Korean Zone kanaliga obuna bo'ling:*
👉 {CHANNEL_ID}

*화이팅!* 💪"""

    await update.message.reply_text(text, parse_mode="Markdown")

# ============================================================
# /WORD KOMANDASI — MANUAL SO'Z
# ============================================================
async def word_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tasodifiy koreys so'zi ko'rsatish"""
    word_data = random.choice(KOREAN_WORDS)

    text = f"""🇰🇷 *Koreys So'zi*

✨ *{word_data['word']}*
🔤 _{word_data['romanization']}_
🇺🇿 {word_data['meaning']}

📝 _{word_data['example']}_"""

    await update.message.reply_text(text, parse_mode="Markdown")

# ============================================================
# /ASK KOMANDASI — AI GA SAVOL
# ============================================================
async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI ga savol berish"""
    if not context.args:
        await update.message.reply_text(
            "❓ Savol yozing: /ask <savolingiz>\n\nMasalan: /ask annyeong so'zining ma'nosi nima?"
        )
        return

    question = " ".join(context.args)
    await update.message.reply_text("⏳ Javob tayyorlanmoqda...")

    prompt = f"Koreys tili haqida savol: {question}. O'zbek tilida qisqa va aniq javob ber."
    answer = await generate_ai_content(prompt)

    await update.message.reply_text(f"🤖 *Javob:*\n\n{answer}", parse_mode="Markdown")

# ============================================================
# ASOSIY FUNKSIYA
# ============================================================
def main():
    """Botni ishga tushirish"""
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("word", word_command))
    app.add_handler(CommandHandler("ask", ask_command))

    app.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_spam))

    job_queue = app.job_queue

    job_queue.run_daily(
        send_daily_word,
        time=time(hour=8, minute=0),
        name="daily_word"
    )

    job_queue.run_daily(
        send_daily_quiz,
        time=time(hour=18, minute=0),
        name="daily_quiz"
    )

    job_queue.run_daily(
        send_weekly_grammar,
        time=time(hour=10, minute=0),
        days=(0,),
        name="weekly_grammar"
    )

    logger.info("Korean Zone Bot ishga tushdi! 🇰🇷")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

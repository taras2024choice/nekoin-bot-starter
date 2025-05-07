import logging
import os
import uuid

from telegram import Update, Poll, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from dotenv import load_dotenv

# Load env and logging
load_dotenv()
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Moderation store
pending = {}  # mod_id -> (description, option1, option2, user_id)
ADMIN_CHAT = 396948407

# Conversation states
DESCRIPTION, OPTION1, OPTION2 = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
     rules = (
         "Привіт! Я бот NEKOIN CHOICE.\n\n"
         "📝 Правила:\n"
         "  • Надсилай лише законні та етичні дилеми. Екстремізм, мова ворожнечі, сексуальний та шок-контент — заборонено.\n"
         "  • Заборонено спам, рекламу та особисті образи.\n"
         "  • Дилеми проходять модерацію перед публікацією.\n\n"
         "❗️ Усі рішення приймає спільнота — бот не несе відповідальності за наслідки голосування. Ми не даємо юридичних, фінансових чи медичних порад.\n\n"
         "Тепер напиши суть твоєї дилеми:"
     )
     await update.message.reply_text(rules)
     return DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    await update.message.reply_text("Окей, тепер введи перший варіант.")
    return OPTION1

async def get_option1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['option1'] = update.message.text
    await update.message.reply_text("А тепер другий варіант.")
    return OPTION2

async def get_option2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Save second option
    context.user_data['option2'] = update.message.text
    desc = context.user_data['description']
    o1 = context.user_data['option1']
    o2 = context.user_data['option2']

    # Send for moderation
    mod_id = str(uuid.uuid4())
    pending[mod_id] = (desc, o1, o2, update.effective_user.id)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Одобрити", callback_data=f"approve#{mod_id}"),
        InlineKeyboardButton("❌ Відхилити", callback_data=f"reject#{mod_id}"),
    ]])
    await context.bot.send_message(
        chat_id = 396948407,
        text=f"🔎 Нова дилема на модерації:\n\n❓ {desc}\n1️⃣ {o1}\n2️⃣ {o2}",
        reply_markup=kb
    )
    await update.message.reply_text("Дилему відправлено на модерацію, дам знати результат ✌️")
    return ConversationHandler.END

async def moderate_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, mod_id = query.data.split("#", 1)
    record = pending.pop(mod_id, None)
    if not record:
        return await query.edit_message_text("⚠️ Запис не знайдено.")
    desc, o1, o2, user_id = record

    if action == "approve":
        await context.bot.send_poll(
            chat_id="@nekoin_choice",
            question=f"🔥 {desc}",
            options=[o1, o2],
            is_anonymous=True,
            allows_multiple_answers=False,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Створи свою дилему", url="https://t.me/NEKOINChoiceBot")
            ]])
        )
        await context.bot.send_message(user_id, "🎉 Дилему схвалено й опубліковано @nekoin_choice! Поділися нею з друзями")
        await query.edit_message_text("✅ Опубліковано в @nekoin_choice")
    else:
        await context.bot.send_message(user_id, "😕 Дилему відхилено модератором.")
        await query.edit_message_text("❌ Дилему відхилено")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "NEKOIN CHOICE — довідка\n\n"
        "📝 Правила:\n"
        "  • Надсилай лише законні та етичні дилеми. Екстремізм, мова ворожнечі, сексуальний та шок-контент — заборонено.\n"
        "  • Без спаму, реклами чи образ.\n"
        "  • Усі дилеми проходять модерацію.\n\n"
        "⚠️ Дислеймер:\n"
        "  Усі рішення приймає спільнота — бот не несе відповідальності за наслідки голосування. Ми не даємо юридичних, фінансових чи медичних порад.\n\n"
        "Щоб створити нову дилему — виконай /start"
    )
    await update.message.reply_text(text)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            OPTION1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_option1)],
            OPTION2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_option2)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(moderate_cb, pattern="^(approve|reject)#"))
    app.add_handler(CommandHandler("help", help_command))
    app.run_polling()

if __name__ == "__main__":
    main()


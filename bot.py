import os
import csv
from datetime import datetime
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.ext import MessageHandler, filters

from transformers import pipeline

# Load environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt2")
PROMPT_PATH = os.getenv("PROMPT_PATH", "prompt.txt")

if TOKEN is None:
    raise RuntimeError("TELEGRAM_TOKEN environment variable not set")

# Load system prompt
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

# Load text generation pipeline
text_generator = pipeline("text-generation", model=MODEL_NAME)

def generate_variants(user_text: str, n: int = 2) -> List[str]:
    prompt = f"{SYSTEM_PROMPT}\nUser: {user_text}\nGremlin:" 
    outputs = text_generator(prompt, max_new_tokens=len(user_text.split()) + 5, num_return_sequences=n, do_sample=True, temperature=0.8)
    variants = []
    for out in outputs:
        text = out["generated_text"].split("Gremlin:")[-1].strip()
        variants.append(text)
    return variants

async def sproto_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = update.message.text
    if not user_input:
        return
    text = user_input[len('/sproto'):].strip().strip('"')
    if not text:
        await update.message.reply_text("Usage: /sproto your text here")
        return
    variants = generate_variants(text, n=2)
    for i, variant in enumerate(variants, start=1):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👍", callback_data=f"up|{variant}"),
             InlineKeyboardButton("👎", callback_data=f"down|{variant}")]
        ])
        await update.message.reply_text(variant, reply_markup=keyboard)

async def feedback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    vote, text = query.data.split("|", 1)
    user = update.effective_user.id
    with open("feedback.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.utcnow().isoformat(), user, vote, text])
    await query.edit_message_reply_markup(reply_markup=None)

async def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("sproto", sproto_command))
    app.add_handler(CallbackQueryHandler(feedback_handler))
    app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

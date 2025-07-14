import os
import csv
from datetime import datetime
from typing import List

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
except ImportError as e:
    raise ImportError(
        "python-telegram-bot is required. Install dependencies with 'pip install -r requirements.txt'"
    ) from e

import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
PROMPT_PATH = os.getenv("PROMPT_PATH", "prompt.txt")
openai.api_key = os.getenv("OPENAI_API_KEY")

if TOKEN is None:
    raise RuntimeError("TELEGRAM_TOKEN environment variable not set")

# Load system prompt
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()


def generate_variants(user_text: str, n: int = 2) -> List[str]:
    variants = []
    
    # Simple templates for Sproto Gremlin style responses
    templates = [
        f"Gremlin sees '{user_text}' and goes BRRRR! 🐸💚 Much chaos, very mischief!",
        f"Sproto Gremlin says: {user_text} but make it GREMLINY! 🦈✨ To the moon!",
        f"*gremlin noises* {user_text}? More like {user_text.upper()}!!! 🚀🐸",
        f"Gremlin wisdom: {user_text} + chaos = PROFIT! 💎🙌 hodl hodl hodl",
        f"Sproto vibes: {user_text} but with extra GREMLIN ENERGY! ⚡🐸💚"
    ]
    
    # Generate gremlin-style text using GPT-4
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            temperature=0.9,
            n=n
        )
        for choice in response.choices:
            variant = choice.message.content.strip().split('\n')[0].strip()
            if (variant and len(variant) > 5 and len(variant) < 280 and
                    not variant.startswith('http') and
                    not variant.startswith('[') and
                    not variant.startswith('@')):
                variants.append(variant)
    except Exception as e:
        print(f"OpenAI API call failed: {e}")
    
    # Fill remaining slots with template responses
    import random
    while len(variants) < n:
        template = random.choice(templates)
        if template not in variants:
            variants.append(template)
    
    return variants[:n]

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
        # Use shorter callback data to avoid 64-byte limit
        callback_id = f"{update.effective_user.id}_{i}_{hash(variant) % 10000}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👍", callback_data=f"up|{callback_id}"),
             InlineKeyboardButton("👎", callback_data=f"down|{callback_id}")]
        ])
        # Store the full text in context for later retrieval
        context.bot_data[callback_id] = variant
        await update.message.reply_text(variant, reply_markup=keyboard)

async def feedback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    vote, callback_id = query.data.split("|", 1)
    user = update.effective_user.id
    
    # Retrieve the stored text using callback_id
    text = context.bot_data.get(callback_id, "Unknown text")
    
    with open("feedback.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.utcnow().isoformat(), user, vote, text])
    
    # Clean up stored data
    if callback_id in context.bot_data:
        del context.bot_data[callback_id]
    
    await query.edit_message_reply_markup(reply_markup=None)

def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("sproto", sproto_command))
    app.add_handler(CallbackQueryHandler(feedback_handler))
    app.run_polling()

if __name__ == "__main__":
    main()

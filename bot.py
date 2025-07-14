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

from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
PROMPT_PATH = os.getenv("PROMPT_PATH", "prompt.txt")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if TOKEN is None:
    raise RuntimeError("TELEGRAM_TOKEN environment variable not set")

# Load system prompt
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()


def generate_variants(user_text: str, n: int = 2) -> List[str]:
    variants = []
    
    # Generate gremlin-style text using GPT-4 with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.9,
                n=n
            )
            for choice in response.choices:
                variant = choice.message.content.strip()
                if (
                    variant
                    and len(variant) < 500
                    and not variant.startswith('http')
                    and not variant.startswith('[')
                ):
                    variants.append(variant)
            
            # If we got enough variants, break out of retry loop
            if len(variants) >= n:
                break
                
        except Exception as e:
            print(f"OpenAI API call failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                # On final failure, return a simple error message
                return [f"*gremlin temporarily unavailable* 🐸💔 Try again in a moment!"]
    
    # If we didn't get enough variants, make additional API calls
    while len(variants) < n:
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.9,
                n=1
            )
            variant = response.choices[0].message.content.strip()
            if (
                variant
                and len(variant) < 500
                and not variant.startswith('http')
                and not variant.startswith('[')
                and variant not in variants
            ):
                variants.append(variant)
        except Exception as e:
            print(f"Additional OpenAI API call failed: {e}")
            break
    
    return variants[:n] if variants else [f"*gremlin temporarily unavailable* 🐸💔 Try again in a moment!"]

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

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

from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
PROMPT_PATH = os.getenv("PROMPT_PATH", "prompt.txt")

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

if TOKEN is None:
    raise RuntimeError("TELEGRAM_TOKEN environment variable not set")

# Load system prompt
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()


def generate_variants(user_text: str, n: int = 2) -> List[str]:
    variants = []
    
    # Generate gremlin-style text using Claude with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                temperature=0.9,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_text}
                ]
            )
            
            # Claude returns a single response, so we need to parse it for multiple variants
            content = response.content[0].text.strip()
            
            # Split the response into variants (assuming they're separated by newlines or numbers)
            # The prompt asks for "two alternate tweet-sized responses"
            lines = content.split('\n')
            current_variant = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check if this line starts a new variant (numbered or bulleted)
                if (line.startswith(('1.', '2.', '3.', '4.', '5.')) or 
                    line.startswith(('• ', '- ', '* ')) or
                    line.startswith(('Option 1:', 'Option 2:', 'Variant 1:', 'Variant 2:'))):
                    
                    # Save the previous variant if it exists
                    if current_variant:
                        clean_variant = current_variant.strip()
                        if (clean_variant and len(clean_variant) < 500 and 
                            not clean_variant.startswith('http') and 
                            not clean_variant.startswith('[')):
                            variants.append(clean_variant)
                    
                    # Start new variant, removing the prefix
                    current_variant = line
                    for prefix in ['1.', '2.', '3.', '4.', '5.', '• ', '- ', '* ', 
                                   'Option 1:', 'Option 2:', 'Variant 1:', 'Variant 2:']:
                        if current_variant.startswith(prefix):
                            current_variant = current_variant[len(prefix):].strip()
                            break
                else:
                    # Continue the current variant
                    if current_variant:
                        current_variant += " " + line
                    else:
                        current_variant = line
            
            # Don't forget the last variant
            if current_variant:
                clean_variant = current_variant.strip()
                if (clean_variant and len(clean_variant) < 500 and 
                    not clean_variant.startswith('http') and 
                    not clean_variant.startswith('[')):
                    variants.append(clean_variant)
            
            # If we still don't have variants, treat the whole response as one
            if not variants and content:
                clean_content = content.strip()
                if (clean_content and len(clean_content) < 500 and 
                    not clean_content.startswith('http') and 
                    not clean_content.startswith('[')):
                    variants.append(clean_content)
            
            # If we got enough variants, break out of retry loop
            if len(variants) >= n:
                break
                
        except Exception as e:
            print(f"Claude API call failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                # On final failure, return a simple error message
                return [f"*gremlin temporarily unavailable* 🐸💔 Try again in a moment!"]
    
    # If we didn't get enough variants, make additional API calls
    while len(variants) < n:
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                temperature=0.9,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_text}
                ]
            )
            
            content = response.content[0].text.strip()
            if (content and len(content) < 500 and 
                not content.startswith('http') and 
                not content.startswith('[') and 
                content not in variants):
                variants.append(content)
        except Exception as e:
            print(f"Additional Claude API call failed: {e}")
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

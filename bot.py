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
    variants = []
    
    # Simple templates for Sproto Gremlin style responses
    templates = [
        f"Gremlin sees '{user_text}' and goes BRRRR! 🐸💚 Much chaos, very mischief!",
        f"Sproto Gremlin says: {user_text} but make it GREMLINY! 🦈✨ To the moon!",
        f"*gremlin noises* {user_text}? More like {user_text.upper()}!!! 🚀🐸",
        f"Gremlin wisdom: {user_text} + chaos = PROFIT! 💎🙌 hodl hodl hodl",
        f"Sproto vibes: {user_text} but with extra GREMLIN ENERGY! ⚡🐸💚"
    ]
    
    # Try GPT-2 generation first
    try:
        prompt = f"Rewrite this in a playful crypto gremlin style: {user_text}\n\nGremlin version:"
        outputs = text_generator(
            prompt, 
            max_new_tokens=30,
            num_return_sequences=n, 
            do_sample=True, 
            temperature=0.9,
            pad_token_id=text_generator.tokenizer.eos_token_id,
            repetition_penalty=1.2
        )
        
        for out in outputs:
            full_text = out["generated_text"]
            if "Gremlin version:" in full_text:
                generated = full_text.split("Gremlin version:")[-1].strip()
            else:
                generated = full_text[len(prompt):].strip()
            
            # Clean up and validate
            generated = generated.split('\n')[0].strip()  # Take first line only
            
            # Remove problematic patterns
            if (generated and 
                len(generated) > 5 and 
                len(generated) < 200 and
                not generated.startswith('http') and
                not generated.startswith('[') and
                not generated.startswith('@') and
                'github.com' not in generated.lower() and
                'bit.ly' not in generated.lower() and
                't.co' not in generated.lower()):
                variants.append(generated)
    except Exception as e:
        print(f"GPT-2 generation failed: {e}")
    
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

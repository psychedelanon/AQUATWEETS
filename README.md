# AQUATWEETS

This repository contains the code for **Sproto Gremlin Bot**, a Telegram DM bot that rewrites your thoughts in the voice of the Sproto Gremlin. It responds to the `/sproto` command with two tweet-style variants and lets you give feedback via 👍/👎 buttons.

## Features

- Runs in private Telegram chats
- Uses a local system prompt stored in `prompt.txt`
- Generates two variations for each `/sproto` command using OpenAI GPT-4
- Records feedback in `feedback.csv`

## Requirements

- Python 3.8+
- The packages listed in `requirements.txt`
- A Telegram bot token set in the `TELEGRAM_TOKEN` environment variable

Set `OPENAI_API_KEY` and `PROMPT_PATH` as needed to use a custom prompt file.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. Set `TELEGRAM_TOKEN` in your environment.
2. Run the bot:

```bash
python bot.py
```

Send `/sproto your text` to the bot in a DM and it will reply with two gremlin-style tweets. Click 👍 or 👎 under each message to record feedback.

Feedback is appended to `feedback.csv` for later analysis.

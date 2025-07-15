# AQUATWEETS

This repository contains the code for **Sproto Gremlin Bot**, a Telegram DM bot that rewrites your thoughts in the voice of the Sproto Gremlin. It responds to the `/sproto` command with two tweet-style variants and lets you give feedback via 👍/👎 buttons.

## Features

- Runs in private Telegram chats
- Uses a local system prompt stored in `prompt.txt`
- Generates two variations for each `/sproto` command using Anthropic Claude
- Records feedback in `feedback.csv`

## Requirements

- Python 3.8+
- The packages listed in `requirements.txt`
- A Telegram bot token set in the `TELEGRAM_TOKEN` environment variable
- An Anthropic API key set in the `ANTHROPIC_API_KEY` environment variable

Set `PROMPT_PATH` as needed to use a custom prompt file (defaults to `prompt.txt`).

## Installation

```bash
pip install -r requirements.txt
```

If you see `ModuleNotFoundError: No module named 'telegram'`, make sure you've
installed the packages in the same Python environment by running the command
above.
If the gremlin still won't behave, run it again—he loves extra mulch.

## Usage

1. Set `TELEGRAM_TOKEN` in your environment.
2. Run the bot:

```bash
python bot.py
```

Send `/sproto your text` to the bot in a DM and it will reply with two gremlin-style tweets. Click 👍 or 👎 under each message to record feedback.

Feedback is appended to `feedback.csv` for later analysis.

## Railway Deployment

To deploy this bot to Railway for 24/7 operation:

1. **Prepare your repository:**
   - Ensure all files are committed to your git repository
   - The `Procfile` and `requirements.txt` are already configured for Railway

2. **Deploy to Railway:**
   - Go to [railway.app](https://railway.app) and sign up/login
   - Click "New Project" → "Deploy from GitHub repo"
   - Connect your GitHub account and select this repository
   - Railway will automatically detect it as a Python project

3. **Set Environment Variables:**
   - In your Railway project dashboard, go to the "Variables" tab
   - Add the following environment variables:
     ```
     TELEGRAM_TOKEN=your_telegram_bot_token_here
     ANTHROPIC_API_KEY=your_anthropic_api_key_here
     ```
   - Optionally set `PROMPT_PATH=prompt.txt` (though this is the default)

4. **Deploy:**
   - Railway will automatically build and deploy your bot
   - Check the "Deployments" tab to monitor the build process
   - Once deployed, your bot will be running 24/7

**Note:** Railway offers a free tier with usage limits. Monitor your usage in the Railway dashboard to avoid unexpected charges.

### Getting Required API Keys

- **Telegram Bot Token:** Message [@BotFather](https://t.me/botfather) on Telegram, create a new bot with `/newbot`, and copy the token
- **Anthropic API Key:** Sign up at [console.anthropic.com](https://console.anthropic.com), go to API Keys, and create a new key

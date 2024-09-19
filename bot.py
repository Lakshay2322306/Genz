import os
import random
import string
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
from flask import Flask, request

# Initialize Flask app
app = Flask(__name__)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "YOUR_OWNER_ID"))
OWNER_NAME = os.getenv("OWNER_NAME", "OwnerName")
BINLIST_URL = "https://binlist.net/"
VALID_CARD_URL = "https://example.com/check_card"  # Replace with actual card validation service

# Generate random credit card numbers
def generate_card_number():
    return ''.join(random.choices(string.digits, k=16))

# Validate card number using Luhn's algorithm
def luhn_check(card_number: str) -> bool:
    card_number = card_number.replace(' ', '')
    total = 0
    reverse_digits = card_number[::-1]
    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0

# Command Handlers
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"👋 Hello {user.first_name}! Welcome to the Credit Card Utility Bot.\n\n"
             "✨ Use /help to see available commands and explore our features! 🎉"
    )

async def help_command(update: Update, context: CallbackContext) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="📚 Available commands:\n"
             "/start - Welcome message with emojis 😊\n"
             "/generate - Generate a random credit card number 🎟️\n"
             "/bin - Lookup BIN information 🔍\n"
             "/check - Validate a credit card number ✅\n"
             "/inline - Interactive buttons example ✨\n"
             "/status - Get bot status 🟢\n"
             "/credits - View credits and acknowledgements 🎖️"
    )

async def generate(update: Update, context: CallbackContext) -> None:
    result = generate_card_number()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🎟️ Your generated credit card number is:\n`{result}`",
        parse_mode='Markdown'
    )

async def bin_lookup(update: Update, context: CallbackContext) -> None:
    bin_number = ' '.join(context.args).strip()
    if not bin_number:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🚫 Please provide a BIN number."
        )
        return

    response = requests.get(f"{BINLIST_URL}{bin_number}")
    data = response.json()

    result = (
        f"🔍 BIN Lookup Result:\n"
        f"**BIN:** {data.get('number', 'Unknown')}\n"
        f"**Brand:** {data.get('scheme', 'Unknown')}\n"
        f"**Type:** {data.get('type', 'Unknown')}\n"
        f"**Category:** {data.get('category', 'Unknown')}\n"
        f"**Bank:** {data.get('bank', {}).get('name', 'Unknown')}\n"
        f"**Country:** {data.get('country', {}).get('name', 'Unknown')}"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=result,
        parse_mode='Markdown'
    )

async def check_card(update: Update, context: CallbackContext) -> None:
    card_number = ' '.join(context.args).strip()
    if not card_number:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🚫 Please provide a credit card number."
        )
        return

    is_valid = luhn_check(card_number)
    result = f"🔍 Card Number: `{card_number}`\n" \
             f"**Validity:** {'Valid ✅' if is_valid else 'Invalid ❌'}"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=result,
        parse_mode='Markdown'
    )

async def inline(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Generate Card 🎟️", callback_data='generate')],
        [InlineKeyboardButton("BIN Lookup 🔍", callback_data='bin')],
        [InlineKeyboardButton("Check Card ✅", callback_data='check')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="✨ Choose an option:",
        reply_markup=reply_markup
    )

async def status(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id == OWNER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🟢 The bot is currently running smoothly!"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🚫 You do not have permission to view the bot status."
        )

async def credits(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id == OWNER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🌟 **Credits:**\n"
                 "This bot was created with ❤️ by @Jukerhenapadega.\n"
                 "Special thanks to the libraries and APIs used! 🙌"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🚫 You do not have permission to view credits."
        )

# Flask route for webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    logger.info(f'Received webhook data: {data}')

    if not data or 'message' not in data:
        logger.warning("No valid message data received in the webhook request.")
        return "No valid message data received", 400

    message = data.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    text = message.get('text', "").strip()

    logger.info(f'Received message from chat_id {chat_id}: "{text}"')

    if chat_id and text:
        if text.startswith('/bin'):
            bin_lookup(update=Update(message=message, effective_chat=Update(message=message, effective_chat={'id': chat_id})), context=None)
        elif text.startswith('/check'):
            check_card(update=Update(message=message, effective_chat=Update(message=message, effective_chat={'id': chat_id})), context=None)
        elif text.startswith('/status'):
            status(update=Update(message=message, effective_chat=Update(message=message, effective_chat={'id': chat_id})), context=None)
        elif text.startswith('/credits'):
            credits(update=Update(message=message, effective_chat=Update(message=message, effective_chat={'id': chat_id})), context=None)
        else:
            await context.bot.send_message(chat_id=chat_id, text="🚫 Unknown command. Use /help for a list of commands.")
        return "OK", 200

    logger.warning("Chat ID or text missing in the message.")
    return "Chat ID or text missing", 400

@app.route('/')
def home():
    return "Welcome to the Credit Card Utility Bot!"

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("generate", generate))
    application.add_handler(CommandHandler("bin", bin_lookup))
    application.add_handler(CommandHandler("check", check_card))
    application.add_handler(CommandHandler("inline", inline))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("credits", credits))

    application.add_handler(CallbackQueryHandler(generate, pattern='generate'))
    application.add_handler(CallbackQueryHandler(bin_lookup, pattern='bin'))
    application.add_handler(CallbackQueryHandler(check_card, pattern='check'))

    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://files-checker.onrender.com/{BOT_TOKEN}"
    )

if __name__ == '__main__':
    main()

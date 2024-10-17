from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ApplicationBuilder
import logging

# Log darajasini va formatini sozlaymiz
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



async def start_command(update: Update, context: ContextTypes):
    first_name = update.message.from_user.first_name
    logging.info(f"User - {first_name}, started the bot")
    await update.message.reply_text("Assalomu alaykum!")



def main():
    app = ApplicationBuilder().token('7443434643:AAENS8ekE0RFt1tQfE9kCSfhR_Nur7W-ST8').build()

    app.add_handler(CommandHandler('start', start_command))



    app.run_polling()

if __name__=="__main__":
    main()
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import yfinance as yf
import pandas as pd
import os

# Bot tokeningiz va admin user ID
BOT_TOKEN = '8033330302:AAHcBUvf2PgB1vSI3pb5fDcA-2YYpedlAH8'
ADMIN_ID = 6214462946
EXCEL_INPUT = 'Aksiyalar-symboli.xlsx'
EXCEL_OUTPUT = 'stack_info.xlsx'

async def start(update, context):
    await update.message.reply_text(f"Assalomu alaykum {update.message.from_user.first_name}")

def atr(ticker):
    data = yf.download(ticker, period="3mo", interval="1d")
    if data.empty:
        return None
    data['H-L'] = data['High'] - data['Low']
    data['H-PC'] = abs(data['High'] - data['Close'].shift(1))
    data['L-PC'] = abs(data['Low'] - data['Close'].shift(1))
    data['TR'] = data[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    data['ATR14'] = data['TR'].rolling(window=14, min_periods=1).mean()
    latest_atr14 = data['ATR14'].iloc[-1] if not data['ATR14'].isna().all() else None
    return latest_atr14

async def fetch_stock_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        options = stock.options
        total_call_volume = 0
        total_put_volume = 0

        for option_date in options:
            option_chain = stock.option_chain(option_date)
            calls = option_chain.calls
            puts = option_chain.puts
            total_call_volume += calls['volume'].sum()
            total_put_volume += puts['volume'].sum()

        data = stock.history(period="1d")
        row = {
            "Aksiya": ticker_symbol,
            "Current Price": data["Close"].iloc[0] if not data["Close"].isna().iloc[0] else 0,
            "Volume": data["Volume"].iloc[0] if not data["Volume"].isna().iloc[0] else 0,
            "ATR14": atr(ticker_symbol) or 0,
            "Short Float %": stock.info.get("shortPercentOfFloat") or 0,
            "Institutional Ownership %": (stock.info.get("heldPercentInstitutions") or 0) * 100,
            "Income (M)": stock.info.get("netIncomeToCommon", 0) / 1e6,
            "Market Cap (M)": (stock.info.get("marketCap") or 0) / 1_000_000,
            "Options PUT volume": total_put_volume,
            "Options CALL volume": total_call_volume,
            "1 yil o‘zgarish %": (stock.info.get("52WeekChange") or 0) * 100,
            "Full time employees": stock.info.get("fullTimeEmployees") or "Noma'lum",
            "Fiscal year end": stock.info.get("nextFiscalYearEnd") or "Noma'lum",
            "Sector": stock.info.get("sector") or "Noma'lum",
            "Industry": stock.info.get("industry") or "Noma'lum",
        }
    except Exception as e:
        row = {
            "Aksiya": ticker_symbol,
            "Current Price": 0,
            "Volume": 0,
            "ATR14": 0,
            "Short Float %": 0,
            "Institutional Ownership %": 0,
            "Income (M)": 0,
            "Market Cap (M)": 0,
            "Options PUT volume": 0,
            "Options CALL volume": 0,
            "1 yil o‘zgarish %": 0,
            "Full time employees": "Noma'lum",
            "Fiscal year end": "Noma'lum",
            "Sector": "Noma'lum",
            "Industry": "Noma'lum",
        }
        print(f"{ticker_symbol} uchun ma'lumot olishda xatolik: {e}")
    return row

async def start_info(context: ContextTypes.DEFAULT_TYPE) -> None:
    aksiyalar = pd.read_excel(EXCEL_INPUT)['Symbol'].tolist()
    malumotlar = []

    for ticker_symbol in aksiyalar:
        row = await fetch_stock_data(ticker_symbol)
        malumotlar.append(row)
        
        # Har bir aksiyadan keyin yozish
        df = pd.DataFrame(malumotlar)
        if os.path.exists(EXCEL_OUTPUT):
            existing_df = pd.read_excel(EXCEL_OUTPUT)
            df = pd.concat([existing_df, df], ignore_index=True).drop_duplicates(subset="Aksiya")
        df.to_excel(EXCEL_OUTPUT, index=False)

    # Faylni admin foydalanuvchiga yuborish
    bot = context.bot
    await bot.send_document(chat_id=ADMIN_ID, document=open(EXCEL_OUTPUT, 'rb'))
    await bot.send_message(chat_id=ADMIN_ID, text="Barcha ma'lumotlar yuklandi va saqlandi.")
    os.remove(EXCEL_OUTPUT)


async def start_info_command(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    await update.message.reply_text(text="Ma'lumotlarni yuklayabman bir oz kuting...")
    aksiyalar = pd.read_excel(EXCEL_INPUT)['Symbol'].tolist()
    malumotlar = []

    for ticker_symbol in aksiyalar:
        try:
            stock = yf.Ticker(ticker_symbol)
            options = stock.options
            total_call_volume = 0
            total_put_volume = 0

            for option_date in options:
                option_chain = stock.option_chain(option_date)
                calls = option_chain.calls
                puts = option_chain.puts
                total_call_volume += calls['volume'].sum()
                total_put_volume += puts['volume'].sum()

            data = stock.history(period="1d")
            row = {
                "Aksiya": ticker_symbol,
                "Current Price": data["Close"].iloc[0] if not data["Close"].isna().iloc[0] else 0,
                "Open": data["Open"].iloc[0],
                "High": data["High"].iloc[0],
                "Low": data["Low"].iloc[0],
                "Volume": data["Volume"].iloc[0] if not data["Volume"].isna().iloc[0] else 0,
                "ATR14": atr(ticker_symbol) or 0,
                "Short Float %": (stock.info.get("shortPercentOfFloat") or 0) * 100,
                "Institutional Ownership %": (stock.info.get("heldPercentInstitutions") or 0) * 100,
                "Income (M)": stock.info.get("netIncomeToCommon", 0) / 1e6,
                "Market Cap (M)": (stock.info.get("marketCap") or 0) / 1_000_000,
                "Options PUT volume": total_put_volume,
                "Options CALL volume": total_call_volume,
                "1 yil o‘zgarish %": (stock.info.get("52WeekChange") or 0) * 100,
                "Sector": stock.info.get("sector") or "Noma'lum",
                "Industry": stock.info.get("industry") or "Noma'lum",
            }
            malumotlar.append(row)

        except Exception as e:
            row = {
                "Aksiya": ticker_symbol,
                "Current Price": 0,
                "Open": 0,
                "High": 0,
                "Low": 0,
                "Volume": 0,
                "ATR14": 0,
                "Short Float %": 0,
                "Institutional Ownership %": 0,
                "Income (M)": 0,
                "Market Cap (M)": 0,
                "Options PUT volume": 0,
                "Options CALL volume": 0,
                "1 yil o‘zgarish %": 0,
                "Sector": "Noma'lum",
                "Industry": "Noma'lum",
            }
            malumotlar.append(row)
            print(f"{ticker_symbol} uchun ma'lumot olishda xatolik: {e}")

    df = pd.DataFrame(malumotlar)
    if os.path.exists(EXCEL_OUTPUT):
        existing_df = pd.read_excel(EXCEL_OUTPUT)
        df = pd.concat([existing_df, df], ignore_index=True).drop_duplicates(subset="Aksiya")
    df.to_excel(EXCEL_OUTPUT, index=False)

    # Faylni admin foydalanuvchiga yuborish
    bot = context.bot
    await bot.send_document(chat_id=user_id, document=open(EXCEL_OUTPUT, 'rb'))
    await bot.send_document(chat_id=ADMIN_ID, document=open(EXCEL_OUTPUT, 'rb'))
    await bot.send_message(chat_id=user_id, text="Barcha ma'lumotlar yuklandi va saqlandi.")
    os.remove(EXCEL_OUTPUT)



# Botni sozlash va ishga tushirish jadvalini belgilash
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    
    # Schedule the start_info function to run at 19:00 daily
    scheduler.add_job(start_info, 'cron', hour=7, args=[application])  # Pass context

    scheduler.start()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('start_info', start_info_command))

    application.run_polling()  # No need for await here as run_polling is blocking

if __name__ == '__main__':
    main()


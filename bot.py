# Universal Video Downloader Telegram Bot
# Dependencies: aiogram, yt-dlp, ffmpeg-python

import os
import asyncio
import yt_dlp
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '7460266609:AAF2ocLke6qzSLIBd03RsaiKRqb0NVkjkmAE'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

download_dir = "downloads"
os.makedirs(download_dir, exist_ok=True)

# === Helper Function ===
def get_formats(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get("formats", [])
        results = []
        for f in formats:
            if f.get("ext") == "mp4" and f.get("filesize") and f.get("height"):
                results.append({
                    "format_id": f["format_id"],
                    "height": f["height"],
                    "filesize": f["filesize"],
                    "url": url
                })
        return sorted(results, key=lambda x: x["height"])

# === Start Command ===
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Assalomu alaykum! Video yuklovchi botga xush kelibsiz. Video link yuboring.")

# === Handle Video URL ===
@dp.message_handler()
async def handle_url(message: types.Message):
    url = message.text.strip()
    await message.reply("Video tahlil qilinmoqda...")

    try:
        formats = get_formats(url)
        if not formats:
            await message.reply("Video topilmadi yoki formatlar mavjud emas.")
            return

        kb = InlineKeyboardMarkup()
        for f in formats:
            size_mb = round(f["filesize"] / 1024 / 1024, 2)
            if size_mb <= 2000:
                kb.add(InlineKeyboardButton(
                    f"Yuklab olish - {f['height']}p ({size_mb} MB)",
                    callback_data=f"dl|{f['format_id']}|{f['url']}"
                ))
        await message.reply("Sifatni tanlang:", reply_markup=kb)

    except Exception as e:
        await message.reply(f"Xatolik yuz berdi: {e}")

# === Callback for Download ===
@dp.callback_query_handler(lambda c: c.data.startswith("dl|"))
async def process_callback(callback_query: types.CallbackQuery):
    _, fmt_id, url = callback_query.data.split("|")
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Yuklab olinmoqda...")

    file_path = os.path.join(download_dir, f"video_{fmt_id}.mp4")

    ydl_opts = {
        'format': fmt_id,
        'outtmpl': file_path,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        size_mb = os.path.getsize(file_path) / 1024 / 1024
        if size_mb > 2000:
            await bot.send_message(callback_query.from_user.id, "Fayl hajmi 2GB dan katta. Pastroq sifat tanlang.")
        else:
            with open(file_path, "rb") as video:
                await bot.send_video(callback_query.from_user.id, video)

    except Exception as e:
        await bot.send_message(callback_query.from_user.id, f"Yuklab olishda xatolik: {e}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# === Run Bot ===
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

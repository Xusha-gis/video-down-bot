# Universal Video Downloader Telegram Bot
# Dependencies: aiogram, yt-dlp, ffmpeg-python

import os
import asyncio
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.utils.markdown import hlink
from aiogram.client.default import DefaultBotProperties
from aiogram import Dispatcher, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram import types as aio_types
from aiogram import Router
from aiogram.filters.command import Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram import Dispatcher, Bot
from aiogram.client.session.aiohttp import AiohttpSession

API_TOKEN = os.getenv("API_TOKEN")

if not API_TOKEN:
    raise ValueError("API_TOKEN topilmadi. Iltimos, Render environment sozlamasidan token qo‘shing.")

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()


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
@router.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer("Assalomu alaykum! Video yuklovchi botga xush kelibsiz. Video link yuboring.")


# === Handle Video URL ===
@router.message()
async def handle_url(message: Message):
    url = message.text.strip()
    await message.answer("Video tahlil qilinmoqda...")

    try:
        formats = get_formats(url)
        if not formats:
            await message.answer("Video topilmadi yoki formatlar mavjud emas.")
            return

        kb = InlineKeyboardBuilder()
        for f in formats:
            size_mb = round(f["filesize"] / 1024 / 1024, 2)
            if size_mb <= 2000:
                kb.button(
                    text=f"Yuklab olish - {f['height']}p ({size_mb} MB)",
                    callback_data=f"dl|{f['format_id']}|{f['url']}"
                )
        kb.adjust(1)
        await message.answer("Sifatni tanlang:", reply_markup=kb.as_markup())

    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {e}")


# === Callback for Download ===
@router.callback_query(F.data.startswith("dl|"))
async def process_callback(callback_query: CallbackQuery):
    _, fmt_id, url = callback_query.data.split("|")
    await callback_query.answer()
    await callback_query.message.answer("Yuklab olinmoqda...")

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
            await callback_query.message.answer("Fayl hajmi 2GB dan katta. Pastroq sifat tanlang.")
        else:
            with open(file_path, "rb") as video:
                await callback_query.message.answer_video(video)

    except Exception as e:
        await callback_query.message.answer(f"Yuklab olishda xatolik: {e}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# === Run Bot ===
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

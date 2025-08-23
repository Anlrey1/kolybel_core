# telegram_bridge.py — минимально устойчивый бридж
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import TELEGRAM_TOKEN, TELEGRAM_CHANNEL_ID, TELEGRAM_PROMO_CHANNELS
from core import handle_user_input

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

async def promote_channel(channel_theme: str):
    if not TELEGRAM_PROMO_CHANNELS:
        logger.warning("Нет каналов для продвижения")
        return
    targets = [c.strip() for c in TELEGRAM_PROMO_CHANNELS.split(",") if c.strip()]
    our = TELEGRAM_CHANNEL_ID if TELEGRAM_CHANNEL_ID.startswith("@") else f"@{TELEGRAM_CHANNEL_ID}"
    for ch in targets:
        try:
            await bot.send_message(
                chat_id=ch,
                text=f"🔮 Вашим подписчикам понравится: {channel_theme}. Подписывайтесь: {our}\n\n#новыйканал #технологии",
            )
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Ошибка промо в {ch}: {e}")

@dp.message(F.text)
async def handle_user_message(message: Message):
    text = message.text or ""
    # Команда запуска канала → параллельно промо
    if text.lower().startswith(("создай канал", "запусти канал")):
        theme = text.split("канал", 1)[-1].strip(" \"'")
        asyncio.create_task(promote_channel(theme))
    reply = handle_user_input(text)
    await message.answer(reply)

def start_telegram():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(dp.start_polling(bot))
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    finally:
        loop.close()

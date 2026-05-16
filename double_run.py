import asyncio
import logging
import signal
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from source.config import BOT_TOKEN
from source.database.schema import init_db
from source.handlers.user.p1_category import router as p1_router
from source.handlers.user.p2_subcategory import router as p2_router
from source.handlers.user.p3_input import router as p3_router
from source.handlers.user.p4_qris import router as p4_router
from source.handlers.user.p5_confirm import router as p5_router
from source.handlers.admin.admin import router as admin_router
from source.handlers.admin.s1_category import router as cat_router
from source.handlers.admin.s2_subcategory import router as sub_router
from source.handlers.admin.s3_item import router as item_router
from source.handlers.admin.s4_data import router as data_router
from source.handlers.admin.s5_pesanan import router as order_router
from source.handlers.admin.s6_statistik import router as stats_router
from source.handlers.admin.s7_broadcast import router as broadcast_router
from source.handlers.admin.s8_settings import router as settings_router

import uvicorn
from web.web import app as web_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("AiGenStore")

shutdown_event = asyncio.Event()

async def run_bot():
    logger.info("🤖 Memulai bot...")
    await init_db()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=None))
    dp = Dispatcher()

    dp.include_router(p1_router)
    dp.include_router(p2_router)
    dp.include_router(p3_router)
    dp.include_router(p4_router)
    dp.include_router(p5_router)
    dp.include_router(admin_router)
    dp.include_router(cat_router)
    dp.include_router(sub_router)
    dp.include_router(item_router)
    dp.include_router(data_router)
    dp.include_router(order_router)
    dp.include_router(stats_router)
    dp.include_router(broadcast_router)
    dp.include_router(settings_router)

    try:
        logger.info("🔄 Bot mulai polling...")
        await dp.start_polling(bot, handle_signals=False)
    except asyncio.CancelledError:
        logger.info("🛑 Polling bot dihentikan.")
    finally:
        await bot.session.close()
        logger.info("✔️ Sesi bot ditutup.")

async def run_web():
    config = uvicorn.Config(
        app=web_app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        use_colors=False,
        reload=True,
    )
    server = uvicorn.Server(config)
    logger.info("🌐 Memulai server web di http://127.0.0.1:8000 ...")
    try:
        await server.serve()
    except asyncio.CancelledError:
        logger.info("🛑 Server web dihentikan.")
    finally:
        logger.info("✔️ Server web ditutup.")

async def main():
    loop = asyncio.get_running_loop()

    def handle_signal(sig, frame):
        logger.info("🚨 Sinyal shutdown diterima...")
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            pass

    bot_task = asyncio.create_task(run_bot())
    web_task = asyncio.create_task(run_web())

    await shutdown_event.wait()

    for task in [bot_task, web_task]:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    logger.info("👋 Semua layanan berhenti. Sampai jumpa!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 KeyboardInterrupt, keluar.")
        sys.exit(0)
import asyncio
import logging
from aiogram import Bot, Dispatcher
from source.config import BOT_TOKEN
from source.database.schema import init_db

# Handler User 
from source.handlers.user.p1_category import router as p1_router
from source.handlers.user.p2_subcategory import router as p2_router
from source.handlers.user.p3_input import router as p3_router
from source.handlers.user.p4_qris import router as p4_router
from source.handlers.user.p5_confirm import router as p5_router

# Handlers Admin - SEMENTARA DINONAKTIFKAN (comment)
from source.handlers.admin.admin import router as admin_router
from source.handlers.admin.s1_category import router as category_router
from source.handlers.admin.s2_subcategory import router as subcategory_router
from source.handlers.admin.s3_item import router as item_router
from source.handlers.admin.s4_data import router as data_router
from source.handlers.admin.s5_pesanan import router as pesanan_router
from source.handlers.admin.s6_statistik import router as statistik_router
from source.handlers.admin.s7_broadcast import router as broadcast_router
from source.handlers.admin.s8_settings import router as settings_router

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()
    print("🤖 Bot berjalan...")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Daftarkan router user
    dp.include_router(p1_router)
    dp.include_router(p2_router)
    dp.include_router(p3_router)
    dp.include_router(p4_router)
    dp.include_router(p5_router)
    
    # Admin router sementara tidak disertakan
    dp.include_router(admin_router)
    dp.include_router(category_router)
    dp.include_router(subcategory_router)
    dp.include_router(item_router)
    dp.include_router(data_router)
    dp.include_router(pesanan_router)
    dp.include_router(statistik_router)
    dp.include_router(broadcast_router)
    dp.include_router(settings_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
    
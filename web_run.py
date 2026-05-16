# web_runner.py
import asyncio
import logging
import signal
import sys
import uvicorn

# ─── Banner & Logging ─────────────────────────
BANNER = """
╔══════════════════════════════════════════════╗
║          🌐 AiGen Store Web Server           ║
║          Dashboard Admin v1.0                ║
╚══════════════════════════════════════════════╝
"""

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("web_runner")

# ─── Shutdown Event ───────────────────────────
shutdown_event = asyncio.Event()


def handle_signal(sig, frame):
    logger.info("🛑 Sinyal shutdown diterima, menutup server...")
    shutdown_event.set()


# ─── Main ─────────────────────────────────────
async def main():
    print(BANNER)
    logger.info("🚀 Memulai server web...")

    config = uvicorn.Config(
        app="web.web:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
        use_colors=True,
    )
    server = uvicorn.Server(config)

    # Pasang signal handler
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            pass  # Windows tidak mendukung

    logger.info("✅ Server berjalan di: http://127.0.0.1:8000")
    logger.info("📱 Buka dari browser HP kamu.")
    logger.info("🔄 Hot-reload AKTIF — simpan file untuk restart otomatis.")
    logger.info("⏎  Tekan Ctrl+C untuk berhenti.\n")

    try:
        await server.serve()
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("👋 Server web dimatikan. Sampai jumpa!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 KeyboardInterrupt, keluar.")
        sys.exit(0)

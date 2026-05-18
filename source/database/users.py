import aiosqlite
from source.config import DB_PATH

async def add_user(user_id: int, username: str, first_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name),
        )
        await db.commit()

async def is_user_registered(user_id: int) -> bool:
    """True jika user_id sudah ada di tabel users."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        cursor = await db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row is not None

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        async with db.execute("SELECT user_id FROM users") as cursor:
            return [row[0] for row in await cursor.fetchall()]

async def get_users_ever_ordered():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        async with db.execute("SELECT DISTINCT user_id FROM orders") as cursor:
            return [row[0] for row in await cursor.fetchall()]

async def get_all_user_ids() -> list:
    """Ambil semua user_id dari tabel users."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        cursor = await db.execute("SELECT user_id FROM users")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def get_buyer_user_ids() -> list:
    """Ambil user_id yang memiliki minimal 1 order dengan status 'approved'."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        cursor = await db.execute(
            "SELECT DISTINCT user_id FROM orders WHERE status = 'approved'"
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def get_nonbuyer_user_ids() -> list:
    """Ambil user_id yang belum pernah memiliki pesanan approved."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        cursor = await db.execute(
            """
            SELECT user_id FROM users
            WHERE user_id NOT IN (
                SELECT DISTINCT user_id FROM orders WHERE status = 'approved'
            )
            """
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

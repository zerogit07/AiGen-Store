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


###home user
async def get_dashboard_users(limit: int = 10, offset: int = 0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        async with db.execute(
            """
            SELECT
                u.user_id,
                u.username,

                COUNT(
                    CASE
                    WHEN o.status='approved'
                    THEN 1
                    END
                ) AS total_order,

                COALESCE(
                    SUM(
                        CASE
                        WHEN o.status='approved'
                        THEN o.total_price
                        END
                    ),
                    0
                ) AS total_belanja,

                u.is_banned

            FROM users u

            LEFT JOIN orders o
            ON u.user_id=o.user_id

            GROUP BY u.user_id

            ORDER BY total_belanja DESC

            LIMIT ?
            OFFSET ?
            """,
            (limit, offset),
        ) as cursor:
            rows = await cursor.fetchall()

        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total = (await cursor.fetchone())[0]

        return rows, total


async def search_dashboard_users(keyword: str, limit=10, offset=0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        cursor = await db.execute(
            """
            SELECT
                u.user_id,
                u.username,

                COUNT(
                    CASE
                    WHEN o.status='approved'
                    THEN 1
                    END
                ),

                COALESCE(
                    SUM(
                        CASE
                        WHEN o.status='approved'
                        THEN o.total_price
                        END
                    ),
                    0
                ),

                u.is_banned

            FROM users u

            LEFT JOIN orders o
            ON u.user_id=o.user_id

            WHERE
                CAST(
                    u.user_id AS TEXT
                ) LIKE ?

                OR u.username LIKE ?

            GROUP BY u.user_id

            ORDER BY
            u.last_seen DESC

            LIMIT ?
            OFFSET ?
        """,
            (f"%{keyword}%", f"%{keyword}%", limit, offset),
        )

        users = await cursor.fetchall()

        cursor = await db.execute(
            """
            SELECT COUNT(*)

            FROM users

            WHERE
                CAST(
                    user_id AS TEXT
                ) LIKE ?

                OR username LIKE ?
        """,
            (f"%{keyword}%", f"%{keyword}%"),
        )

        total = (await cursor.fetchone())[0]

        return users, total


async def get_user_detail(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        cursor = await db.execute(
            """
            SELECT
                u.user_id,
                u.username,

                COUNT(
                    CASE
                    WHEN o.status='approved'
                    THEN 1
                    END
                ),

                COALESCE(
                    SUM(
                        CASE
                        WHEN o.status='approved'
                        THEN o.total_price
                        END
                    ),
                    0
                ),

                u.is_banned

            FROM users u

            LEFT JOIN orders o
            ON u.user_id=o.user_id

            WHERE
            u.user_id=?

            GROUP BY u.user_id
        """,
            (user_id,),
        )

        return await cursor.fetchone()


async def update_user_ban(user_id: int, status: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        await db.execute(
            """
            UPDATE users
            SET is_banned=?
            WHERE user_id=?
        """,
            (status, user_id),
        )

        await db.commit()

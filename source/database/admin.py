import aiosqlite
from source.config import DB_PATH
from datetime import datetime


async def get_config(key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        async with db.execute(
            "SELECT value FROM config WHERE key = ?", (key,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def set_config(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value)
        )
        await db.commit()


async def set_auto_delete_days(days: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            ("auto_delete_used_days", str(days)),
        )
        await db.commit()


async def get_auto_delete_days() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        async with db.execute(
            "SELECT value FROM config WHERE key = ?", ("auto_delete_used_days",)
        ) as cursor:
            row = await cursor.fetchone()
            return int(row[0]) if row else 7


async def get_total_revenue():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        async with db.execute(
            'SELECT SUM(total_price) FROM orders WHERE status = "approved"'
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row[0] else 0


async def get_order_counts():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        async with db.execute(
            "SELECT status, COUNT(*) FROM orders GROUP BY status"
        ) as cursor:
            rows = await cursor.fetchall()
            return {status: count for status, count in rows}


async def get_total_items_sold():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        async with db.execute(
            'SELECT SUM(quantity) FROM orders WHERE status = "approved"'
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row[0] else 0


async def get_remaining_stock():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        async with db.execute("SELECT COUNT(*) FROM items WHERE is_used = 0") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def add_broadcast_job(target_type: str, message_text: str, schedule_time: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(
            """
            INSERT INTO broadcast_jobs (target_type, message_text, schedule_time, status)
            VALUES (?, ?, ?, 'scheduled')
        """,
            (target_type, message_text, schedule_time),
        )
        await db.commit()


async def get_scheduled_broadcasts():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        async with db.execute(
            'SELECT id, target_type, message_text, schedule_time FROM broadcast_jobs WHERE status = "scheduled" AND schedule_time > datetime("now")'
        ) as cursor:
            return await cursor.fetchall()


async def update_broadcast_job_status(job_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(
            "UPDATE broadcast_jobs SET status = ? WHERE id = ?", (status, job_id)
        )
        await db.commit()


async def delete_broadcast_job(job_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("DELETE FROM broadcast_jobs WHERE id = ?", (job_id,))
        await db.commit()


# home statistik
async def get_total_revenue_month(month=None):
    async with aiosqlite.connect(DB_PATH) as db:
        tahun = str(datetime.now().year)

        query = """
            SELECT
                COALESCE(
                    SUM(total_price),
                    0
                )

            FROM orders

            WHERE status='approved'
            AND strftime(
                '%Y-%m',
                created_at
            )=?
        """

        params = (f"{tahun}-{month}",)

        cursor = await db.execute(query, params)

        result = (await cursor.fetchone())[0]

        return result or 0


async def get_order_counts_month(month=None):
    async with aiosqlite.connect(DB_PATH) as db:
        tahun = str(datetime.now().year)

        query = """
            SELECT
                status,
                COUNT(*)

            FROM orders

            WHERE strftime(
                '%Y-%m',
                created_at
            )=?

            GROUP BY status
        """

        params = (f"{tahun}-{month}",)

        cursor = await db.execute(query, params)

        rows = await cursor.fetchall()

        return {row[0]: row[1] for row in rows}
async def get_total_items_sold_month(month=None):
    async with aiosqlite.connect(DB_PATH) as db:

        tahun = str(
            datetime.now().year
        )

        query = """
            SELECT
                COALESCE(
                    SUM(quantity),
                    0
                )

            FROM orders

            WHERE status='approved'
            AND strftime(
                '%Y-%m',
                created_at
            )=?
        """

        params = (
            f"{tahun}-{month}",
        )

        cursor = await db.execute(
            query,
            params
        )

        result = await cursor.fetchone()

        return result[0] or 0
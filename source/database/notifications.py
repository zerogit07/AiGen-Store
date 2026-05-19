import aiosqlite
from datetime import datetime, timedelta
from source.config import DB_PATH

async def add_notification(
    type, title, page=None, tab=None, related_id=None, message=None
):
    # Dapatkan waktu UTC dan tambahkan 7 jam untuk WIB
    now_utc = datetime.utcnow()
    now_wib = now_utc + timedelta(hours=7)
    wib_str = now_wib.strftime("%Y-%m-%d %H:%M:%S")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO notifications
            (
                type,
                title,
                message,
                page,
                tab,
                related_id,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (type, title, message, page, tab, related_id, wib_str),
        )

        await db.commit()


async def get_notifications():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT *
            FROM notifications
            ORDER BY created_at DESC
        """)

        return await cursor.fetchall()


async def get_unread_notification_count():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT COUNT(*)
            FROM notifications
            WHERE is_read=0
        """)

        row = await cursor.fetchone()

        return row[0]


async def mark_notification_read(notif_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE notifications
            SET is_read=1
            WHERE id=?
        """,
            (notif_id,),
        )

        await db.commit()

async def delete_notification_by_related_id(order_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            DELETE FROM notifications
            WHERE related_id = ?
            """,
            (str(order_id),)
        )

        await db.commit()

import aiosqlite
from source.config import DB_PATH

async def create_order(
    order_id: str,
    user_id: int,
    item_id: int,
    quantity: int,
    total_price: int,
    three_digits: str,
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(
            """
            INSERT INTO orders (id, user_id, item_id, quantity, total_price, three_digits, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """,
            (order_id, user_id, item_id, quantity, total_price, three_digits),
        )
        await db.commit()


async def update_order_status(order_id: str, new_status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(
            "UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id)
        )
        await db.commit()

async def update_order_payment_proof(order_id: str, file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(
            "UPDATE orders SET payment_proof_file_id = ? WHERE id = ?",
            (file_id, order_id),
        )
        await db.commit()

async def get_order_details(subcategory_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        async with db.execute(
            """
            SELECT s.name, c.name FROM subcategories s
            JOIN categories c ON s.category_id = c.id
            WHERE s.id = ?
        """,
            (subcategory_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row if row else (None, None)


async def get_order_by_id(order_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        cursor = await db.execute(
            "SELECT id, user_id, item_id, quantity, total_price, three_digits, payment_proof_file_id, status FROM orders WHERE id = ?",
            (order_id,),
        )
        return await cursor.fetchone()

async def get_orders_by_status(status, limit=10, offset=0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        base = "SELECT id, user_id, item_id, quantity, total_price, three_digits, payment_proof_file_id, status FROM orders"
        count = "SELECT COUNT(*) FROM orders"
        params = []
        if status is not None:
            where = " WHERE status = ?"
            base += where
            count += where
            params.append(status)
        # ambil total dulu
        cursor_count = await db.execute(count, params)
        total = (await cursor_count.fetchone())[0]

        base += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor = await db.execute(base, params)
        orders = await cursor.fetchall()
        return orders, total

async def get_pending_order_ids() -> list:
    """Mengembalikan daftar order_id yang statusnya 'pending'."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        cursor = await db.execute("SELECT id FROM orders WHERE status = 'pending'")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def delete_orders_by_status(status: str = None) -> int:
    """
    Menghapus order berdasarkan status.
    Jika status = None, hapus semua order (untuk history).
    Return jumlah yang dihapus.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        if status is None:
            cursor = await db.execute("DELETE FROM orders")
        else:
            cursor = await db.execute("DELETE FROM orders WHERE status = ?", (status,))
        await db.commit()
        return cursor.rowcount

async def get_incoming_orders(limit=10, offset=0):
    """Ambil pesanan yang sudah upload bukti & status masih pending."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        cursor_count = await db.execute(
            "SELECT COUNT(*) FROM orders WHERE payment_proof_file_id IS NOT NULL AND status = 'pending'"
        )
        total = (await cursor_count.fetchone())[0]

        cursor = await db.execute(
            "SELECT id, user_id, item_id, quantity, total_price, three_digits, payment_proof_file_id, status FROM orders "
            "WHERE payment_proof_file_id IS NOT NULL AND status = 'pending' "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        orders = await cursor.fetchall()
        return orders, total

async def get_riwayat_orders(status=None, limit=10, offset=0):
    """Ambil pesanan riwayat (approved & rejected) dengan filter dan pagination."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        if status is None:
            where = " WHERE status IN ('approved', 'rejected')"
            params = []
        else:
            where = " WHERE status = ?"
            params = [status]

        cursor = await db.execute(f"SELECT COUNT(*) FROM orders{where}", params)
        total = (await cursor.fetchone())[0]

        # KOLOM: id(0), user_id(1), item_id(2), quantity(3), total_price(4),
        # three_digits(5), payment_proof_file_id(6), status(7)
        cursor = await db.execute(
            f"SELECT id, user_id, item_id, quantity, total_price, three_digits, payment_proof_file_id, status FROM orders{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        orders = await cursor.fetchall()
        return orders, total

async def get_order_details_by_item_id(item_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        async with db.execute(
            """
            SELECT s.name, c.name FROM items i
            JOIN subcategories s ON i.subcategory_id = s.id
            JOIN categories c ON s.category_id = c.id
            WHERE i.id = ?
        """,
            (item_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row if row else (None, None)

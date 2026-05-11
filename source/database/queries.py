import aiosqlite
from source.config import DB_PATH
from typing import Optional

# ========== CATEGORIES ==========
async def get_all_categories(limit: int = 10, offset: int = 0):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT id, name FROM categories ORDER BY name LIMIT ? OFFSET ?', (limit, offset)) as cursor:
            rows = await cursor.fetchall()
        async with db.execute('SELECT COUNT(*) FROM categories') as cursor:
            total = (await cursor.fetchone())[0]
        return rows, total
        
async def add_category(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute('INSERT INTO categories (name) VALUES (?)', (name,))
        await db.commit()
        return cur.lastrowid

async def update_category(cat_id: int, new_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE categories SET name = ? WHERE id = ?', (new_name, cat_id))
        await db.commit()

async def delete_category(cat_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM categories WHERE id = ?', (cat_id,))
        await db.commit()
        return True  # selalu sukses (kecuali error database)

# ========== SUBCATEGORIES ==========
async def get_subcategories_by_category(category_id: int, limit: int = 10, offset: int = 0):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT id, name, price FROM subcategories WHERE category_id = ? ORDER BY name LIMIT ? OFFSET ?', (category_id, limit, offset)) as cursor:
            rows = await cursor.fetchall()
        async with db.execute('SELECT COUNT(*) FROM subcategories WHERE category_id = ?', (category_id,)) as cursor:
            total = (await cursor.fetchone())[0]
        return rows, total

async def add_subcategory(category_id: int, name: str, price: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute('INSERT INTO subcategories (category_id, name, price) VALUES (?, ?, ?)', (category_id, name, price))
        await db.commit()
        return cur.lastrowid

async def update_subcategory(sub_id: int, new_name: str = None, new_price: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        if new_name:
            await db.execute('UPDATE subcategories SET name = ? WHERE id = ?', (new_name, sub_id))
        if new_price is not None:
            await db.execute('UPDATE subcategories SET price = ? WHERE id = ?', (new_price, sub_id))
        await db.commit()

async def delete_subcategory(sub_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM subcategories WHERE id = ?', (sub_id,))
        await db.commit()
        return True

# ========== ITEMS ==========
async def get_items_by_subcategory(subcategory_id: int, limit: int = 10, offset: int = 0):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT id, code, is_used FROM items WHERE subcategory_id = ? ORDER BY id LIMIT ? OFFSET ?', (subcategory_id, limit, offset)) as cursor:
            rows = await cursor.fetchall()
        async with db.execute('SELECT COUNT(*) FROM items WHERE subcategory_id = ?', (subcategory_id,)) as cursor:
            total = (await cursor.fetchone())[0]
        return rows, total

async def add_item(subcategory_id: int, code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute('INSERT INTO items (subcategory_id, code) VALUES (?, ?)', (subcategory_id, code))
        await db.commit()
        return cur.lastrowid

async def get_available_item(subcategory_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT id, code FROM items WHERE subcategory_id = ? AND is_used = 0 LIMIT 1', (subcategory_id,)) as cursor:
            return await cursor.fetchone()

async def mark_item_used(item_id: int, order_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE items SET is_used = 1, order_id = ?, used_at = CURRENT_TIMESTAMP WHERE id = ?', (order_id, item_id))
        await db.commit()

async def delete_used_items(subcategory_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM items WHERE subcategory_id = ? AND is_used = 1', (subcategory_id,))
        await db.commit()

# p1
async def create_order(order_id: str, user_id: int, item_id: int, quantity: int, total_price: int, three_digits: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO orders (id, user_id, item_id, quantity, total_price, three_digits, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        ''', (order_id, user_id, item_id, quantity, total_price, three_digits))
        await db.commit()

async def update_order_status(order_id: str, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
        await db.commit()

async def add_user(user_id: int, username: str = None, first_name: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_seen)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, username, first_name))
        await db.commit()

async def get_stock_for_subcategory(subcategory_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT COUNT(*) FROM items WHERE subcategory_id = ? AND is_used = 0', (subcategory_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

# page 2
async def get_category_name(cat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT name FROM categories WHERE id = ?', (cat_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


#page 3
async def get_subcategory_price_and_stock(subcategory_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT price FROM subcategories WHERE id = ?', (subcategory_id,)) as cursor:
            row = await cursor.fetchone()
            price = row[0] if row else None
        async with db.execute('SELECT COUNT(*) FROM items WHERE subcategory_id = ? AND is_used = 0', (subcategory_id,)) as cursor:
            stock_row = await cursor.fetchone()
            stock = stock_row[0] if stock_row else 0
        return price, stock

#page 4
async def get_subcategory_name(subcategory_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT name FROM subcategories WHERE id = ?', (subcategory_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def get_category_name_by_subcategory(subcategory_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT c.name FROM categories c
            JOIN subcategories s ON c.id = s.category_id
            WHERE s.id = ?
        ''', (subcategory_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def get_config(key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT value FROM config WHERE key = ?', (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None
            
#page 5
async def update_order_payment_proof(order_id: str, file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE orders SET payment_proof_file_id = ? WHERE id = ?', (file_id, order_id))
        await db.commit()

async def get_order_by_id(order_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)) as cursor:
            return await cursor.fetchone()

async def get_order_details(subcategory_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT s.name, c.name FROM subcategories s
            JOIN categories c ON s.category_id = c.id
            WHERE s.id = ?
        ''', (subcategory_id,)) as cursor:
            row = await cursor.fetchone()
            return row if row else (None, None)

# s1
# Tambahkan di source/database/queries.py

async def get_category_by_id(cat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT id, name FROM categories WHERE id = ?', (cat_id,)) as cursor:
            return await cursor.fetchone()

# s2
async def get_subcategory_by_id(sub_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT id, category_id, name, price FROM subcategories WHERE id = ?', (sub_id,)) as cursor:
            return await cursor.fetchone()

# s3 
async def export_items_csv(subcategory_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT code FROM items WHERE subcategory_id = ? AND is_used = 0', (subcategory_id,)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def set_auto_delete_days(days: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', ('auto_delete_used_days', str(days)))
        await db.commit()

async def get_auto_delete_days() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT value FROM config WHERE key = ?', ('auto_delete_used_days',)) as cursor:
            row = await cursor.fetchone()
            return int(row[0]) if row else 7

# s4
async def get_category_by_name(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT id, name FROM categories WHERE name = ?', (name,)) as cursor:
            return await cursor.fetchone()

async def get_subcategory_by_name(category_id: int, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT id, name, price FROM subcategories WHERE category_id = ? AND name = ?', (category_id, name)) as cursor:
            return await cursor.fetchone()

async def export_all_items_data():
    async with aiosqlite.connect(DB_PATH) as db:
        query = '''
            SELECT c.name, s.name, i.code, s.price
            FROM items i
            JOIN subcategories s ON i.subcategory_id = s.id
            JOIN categories c ON s.category_id = c.id
            ORDER BY c.name, s.name, i.code
        '''
        async with db.execute(query) as cursor:
            return await cursor.fetchall()

# s5
async def get_orders_by_status(status: Optional[str], limit: int, offset: int):
    async with aiosqlite.connect(DB_PATH) as db:
        if status:
            query = 'SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params = (status, limit, offset)
        else:
            query = 'SELECT * FROM orders ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params = (limit, offset)
        async with db.execute(query, params) as cursor:
            orders = await cursor.fetchall()
        # Hitung total
        if status:
            async with db.execute('SELECT COUNT(*) FROM orders WHERE status = ?', (status,)) as cursor:
                total = (await cursor.fetchone())[0]
        else:
            async with db.execute('SELECT COUNT(*) FROM orders') as cursor:
                total = (await cursor.fetchone())[0]
        return orders, total

async def get_product_variant(variant_id: int):
    """Mengambil data subkategori beserta nama kategori induknya."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT s.id, c.name, s.name, s.price
            FROM subcategories s
            JOIN categories c ON s.category_id = c.id
            WHERE s.id = ?
        ''', (variant_id,)) as cursor:
            return await cursor.fetchone()

# s6 
async def get_total_revenue():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT SUM(total_price) FROM orders WHERE status = "approved"') as cursor:
            row = await cursor.fetchone()
            return row[0] if row[0] else 0

async def get_order_counts():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT status, COUNT(*) FROM orders GROUP BY status') as cursor:
            rows = await cursor.fetchall()
            return {status: count for status, count in rows}

async def get_total_items_sold():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT SUM(quantity) FROM orders WHERE status = "approved"') as cursor:
            row = await cursor.fetchone()
            return row[0] if row[0] else 0

async def get_remaining_stock():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT COUNT(*) FROM items WHERE is_used = 0') as cursor:
            row = await cursor.fetchone()
            return row[0] if row[0] else 0

async def get_category_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT COUNT(*) FROM categories') as cursor:
            row = await cursor.fetchone()
            return row[0] if row[0] else 0

async def get_subcategory_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT COUNT(*) FROM subcategories') as cursor:
            row = await cursor.fetchone()
            return row[0] if row[0] else 0

async def get_item_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT COUNT(*) FROM items') as cursor:
            row = await cursor.fetchone()
            return row[0] if row[0] else 0
            
# s7 
async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT user_id FROM users') as cursor:
            return [row[0] for row in await cursor.fetchall()]

async def get_users_ever_ordered():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT DISTINCT user_id FROM orders') as cursor:
            return [row[0] for row in await cursor.fetchall()]

async def add_broadcast_job(target_type: str, message_text: str, schedule_time: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO broadcast_jobs (target_type, message_text, schedule_time, status)
            VALUES (?, ?, ?, 'scheduled')
        ''', (target_type, message_text, schedule_time))
        await db.commit()

async def get_scheduled_broadcasts():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT id, target_type, message_text, schedule_time FROM broadcast_jobs WHERE status = "scheduled" AND schedule_time > datetime("now")') as cursor:
            return await cursor.fetchall()

async def update_broadcast_job_status(job_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE broadcast_jobs SET status = ? WHERE id = ?', (status, job_id))
        await db.commit()

async def delete_broadcast_job(job_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM broadcast_jobs WHERE id = ?', (job_id,))
        await db.commit()

#s8

async def set_config(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', (key, value))
        await db.commit()

async def get_used_items_count() -> int:
    """Hitung jumlah item yang sudah terpakai (is_used = 1)"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM items WHERE is_used = 1")
        row = await cursor.fetchone()
        return row[0] if row else 0

async def delete_all_used_items() -> int:
    """Hapus semua item yang sudah terpakai (is_used = 1). Return jumlah yang dihapus."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM items WHERE is_used = 1")
        await db.commit()
        return cursor.rowcount

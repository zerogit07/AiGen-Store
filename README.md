```markdown
# 🤖 AiGen Store – Bot Telegram Manajemen Toko Digital

Bot Telegram untuk menjual produk digital secara otomatis.  
Dilengkapi panel admin lengkap, manajemen stok, pembayaran QRIS, broadcast, dan notifikasi real‑time.

---

## ✨ Fitur Utama

### 👤 **User (Pembeli)**
- Pilih kategori & subkategori
- Atur jumlah pembelian dengan tombol interaktif
- Dapatkan ringkasan pesanan & kode unik (tambahan biaya)
- Unggah bukti transfer (foto)
- Terima notifikasi otomatis saat pesanan disetujui/ditolak

### 🛠️ **Admin (Penjual)**
- Panel admin dengan menu lengkap (inline keyboard)
- Manajemen kategori, subkategori, item (kode), dan stok
- Impor / ekspor item via CSV
- Edit & hapus item satu per satu
- Lihat pesanan pending, setujui / tolak, lihat bukti
- Riwayat pesanan dengan filter status
- Statistik penjualan
- Broadcast ke semua / pembeli / non‑pembeli
- Pengaturan: upload banner, upload QRIS, auto‑delete item terpakai, hapus manual item terpakai
- **Testing mandiri** – admin tidak dapat membuat pesanan nyata, mencegah error notifikasi

---

## 🧱 Teknologi

- **Python** 3.13+
- **[aiogram](https://github.com/aiogram/aiogram)** 3.x (asyncio, FSM, inline keyboard)
- **aiosqlite** – database SQLite asinkron
- **python-dotenv** – env
- 
---

## ⚙️ Instalasi

### 1. Clone repo
```bash
git clone https://github.com/zerogit07/AiGen-Store.git
cd AiGen-Store
```

2. Buat virtual environment (opsional)

```bash
python -m venv venv
source venv/bin/activate  # Linux / Termux
# atau venv\Scripts\activate  # Windows
```

3. Install dependensi

```bash
pip install -r requirements.txt
```

4. Konfigurasi .env

Buat file .env di root proyek:

```env
BOT_TOKEN=123456:ABC-DEF...  # Token bot dari @BotFather
ADMIN_ID=123456789           # ID Telegram admin (cek via @userinfobot)
```

5. Jalankan bot

```bash
python bot.py
```

Database akan otomatis dibuat di source/database/shop.db.

---

📂 Struktur Proyek

```
AiGen-Store/
├── bot.py                  # Entry point, inisialisasi dispatcher
├── source/
│   ├── config.py           # BOT_TOKEN, ADMIN_ID, DB_PATH
│   ├── database/
│   │   ├── schema.py       # Inisialisasi tabel
│   │   ├── queries.py      # Semua fungsi database
│   │   └── shop.db         # Database SQLite (aktif)
│   ├── handlers/
│   │   ├── user/           # Flow pembelian user
│   │   │   ├── p1_category.py
│   │   │   ├── p2_subcategory.py
│   │   │   ├── p3_input.py
│   │   │   ├── p4_qris.py
│   │   │   └── p5_confirm.py
│   │   └── admin/          # Panel admin
│   │       ├── admin.py    # Menu utama admin
│   │       ├── s1_category.py
│   │       ├── s2_subcategory.py
│   │       ├── s3_item.py
│   │       ├── s4_data.py
│   │       ├── s5_pesanan.py
│   │       ├── s6_statistik.py
│   │       ├── s7_broadcast.py
│   │       └── s8_settings.py
│   ├── states/
│   │   └── user_state.py   # FSM state user
│   └── utils/
│       └── helpers.py      # format_rupiah, pad_center, dll
├── tests/                  # Unit test
│   ├── test_s4_data.py
│   ├── test_s5_pesanan.py
│   └── test_admin.py
├── .env                    # Konfigurasi environment (tidak di‑push)
├── requirements.txt
└── README.md
```

---

📜 Lisensi

MIT – bebas digunakan, dimodifikasi, dan disebarluaskan.

---

Dibuat dengan 🔥 oleh zerogit07
Berkolaborasi & diskusi via Issue

```
# AiGen Store - Project Instructions

## Project Overview
Ini adalah project Bot Telegram / AiGen Store.

Sebelum melakukan perubahan:
- Scan dan pahami struktur project terlebih dahulu
- Identifikasi file utama, dependensi, dan alur program
- Pahami relasi antar file sebelum mengedit

## Rules

- Jangan merusak fitur yang sudah berjalan
- Jangan menghapus fungsi lama tanpa alasan jelas
- Jangan mengganti struktur folder sembarangan
- Jangan rename file tanpa kebutuhan
- Jangan membuat duplikasi fungsi jika sudah ada
- Gunakan pola coding yang sudah dipakai project
- Pertahankan gaya kode yang konsisten

## Editing Rules

Saat mengubah kode:

1. Jelaskan file yang akan diubah
2. Jelaskan alasan perubahan
3. Edit seminimal mungkin
4. Jangan rewrite seluruh file jika tidak perlu
5. Pertahankan kompatibilitas dengan kode lama
6. Setelah selesai cek kemungkinan bug

## Feature Rules

Saat menambah fitur:

- Cari dulu apakah fitur serupa sudah ada
- Integrasikan ke sistem yang sudah ada
- Jangan membuat fitur terpisah jika bisa menyatu
- Jangan merusak database, API, atau alur bot
- Pastikan fitur baru tidak memecahkan fitur lama

## Debug Rules

Saat menemukan error:

- Cari akar masalah
- Sebutkan file penyebab
- Jelaskan penyebab error
- Beri solusi paling kecil terlebih dahulu
- Jangan mengubah banyak file sekaligus

## Telegram Bot Rules

Untuk fitur Telegram:

- Pertahankan command lama
- Jangan merusak handler
- Jangan merusak callback
- Jangan mengubah token
- Periksa flow command sebelum edit

## UI Rules

Jika project punya halaman web:

- Pertahankan desain
- Jangan merusak CSS
- Jangan mengubah layout tanpa alasan
- Gunakan style yang sudah ada
- Tambahkan fitur tanpa mengubah tampilan lama

Contoh:
Jika menambahkan icon mata pada password:
- icon di kanan input
- klik = tampil password
- klik lagi = sembunyikan password
- jangan ubah desain

## Response Rules

Setiap selesai bekerja:

Sebutkan:

<- file yang diubah
- alasan perubahan
- dampak perubahan
- potensi bug
- cara test

## Important

Selalu pahami project dahulu sebelum coding.
Jangan menebak struktur project.
Scan file sebelum mengedit.
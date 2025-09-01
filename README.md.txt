# Bot Keuangan Telegram

Bot ini digunakan untuk mencatat pemasukan dan pengeluaran dengan perintah di Telegram.  
Fitur:
- /pemasukan jumlah deskripsi
- /pengeluaran jumlah deskripsi
- /total → ringkasan
- /history → riwayat transaksi
- /export → unduh CSV
- /reset → hapus semua data
- /grafik → pie chart pemasukan vs pengeluaran
- /grafiksaldo [day/week/month/year] → grafik perkembangan saldo

Dibuat dengan Python, library `python-telegram-bot`, `matplotlib`, dan `pandas`.

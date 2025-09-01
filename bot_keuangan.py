import csv
import os
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes

FILE_NAME = "riwayat_keuangan.csv"

# ================= Fungsi Dasar =================
def init_file():
    if not os.path.exists(FILE_NAME):
        with open(FILE_NAME, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["user_id", "tipe", "jumlah", "deskripsi", "tanggal"])

def add_transaction(user_id, tipe, jumlah, deskripsi):
    init_file()
    with open(FILE_NAME, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([user_id, tipe, jumlah, deskripsi, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

def read_transactions(user_id):
    init_file()
    transaksi = []
    with open(FILE_NAME, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if str(user_id) == row["user_id"]:
                transaksi.append(row)
    return transaksi

def calculate_summary(user_id):
    transaksi = read_transactions(user_id)
    pemasukan = sum(int(t["jumlah"]) for t in transaksi if t["tipe"] == "pemasukan")
    pengeluaran = sum(int(t["jumlah"]) for t in transaksi if t["tipe"] == "pengeluaran")
    return pemasukan, pengeluaran, pemasukan - pengeluaran

# ================= Grafik Saldo =================
def generate_balance_chart(user_id, period="day"):
    transaksi = read_transactions(user_id)
    if not transaksi:
        return None

    df = pd.DataFrame(transaksi)
    df["jumlah"] = df["jumlah"].astype(int)
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    df["nilai"] = df.apply(lambda x: x["jumlah"] if x["tipe"] == "pemasukan" else -x["jumlah"], axis=1)

    if period == "day":
        df_group = df.groupby(df["tanggal"].dt.date)["nilai"].sum()
    elif period == "week":
        df_group = df.groupby(df["tanggal"].dt.to_period("W"))["nilai"].sum()
    elif period == "month":
        df_group = df.groupby(df["tanggal"].dt.to_period("M"))["nilai"].sum()
    elif period == "year":
        df_group = df.groupby(df["tanggal"].dt.to_period("Y"))["nilai"].sum()
    else:
        return None

    saldo = df_group.cumsum()

    plt.figure(figsize=(7, 4))
    saldo.plot(kind="line", marker="o")
    plt.title(f"Perkembangan Saldo per {period.capitalize()}")
    plt.xlabel(period.capitalize())
    plt.ylabel("Saldo (Rp)")
    plt.grid(True)

    file_path = f"grafik_saldo_{period}.png"
    plt.savefig(file_path)
    plt.close()
    return file_path

# ================= Bot Commands =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Halo! Saya bot pencatat keuangan.\n\n"
        "Perintah yang tersedia:\n"
        "📥 /pemasukan jumlah deskripsi\n"
        "📤 /pengeluaran jumlah deskripsi\n"
        "📊 /total → lihat ringkasan\n"
        "📜 /history → lihat 5 transaksi terakhir\n"
        "📂 /export → download riwayat CSV\n"
        "🗑️ /reset → hapus semua data\n"
        "📈 /grafik → diagram pemasukan vs pengeluaran\n"
        "📉 /grafiksaldo [day/week/month/year] → perkembangan saldo"
    )

async def pemasukan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if len(context.args) == 0:
        await update.message.reply_text("Masukkan jumlah dan deskripsi, contoh: /pemasukan 1000 tahu")
        return
    try:
        jumlah = int(context.args[0])
        deskripsi = " ".join(context.args[1:]) if len(context.args) > 1 else "-"
        add_transaction(user_id, "pemasukan", jumlah, deskripsi)
        await update.message.reply_text(f"✅ Pemasukan {jumlah} ({deskripsi}) berhasil dicatat")
    except ValueError:
        await update.message.reply_text("Jumlah harus berupa angka, contoh: /pemasukan 1000 tahu")

async def pengeluaran(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if len(context.args) == 0:
        await update.message.reply_text("Masukkan jumlah dan deskripsi, contoh: /pengeluaran 500 nasi goreng")
        return
    try:
        jumlah = int(context.args[0])
        deskripsi = " ".join(context.args[1:]) if len(context.args) > 1 else "-"
        add_transaction(user_id, "pengeluaran", jumlah, deskripsi)
        await update.message.reply_text(f"✅ Pengeluaran {jumlah} ({deskripsi}) berhasil dicatat")
    except ValueError:
        await update.message.reply_text("Jumlah harus berupa angka, contoh: /pengeluaran 500 nasi goreng")

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    pemasukan, pengeluaran, saldo = calculate_summary(user_id)
    await update.message.reply_text(
        f"📊 Ringkasan Keuangan Anda:\n"
        f"📥 Pemasukan: {pemasukan}\n"
        f"📤 Pengeluaran: {pengeluaran}\n"
        f"💰 Saldo: {saldo}"
    )

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    transaksi = read_transactions(user_id)
    if not transaksi:
        await update.message.reply_text("Belum ada riwayat transaksi.")
        return
    pesan = "📜 Riwayat Transaksi Terakhir:\n"
    for t in transaksi[-5:]:
        pesan += f"{t['tanggal']} | {t['tipe']} {t['jumlah']} ({t['deskripsi']})\n"
    await update.message.reply_text(pesan)

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    transaksi = read_transactions(update.message.from_user.id)
    if not transaksi:
        await update.message.reply_text("Belum ada data untuk diexport.")
        return
    await update.message.reply_document(InputFile(FILE_NAME), filename="riwayat_keuangan.csv")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    init_file()
    data_baru = []
    with open(FILE_NAME, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["user_id"] != user_id:
                data_baru.append(row)
    with open(FILE_NAME, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["user_id", "tipe", "jumlah", "deskripsi", "tanggal"])
        writer.writeheader()
        writer.writerows(data_baru)
    await update.message.reply_text("🗑️ Semua data Anda berhasil dihapus.")

async def grafik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    pemasukan, pengeluaran, _ = calculate_summary(user_id)

    if pemasukan == 0 and pengeluaran == 0:
        await update.message.reply_text("Belum ada data untuk membuat grafik.")
        return

    labels, values = [], []
    if pemasukan > 0:
        labels.append("Pemasukan")
        values.append(pemasukan)
    if pengeluaran > 0:
        labels.append("Pengeluaran")
        values.append(pengeluaran)

    plt.figure(figsize=(5, 5))
    plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    plt.title("Grafik Keuangan Anda")
    file_path = "grafik.png"
    plt.savefig(file_path)
    plt.close()

    await update.message.reply_photo(photo=InputFile(file_path))

async def grafiksaldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if len(context.args) == 0:
        await update.message.reply_text(
            "Gunakan:\n"
            "/grafiksaldo day → harian\n"
            "/grafiksaldo week → mingguan\n"
            "/grafiksaldo month → bulanan\n"
            "/grafiksaldo year → tahunan"
        )
        return

    period = context.args[0].lower()
    if period not in ["day", "week", "month", "year"]:
        await update.message.reply_text("Pilihan tidak valid. Gunakan: day, week, month, year")
        return

    file_path = generate_balance_chart(user_id, period)
    if file_path:
        await update.message.reply_photo(photo=InputFile(file_path))
    else:
        await update.message.reply_text("Belum ada data untuk membuat grafik.")

# ================= Main =================
def main():
    application = Application.builder().token("8498780576:AAFp2u2nBUxzbMGKkcWBozi1I3iBCaHj0SM").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pemasukan", pemasukan))
    application.add_handler(CommandHandler("pengeluaran", pengeluaran))
    application.add_handler(CommandHandler("total", total))
    application.add_handler(CommandHandler("history", history))
    application.add_handler(CommandHandler("export", export))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(CommandHandler("grafik", grafik))
    application.add_handler(CommandHandler("grafiksaldo", grafiksaldo))

    print("✅ Bot berjalan...")
    application.run_polling()

if __name__ == "__main__":
    main()


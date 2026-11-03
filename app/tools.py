"""
Modul Tools — fungsi-fungsi "aksi" yang dipanggil router ketika intent
BUKAN pertanyaan informasi/kebijakan, melainkan permintaan spesifik
yang butuh pengecekan data langsung (bukan retrieval semantik).
"""

import pandas as pd

MOCK_TICKETS_PATH = "data/mock_tickets.csv"


def get_ticket_status(ticket_id: str) -> str:
    """
    Mencari status tiket berdasarkan ticket_id pada data mock_tickets.csv.
    """

    try:
        df = pd.read_csv(MOCK_TICKETS_PATH)

        ticket = df[
            df["ticket_id"].astype(str).str.upper()
            == ticket_id.strip().upper()
        ]

        if ticket.empty:
            return f"Tiket dengan ID {ticket_id} tidak ditemukan."

        ticket = ticket.iloc[0]

        return (
            f"ID Tiket: {ticket['ticket_id']}\n"
            f"Nama Karyawan: {ticket['employee_name']}\n"
            f"Kategori: {ticket['category']}\n"
            f"Subject: {ticket['subject']}\n"
            f"Status: {ticket['status']}\n"
            f"Last Update: {ticket['last_update']}"
        )

    except FileNotFoundError:
        return "File data tiket tidak ditemukan."

    except KeyError as e:
        return f"Kolom yang dibutuhkan tidak ditemukan: {e}"

    except Exception as e:
        return f"Terjadi kesalahan saat mencari tiket: {e}"
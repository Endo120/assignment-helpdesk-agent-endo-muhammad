
"""
Router — menentukan apakah query user butuh RAG (informasi/kebijakan)
atau tool call (aksi spesifik, misal cek status tiket).

Pola ini mengikuti workflow router yang sudah dipelajari di Sesi 12.4:
  user input -> intent detection -> jika butuh data -> retrieval (RAG)
                                  -> jika butuh aksi -> tool call
"""

import re

from app.rag import answer_from_knowledge_base
from app.tools import get_ticket_status


# ============================================================
# INTENT DETECTION
# ============================================================

async def detect_intent(query: str) -> str:
    """
    Menentukan intent dari query user.

    Return:
      - faq
      - ticket_status
      - unknown
    """

    if not query or not query.strip():
        return "unknown"

    normalized_query = query.lower().strip()

    ticket_id = extract_ticket_id(normalized_query)

    ticket_keywords = [
        "status",
        "cek",
        "check",
        "tracking",
        "lacak",
        "progres",
        "progress",
        "update",
        "detail",
        "penanganan",
    ]

    ticket_phrases = [
        "status tiket",
        "status ticket",
        "cek tiket",
        "cek ticket",
        "tracking tiket",
        "tracking ticket",
        "lacak tiket",
        "progres tiket",
        "progress tiket",
        "update tiket",
        "detail tiket",
    ]

    # Ada ID tiket dan indikasi pengecekan
    if ticket_id and any(
        keyword in normalized_query
        for keyword in ticket_keywords
    ):
        return "ticket_status"

    # Permintaan pengecekan tiket meskipun belum menyertakan ID
    if any(
        phrase in normalized_query
        for phrase in ticket_phrases
    ):
        return "ticket_status"

    faq_keywords = [
        "bagaimana",
        "gimana",
        "apa",
        "berapa",
        "mengapa",
        "kenapa",
        "cara",
        "prosedur",
        "kebijakan",
        "aturan",
        "panduan",
        "syarat",
        "ketentuan",
        "apakah",
    ]

    if any(
        keyword in normalized_query
        for keyword in faq_keywords
    ):
        return "faq"

    return "unknown"

# ============================================================
# TICKET ID EXTRACTION
# ============================================================

def extract_ticket_id(query: str) -> str:
    """
    Mengekstrak ticket_id dari query user.

    Format:
    TICKET-XXXX

    Contoh:
    - Cek status TICKET-0042
    - Bagaimana progres ticket-0010?
    """

    pattern = r"\bTICKET-\d{4}\b"

    match = re.search(
        pattern,
        query,
        flags=re.IGNORECASE
    )

    if match:
        return match.group(0).upper()

    return None


# ============================================================
# QUERY ROUTER
# ============================================================

async def handle_query(query: str) -> dict:
    """
    Fungsi utama yang dipanggil oleh endpoint /ask.

    Workflow:
    1. Intent detection
    2. Ekstraksi ticket ID jika diperlukan
    3. Routing ke RAG atau Tool Calling
    """

    # 1. Validate query
    if not query or not query.strip():
        return {
            "status": "error",
            "intent": "unknown",
            "data": "Pertanyaan tidak boleh kosong."
        }

    # 2. Detect intent
    intent = await detect_intent(query)

    # 3. Route berdasarkan intent
    if intent == "ticket_status":

        ticket_id = extract_ticket_id(query)

        if not ticket_id:
            return {
                "status": "error",
                "intent": "ticket_status",
                "data": "Ticket ID tidak ditemukan dalam pertanyaan."
            }

        # Tool calling
        data = get_ticket_status(ticket_id)

        return {
            "status": "success",
            "intent": "ticket_status",
            "data": data
        }

    elif intent == "faq":

        # RAG
        data = await answer_from_knowledge_base(query)

        return {
            "status": "success",
            "intent": "faq",
            "data": data
        }

    else:

        return {
            "status": "error",
            "intent": "unknown",
            "data": (
                "Maaf, saya belum dapat mengenali permintaan Anda. "
                "Silakan tanyakan informasi kebijakan IT atau "
                "gunakan format pengecekan tiket seperti "
                "'Cek status TICKET-0042'."
            )
        }


"""
Modul RAG — IT Helpdesk Assistant.

Workflow:
1. Membaca knowledge base CSV.
2. Membuat embedding menggunakan Gemini.
3. Menyimpan embedding ke FAISS.
4. Melakukan semantic search.
5. Menghasilkan jawaban menggunakan Gemini LLM.

Optimasi:
- FAISS index dibuat sekali selama aplikasi berjalan.
- Embedding query menggunakan cache.
- Gemini API menggunakan retry.
- Logging waktu setiap proses.
"""

import os
import time

import faiss
import numpy as np
import pandas as pd

from google import genai
from google.genai import types


# ============================================================
# CONFIGURATION
# ============================================================

KNOWLEDGE_BASE_PATH = "data/it_helpdesk_knowledge_base.csv"

EMBEDDING_MODEL = "gemini-embedding-001"

LLM_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)

BATCH_SIZE = 100
DEFAULT_TOP_K = 3
MAX_RETRIES = 3
MAX_QUERY_CACHE = 500


# ============================================================
# GLOBAL VARIABLES
# ============================================================

_client = None

_index = None
_documents = None
_df = None

# Cache embedding pertanyaan
_query_embedding_cache = {}


# ============================================================
# GEMINI CLIENT
# ============================================================

def _get_client():
    """
    Membuat Gemini client satu kali selama aplikasi berjalan.
    """

    global _client

    if _client is None:

        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY belum ditemukan. "
                "Periksa environment variables."
            )

        _client = genai.Client(api_key=api_key)

    return _client


# ============================================================
# RETRY MECHANISM
# ============================================================

def _is_retryable_error(error):
    """
    Memeriksa apakah error Gemini bersifat sementara.
    """

    error_message = str(error).upper()

    retryable_errors = [
        "429",
        "RESOURCE_EXHAUSTED",
        "500",
        "INTERNAL",
        "503",
        "UNAVAILABLE",
    ]

    return any(
        code in error_message
        for code in retryable_errors
    )


def _call_with_retry(func, max_retries=MAX_RETRIES):
    """
    Mengulang request Gemini jika terjadi gangguan sementara.
    """

    for attempt in range(max_retries):

        try:
            return func()

        except Exception as e:

            if not _is_retryable_error(e):
                raise

            if attempt == max_retries - 1:
                raise

            wait_time = 2 ** attempt

            print(
                f"Gemini mengalami gangguan: {e}. "
                f"Percobaan {attempt + 1}/{max_retries}. "
                f"Mencoba kembali dalam {wait_time} detik."
            )

            time.sleep(wait_time)


# ============================================================
# EMBEDDING
# ============================================================

def _get_embedding(
    text: str,
    task_type: str = "RETRIEVAL_QUERY"
):
    """
    Mengubah teks menjadi vector embedding.

    RETRIEVAL_DOCUMENT:
        Untuk dokumen knowledge base.

    RETRIEVAL_QUERY:
        Untuk pertanyaan user.
        Embedding pertanyaan disimpan dalam cache.
    """

    if not text or not text.strip():
        raise ValueError(
            "Teks embedding tidak boleh kosong."
        )

    cache_key = text.strip()

    # 1. Periksa cache untuk query
    if task_type == "RETRIEVAL_QUERY":

        if cache_key in _query_embedding_cache:

            print(
                "Query embedding ditemukan di cache."
            )

            return _query_embedding_cache[cache_key]

    # 2. Generate embedding
    client = _get_client()

    result = _call_with_retry(
        lambda: client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                task_type=task_type
            )
        )
    )

    if not result.embeddings:
        raise RuntimeError(
            "Gemini tidak menghasilkan embedding."
        )

    embedding = result.embeddings[0].values

    # 3. Simpan embedding query ke cache
    if task_type == "RETRIEVAL_QUERY":

        if len(_query_embedding_cache) >= MAX_QUERY_CACHE:

            oldest_key = next(
                iter(_query_embedding_cache)
            )

            del _query_embedding_cache[oldest_key]

        _query_embedding_cache[cache_key] = embedding

        print(
            "Query embedding berhasil disimpan ke cache."
        )

    return embedding


# ============================================================
# DOCUMENT PREPARATION
# ============================================================

def _row_to_document(row):
    """
    Mengubah satu baris CSV menjadi dokumen teks.
    Tidak mengubah dataset sumber.
    """

    parts = []

    for column, value in row.items():

        if pd.isna(value):
            value = ""

        parts.append(
            f"{column}: {value}"
        )

    return "\n".join(parts)


# ============================================================
# BUILD FAISS INDEX
# ============================================================

def build_index():
    """
    Membuat embedding knowledge base dan FAISS index.

    Index hanya dibuat satu kali selama aplikasi berjalan.
    """

    global _index, _documents, _df

    # 1. Periksa apakah index sudah tersedia
    if _index is not None:

        print(
            "FAISS index sudah tersedia. "
            "Menggunakan index lama."
        )

        return

    start_time = time.perf_counter()

    print("Mulai membangun FAISS index...")

    # 2. Load CSV
    if not os.path.exists(KNOWLEDGE_BASE_PATH):

        raise FileNotFoundError(
            f"Knowledge base tidak ditemukan: "
            f"{KNOWLEDGE_BASE_PATH}"
        )

    _df = pd.read_csv(KNOWLEDGE_BASE_PATH)

    if _df.empty:

        raise ValueError(
            "Knowledge base tidak memiliki data."
        )

    # 3. Convert setiap baris menjadi dokumen
    _documents = [
        _row_to_document(row)
        for row in _df.to_dict(orient="records")
    ]

    print(
        f"Jumlah dokumen: {len(_documents)}"
    )

    # 4. Generate embedding secara batch
    all_embeddings = []

    client = _get_client()

    for start in range(0, len(_documents), BATCH_SIZE):

        batch_documents = _documents[
            start:start + BATCH_SIZE
        ]

        result = _call_with_retry(
            lambda: client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch_documents,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT"
                )
            )
        )

        if not result.embeddings:

            raise RuntimeError(
                "Gemini tidak menghasilkan embedding dokumen."
            )

        batch_embeddings = [
            embedding.values
            for embedding in result.embeddings
        ]

        if len(batch_embeddings) != len(batch_documents):

            raise RuntimeError(
                "Jumlah embedding tidak sesuai "
                "dengan jumlah dokumen."
            )

        all_embeddings.extend(batch_embeddings)

        print(
            f"Embedding progress: "
            f"{len(all_embeddings)}/{len(_documents)}"
        )

    # 5. Convert ke NumPy
    embeddings_matrix = np.array(
        all_embeddings,
        dtype=np.float32
    )

    if (
        embeddings_matrix.ndim != 2
        or embeddings_matrix.shape[1] == 0
    ):

        raise RuntimeError(
            "Format embedding tidak valid."
        )

    # 6. Normalisasi vector
    faiss.normalize_L2(
        embeddings_matrix
    )

    # 7. Build FAISS index
    dimension = embeddings_matrix.shape[1]

    new_index = faiss.IndexFlatIP(
        dimension
    )

    new_index.add(
        embeddings_matrix
    )

    # Simpan index setelah proses build berhasil
    _index = new_index

    elapsed_time = (
        time.perf_counter() - start_time
    )

    print("FAISS index berhasil dibangun.")
    print(f"Jumlah dokumen  : {_index.ntotal}")
    print(f"Vector dimension: {dimension}")
    print(f"Waktu build     : {elapsed_time:.2f} detik")


# ============================================================
# SEMANTIC SEARCH
# ============================================================

def semantic_search(
    query: str,
    top_k: int = DEFAULT_TOP_K
):
    """
    Mencari dokumen paling relevan menggunakan FAISS.
    """

    start_time = time.perf_counter()

    if not query or not query.strip():

        raise ValueError(
            "Query tidak boleh kosong."
        )

    # 1. Build index jika belum tersedia
    if _index is None:

        build_index()

    # 2. Generate query embedding
    embedding_start = time.perf_counter()

    query_embedding = _get_embedding(
        query,
        task_type="RETRIEVAL_QUERY"
    )

    embedding_elapsed = (
        time.perf_counter() - embedding_start
    )

    print(
        f"Waktu query embedding: "
        f"{embedding_elapsed:.2f} detik"
    )

    # 3. Convert menjadi NumPy
    query_vector = np.array(
        [query_embedding],
        dtype=np.float32
    )

    if query_vector.shape[1] != _index.d:

        raise ValueError(
            "Dimensi query embedding tidak sesuai "
            "dengan dimensi FAISS index."
        )

    # 4. Normalisasi query vector
    faiss.normalize_L2(
        query_vector
    )

    # 5. Search FAISS
    search_start = time.perf_counter()

    k = min(
        max(1, int(top_k)),
        _index.ntotal
    )

    scores, indices = _index.search(
        query_vector,
        k
    )

    search_elapsed = (
        time.perf_counter() - search_start
    )

    print(
        f"Waktu pencarian FAISS: "
        f"{search_elapsed:.4f} detik"
    )

    # 6. Collect hasil pencarian
    results = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        if idx < 0:
            continue

        results.append({
            "document": _documents[int(idx)],
            "score": float(score),
            "index": int(idx)
        })

    total_elapsed = (
        time.perf_counter() - start_time
    )

    print(
        f"Waktu semantic search: "
        f"{total_elapsed:.2f} detik"
    )

    return results


# ============================================================
# GENERATE ANSWER
# ============================================================

async def answer_from_knowledge_base(query: str) -> str:
    """
    Menjawab pertanyaan user menggunakan RAG.
    """

    total_start = time.perf_counter()

    # 1. Semantic search
    search_results = semantic_search(
        query,
        top_k=DEFAULT_TOP_K
    )

    if not search_results:

        return (
            "Maaf, saya tidak menemukan informasi "
            "yang relevan dalam knowledge base."
        )

    # 2. Prepare context
    context = "\n\n".join(
        [
            f"[Dokumen {i + 1}]\n{result['document']}"
            for i, result in enumerate(search_results)
        ]
    )

    # 3. Build prompt
    prompt = f"""
PERSONA:
Anda adalah IT Helpdesk Assistant yang membantu
karyawan menjawab pertanyaan mengenai kebijakan
dan prosedur IT perusahaan.

TASK:
Jawab pertanyaan user berdasarkan informasi
yang tersedia pada knowledge base.

CONTEXT:
{context}

USER QUESTION:
{query}

RULES:
1. Gunakan informasi dari CONTEXT sebagai sumber utama.
2. Jangan mengarang informasi yang tidak tersedia.
3. Jika informasi tidak ditemukan dalam CONTEXT,
   sampaikan bahwa informasi tersebut belum tersedia.
4. Jawab dengan bahasa Indonesia yang jelas dan mudah dipahami.
5. Jangan menyatakan sesuatu sebagai kebijakan resmi
   jika tidak didukung oleh CONTEXT.

FORMAT:
Berikan jawaban secara langsung, terstruktur,
dan mudah dipahami oleh karyawan.
"""

    # 4. Generate jawaban dengan Gemini
    client = _get_client()

    llm_start = time.perf_counter()

    try:

        response = _call_with_retry(
            lambda: client.models.generate_content(
                model=LLM_MODEL,
                contents=prompt
            )
        )

    except Exception as e:

        if _is_retryable_error(e):

            print(
                f"Gemini LLM gagal setelah retry: {e}"
            )

            return (
                "Maaf, layanan AI Helpdesk sedang "
                "mengalami gangguan atau permintaan "
                "sedang tinggi. Silakan coba kembali "
                "beberapa saat lagi."
            )

        raise

    llm_elapsed = (
        time.perf_counter() - llm_start
    )

    print(
        f"Waktu Gemini generate: "
        f"{llm_elapsed:.2f} detik"
    )

    if not response.text:

        raise RuntimeError(
            "Gemini tidak menghasilkan jawaban."
        )

    total_elapsed = (
        time.perf_counter() - total_start
    )

    print(
        f"Total waktu RAG: "
        f"{total_elapsed:.2f} detik"
    )

    return response.text.strip()

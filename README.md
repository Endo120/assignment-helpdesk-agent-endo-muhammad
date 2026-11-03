
# IT Helpdesk Assistant

Implementasi Assignment 4: **End-to-End RAG & AI Agent Development**.

IT Helpdesk Assistant merupakan aplikasi berbasis AI yang membantu karyawan mendapatkan informasi terkait kebijakan dan prosedur perusahaan serta melakukan pengecekan status tiket IT.

Aplikasi menggabungkan pendekatan **Retrieval-Augmented Generation (RAG)** menggunakan Google Gemini dan FAISS, serta mekanisme AI Agent sederhana untuk mengidentifikasi intent pengguna dan menjalankan fungsi pengecekan status tiket.

## Fitur Utama

- Menjawab pertanyaan FAQ berdasarkan knowledge base perusahaan.
- Melakukan pencarian informasi menggunakan semantic search.
- Menghasilkan jawaban menggunakan Gemini LLM.
- Mengidentifikasi intent pertanyaan secara otomatis.
- Melakukan pengecekan status tiket berdasarkan ID tiket.
- Menangani pertanyaan yang informasinya tidak tersedia.
- Memberikan respons terhadap pertanyaan di luar cakupan IT Helpdesk.
- Menyediakan REST API menggunakan FastAPI.
- Mendukung deployment menggunakan Docker.

## Struktur Project

```text
it_helpdesk_starter_repo/
├── app/
│   ├── __init__.py
│   ├── main.py           # Entry point FastAPI dan endpoint API
│   ├── router.py         # Intent detection dan routing
│   ├── rag.py            # Embedding, FAISS, semantic search, dan LLM
│   └── tools.py          # Fungsi pengecekan status tiket
│
├── data/
│   ├── it_helpdesk_knowledge_base.csv
│   └── mock_tickets.csv
│
├── Dockerfile
├── README.md
└── requirements.txt
```

## Teknologi yang Digunakan

| Teknologi | Fungsi |
|---|---|
| Python 3.11 | Bahasa pemrograman utama |
| FastAPI | Membangun REST API |
| Google Gemini API | Embedding dan generasi jawaban |
| FAISS | Penyimpanan dan pencarian vector embedding |
| Pandas | Membaca dan mengolah dataset CSV |
| NumPy | Pengolahan vector embedding |
| Docker | Containerization aplikasi |
| Uvicorn | Menjalankan aplikasi FastAPI |

## Arsitektur Aplikasi

Aplikasi memiliki dua jalur pemrosesan utama.

### 1. RAG (Retrieval-Augmented Generation)

Digunakan untuk menjawab pertanyaan mengenai kebijakan dan prosedur perusahaan berdasarkan knowledge base.

Alur pemrosesan:

1. Membaca knowledge base dari file CSV.
2. Mengubah dokumen menjadi vector embedding menggunakan Gemini Embedding.
3. Menyimpan vector embedding ke FAISS.
4. Mengubah pertanyaan pengguna menjadi vector embedding.
5. Melakukan semantic search untuk menemukan dokumen yang relevan.
6. Mengirimkan konteks yang ditemukan ke Gemini LLM.
7. Menghasilkan jawaban berdasarkan informasi dalam knowledge base.

### 2. AI Agent / Ticket Lookup

Digunakan untuk melakukan pengecekan status tiket IT.

Alur pemrosesan:

1. Menerima pertanyaan pengguna.
2. Mengidentifikasi intent pertanyaan menggunakan router.
3. Mengekstrak ID tiket dari pertanyaan.
4. Melakukan pencarian ID tiket pada mock tickets CSV.
5. Mengembalikan informasi tiket atau pesan jika tiket tidak ditemukan.

### Diagram Arsitektur

```text
                User
                  |
                  v
             FastAPI API
                  |
                  v
              Intent Router
                  |
          +-------+-------+
          |               |
          v               v
      FAQ / RAG       Ticket Lookup
          |               |
          v               v
   Gemini Embedding   Extract Ticket ID
          |               |
          v               v
       FAISS          Mock Tickets CSV
          |               |
          v               v
   Relevant Context    Ticket Result
          |
          v
      Gemini LLM
          |
          v
     Final Response
```

## Menjalankan Secara Lokal (Tanpa Docker)

### 1. Clone Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd it_helpdesk_starter_repo
```

### 2. Membuat Virtual Environment

```bash
python3.11 -m venv venv
```

Aktifkan virtual environment.

macOS/Linux:

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Gemini API Key

Pastikan environment variable `GEMINI_API_KEY` sudah diatur menggunakan API key dari Google AI Studio.

macOS/Linux:

```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

Model Gemini dapat dikonfigurasi melalui environment variable `GEMINI_MODEL` apabila diperlukan.

Contoh:

```bash
export GEMINI_MODEL="gemini-3.8-flash"
```

### 5. Menjalankan Aplikasi

```bash
uvicorn app.main:app --reload
```

Aplikasi berjalan pada:

```text
http://127.0.0.1:8000
```

Dokumentasi API Swagger dapat diakses melalui:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

| Method | Endpoint | Fungsi |
|---|---|---|
| GET | `/health` | Memeriksa status aplikasi |
| POST | `/ask` | Mengirim pertanyaan ke IT Helpdesk Assistant |

### Contoh Request FAQ

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Berapa jatah cuti tahunan karyawan tetap?"}'
```

Contoh response:

```json
{
  "status": "success",
  "intent": "faq",
  "data": "Karyawan tetap mendapatkan jatah 12 hari cuti tahunan..."
}
```

### Contoh Request Ticket Lookup

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Tolong cek status tiket TICKET-0002"}'
```

Contoh response:

```json
{
  "status": "success",
  "intent": "ticket_status",
  "data": "ID Tiket: TICKET-0002\nNama Karyawan: Sari Dewi\nKategori: Access\nSubject: Permintaan akses Google Analytics\nStatus: Diproses\nLast Update: 2026-08-25"
}
```

## Pengujian (Testing)

Pengujian dilakukan menggunakan endpoint `POST /ask` melalui Swagger UI dan Docker untuk memastikan setiap fitur berjalan sesuai kebutuhan.

### Ringkasan Hasil Pengujian

| ID | Skenario Pengujian | Hasil | Status |
|---|---|---|---|
| TC-01 | FAQ dengan informasi tersedia | Sistem berhasil menjawab berdasarkan knowledge base | PASS |
| TC-02 | FAQ dengan informasi tidak tersedia | Sistem menyampaikan bahwa informasi belum tersedia | PASS |
| TC-03 | Pengecekan tiket ditemukan | Sistem berhasil menampilkan detail tiket | PASS |
| TC-04 | Pengecekan tiket tidak ditemukan | Sistem menyampaikan bahwa tiket tidak ditemukan | PASS |
| TC-05 | Pertanyaan di luar cakupan IT Helpdesk | Sistem memberikan respons sesuai batasan knowledge base | PASS |

### Detail Hasil Pengujian

#### TC-01 — FAQ dengan Informasi Tersedia

Input:

```json
{
  "query": "Berapa jatah cuti tahunan karyawan tetap?"
}
```

Hasil aktual:

- Intent: `faq`
- Jatah cuti tahunan: 12 hari.
- Masa kerja minimal: 3 bulan.

Kesimpulan: Sistem berhasil mengambil informasi yang relevan dari knowledge base dan menghasilkan jawaban menggunakan Gemini.

Status: **PASS**

#### TC-02 — FAQ dengan Informasi Tidak Tersedia

Input:

```json
{
  "query": "Apakah perusahaan memberikan tunjangan transportasi bulanan?"
}
```

Hasil aktual:

- Intent: `faq`
- Sistem menyampaikan bahwa informasi tunjangan transportasi belum tersedia dalam knowledge base.
- Sistem menyarankan konfirmasi kepada HR atau atasan.

Kesimpulan: Sistem berhasil menangani pertanyaan yang informasinya tidak tersedia tanpa mengarang kebijakan perusahaan.

Status: **PASS**

#### TC-03 — Pengecekan Tiket yang Ditemukan

Input:

```json
{
  "query": "Tolong cek status tiket TICKET-0002"
}
```

Hasil aktual:

| Field | Hasil |
|---|---|
| ID Tiket | TICKET-0002 |
| Nama Karyawan | Sari Dewi |
| Kategori | Access |
| Subject | Permintaan akses Google Analytics |
| Status | Diproses |
| Last Update | 2026-08-25 |

Kesimpulan: Sistem berhasil mengidentifikasi ID tiket dan mengambil informasi yang sesuai dari mock tickets CSV.

Status: **PASS**

#### TC-04 — Pengecekan Tiket yang Tidak Ditemukan

Input:

```json
{
  "query": "Tolong cek status tiket TICKET-9999"
}
```

Hasil aktual:

```text
Tiket dengan ID TICKET-9999 tidak ditemukan.
```

Kesimpulan: Sistem berhasil menangani ID tiket yang tidak tersedia dalam dataset.

Status: **PASS**

#### TC-05 — Pertanyaan di Luar Cakupan IT Helpdesk

Input:

```json
{
  "query": "Siapa presiden Indonesia saat ini?"
}
```

Hasil aktual:

- Intent: `faq`
- Sistem menyampaikan bahwa informasi tidak tersedia dalam knowledge base.
- Sistem menjelaskan bahwa layanan hanya mencakup kebijakan dan prosedur perusahaan.

Kesimpulan: Sistem berhasil memberikan respons sesuai batasan cakupan layanan IT Helpdesk.

Status: **PASS**

### Kesimpulan Pengujian

Berdasarkan lima skenario pengujian yang telah dilakukan, seluruh skenario berhasil memenuhi hasil yang diharapkan.

| Metrik | Hasil |
|---|---:|
| Total skenario pengujian | 5 |
| PASS | 5 |
| FAIL | 0 |
| Tingkat keberhasilan | 100% |

Hasil pengujian menunjukkan bahwa aplikasi telah mampu menjalankan fungsi utama, yaitu menjawab FAQ menggunakan RAG, mengidentifikasi intent pengguna, melakukan pengecekan status tiket, serta menangani pertanyaan di luar cakupan layanan.

## Menjalankan dengan Docker

Aplikasi telah berhasil dibangun menjadi Docker image dan dijalankan menggunakan Docker Desktop.

### 1. Build Docker Image

Jalankan perintah berikut dari direktori utama project:

```bash
docker build -t it-helpdesk-assistant .
```

### 2. Menjalankan Container

```bash
docker run -d \
  --name it-helpdesk-container \
  -p 8000:8000 \
  -e GEMINI_API_KEY="YOUR_GEMINI_API_KEY" \
  it-helpdesk-assistant
```

### 3. Memeriksa Status Container

```bash
docker ps
```

### 4. Memeriksa Log Aplikasi

```bash
docker logs it-helpdesk-container
```

### 5. Mengakses Aplikasi

Setelah container berjalan, aplikasi dapat diakses melalui:

```text
http://localhost:8000/docs
```

### 6. Menguji Endpoint melalui Docker

Health check:

```bash
curl http://localhost:8000/health
```

FAQ:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Berapa jatah cuti tahunan karyawan tetap?"}'
```

Ticket lookup:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Tolong cek status tiket TICKET-0002"}'
```

### 7. Menghentikan Container

```bash
docker stop it-helpdesk-container
```

Menghapus container:

```bash
docker rm it-helpdesk-container
```

## Catatan

- Gemini API memerlukan API key yang valid.
- Penggunaan Gemini API mengikuti batas kuota dan rate limit sesuai project dan model yang digunakan.
- API key diberikan melalui environment variable dan tidak disimpan langsung di source code.
- FAISS index dibangun ketika aplikasi membutuhkan pencarian FAQ.
- Dataset knowledge base dan mock tickets menggunakan file CSV yang disediakan pada starter repository.
- Data tiket yang digunakan merupakan mock data untuk kebutuhan demonstrasi.
- Docker image menggunakan Python 3.11-slim sebagai base image.

## Kesimpulan

IT Helpdesk Assistant berhasil diimplementasikan dengan menggabungkan teknologi Retrieval-Augmented Generation (RAG) dan mekanisme AI Agent sederhana.

Aplikasi menyediakan dua fungsi utama, yaitu menjawab pertanyaan berdasarkan knowledge base perusahaan dan melakukan pengecekan status tiket IT.

Implementasi juga telah mencakup REST API menggunakan FastAPI, integrasi Google Gemini API, pencarian vector embedding menggunakan FAISS, serta containerization menggunakan Docker.

Berdasarkan pengujian yang dilakukan, seluruh lima skenario pengujian berhasil memenuhi hasil yang diharapkan.
# assignment-helpdesk-agent-endo-muhammad

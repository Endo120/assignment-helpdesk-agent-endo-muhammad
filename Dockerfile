# 🔧 TODO: lengkapi Dockerfile berikut mengikuti pola yang sudah dipelajari
# di Sesi 14.2 (FROM python -> WORKDIR -> COPY -> RUN pip -> CMD).

# Menggunakan Python 3.11 versi ringan
FROM python:3.11-slim

# Menentukan direktori kerja di dalam container
WORKDIR /app

# Copy requirements terlebih dahulu
COPY requirements.txt .

# Install seluruh dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code aplikasi dan dataset
COPY app/ ./app/
COPY data/ ./data/

# Port FastAPI
EXPOSE 8000

# Menjalankan aplikasi FastAPI menggunakan Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Gunakan image Python sebagai base
FROM python:3.9-slim

# Set direktori kerja di dalam container
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir requests regex

# Salin file script Python ke dalam container
COPY backup.py /app/grafana_backup.py

# Set environment variables (akan ditimpa oleh Kubernetes Pod)
ENV GRAFANA_URL=""
ENV API_KEY=""

# Perintah untuk menjalankan aplikasi Python
CMD ["python", "grafana_backup.py"]

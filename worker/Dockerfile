FROM python:3.9-slim-bookworm
WORKDIR /app

# Dependências de sistema para o OpenCV; limpa cache do apt para reduzir a imagem
RUN apt-get update && \
    apt-get install -y --no-install-recommends libglib2.0-0 libsm6 libxext6 libxrender-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Usuário não-root por segurança
RUN useradd --create-home appuser && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app
USER appuser

CMD ["python", "app.py"]
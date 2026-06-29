# =====================================================================
# Dockerfile do Nó Mestre
# Responsavel por receber imagens, dividir em SLICES fatias,
# publicar no RabbitMQ e consolidar os resultados dos workers.
# =====================================================================

# Imagem base Python leve (Debian Bookworm slim)
FROM python:3.9-slim-bookworm

# Define o diretorio de trabalho dentro do container
WORKDIR /app

# Dependencias de sistema para o OpenCV funcionar sem GUI
# libglib2.0-0: biblioteca de suporte GLib
# libsm6, libxext6, libxrender-dev: bibliotecas X11 para decodificacao
# Limpeza do cache do apt reduz o tamanho da imagem final
RUN apt-get update && \
    apt-get install -y --no-install-recommends libglib2.0-0 libsm6 libxext6 libxrender-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de dependencias Python primeiro (cache de camadas do Docker)
COPY requirements.txt .

# Instala as bibliotecas Python: flask, opencv, numpy, pika (RabbitMQ), requests
# --no-cache-dir: nao armazena cache do pip, reduz a imagem
RUN pip install --no-cache-dir -r requirements.txt

# Copia o codigo da aplicacao
COPY app.py .

# Cria usuario nao-root "appuser" por seguranca
# Cria a pasta /app/logs para os logs visuais (imagens de resultado)
# Transfere ownership para o appuser
RUN useradd --create-home appuser && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Muda para o usuario nao-root (container nunca roda como root)
USER appuser

# Comando de entrada: inicia o servidor Flask na porta 5000
CMD ["python", "app.py"]

# Imagem base oficial enxuta do Python
FROM python:3.11-slim

# Evita geração de arquivos .pyc e força flush imediato dos buffers de log
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STATE_FILE_PATH=/app/data/estado_links.json

# Criação de usuário não-privilegiado para segurança do contêiner
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

WORKDIR /app

# Instalação de dependências em camada cacheada
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cópia do código-fonte da aplicação
COPY src/ ./src/
COPY main.py .

# Criação da pasta de volume para armazenamento persistente do estado (Princípio I)
RUN mkdir -p /app/data && chown -R appuser:appuser /app

VOLUME ["/app/data"]

USER appuser

# Entrypoint daemon
CMD ["python", "main.py"]

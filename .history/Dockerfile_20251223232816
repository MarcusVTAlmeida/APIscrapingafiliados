# 1. Base Python
FROM python:3.11-slim

# 2. Instala dependências de SO que o Chromium requer
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgtk-3-0 \
    libxcb1 \
    libxss1 \
    libxshmfence1 \
    libxkbcommon0 \
    libdrm2 \
    libexpat1 \
  && rm -rf /var/lib/apt/lists/*

# 3. Cria diretório da app e copia requirements
WORKDIR /app
COPY requirements.txt .

# 4. Instala dependências Python (inclui fastapi, uvicorn, playwright, etc)
RUN pip install --no-cache-dir -r requirements.txt


# 6. Copia todo o seu código para /app
COPY . .

# 7. Comando para iniciar sua API
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

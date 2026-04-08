FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Exposer le port par défaut pour la documentation (Cloud Run gère le reste)
EXPOSE 8080

# Utilisation de "sh -c" pour s'assurer que la variable $PORT injectée par Cloud Run est bien lue
CMD sh -c "mcp run main.py --transport sse --port ${PORT:-8080}"

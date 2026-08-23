FROM python:3.10-slim

WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Exposition du port par défaut de Koyeb
EXPOSE 8000

# Commande de démarrage : Scraper en arrière-plan + API FastAPI sur le port 8000
CMD ["sh", "-c", "python scraper.py & uvicorn main:app --host 0.0.0.0 --port 8000"]

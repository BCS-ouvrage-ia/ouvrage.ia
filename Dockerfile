# Utiliser une image Python officielle
FROM python:3.11-slim

# Installer Graphviz
RUN apt-get update && apt-get install -y graphviz

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers locaux dans le conteneur
COPY . /app

# Installer les dépendances Python
RUN pip install -r requirements.txt

# Exposer le port 5000 pour Flask
EXPOSE 5000

# Lancer l'application Flask
CMD ["python", "main.py"]

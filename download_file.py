from pyuploadcare import Uploadcare
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Clés d'accès à Uploadcare
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

# Initialisation du client Uploadcare
uploadcare = Uploadcare(public_key=PUBLIC_KEY, secret_key=SECRET_KEY)

def download_from_asset_id(uuid, file_path):
    try:
        file = uploadcare.file(uuid)
        # download_url = file.cdn_url  # URL pour accéder au fichier
        file_info = file.info
        download_url = file_info.get('original_file_url')

        # Téléchargement du fichier avec requests
        response = requests.get(download_url)
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(response.content)
        else:
            print("Erreur lors de l'accès au fichier : code de statut", response.status_code)
    except Exception as e:
        print(f"Erreur lors du téléchargement : {e}")

# Appel de la fonction pour télécharger le fichier
# download_from_asset_id("file_uuid", "download_folder")

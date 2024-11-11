# utils.py

import requests
import json
import os
import hashlib
import os
import re

# Variables
COLLECTION_ID = os.getenv("COLLECTION_ID")
MEMOIRE_TECHNIQUE_GENERATED_COLLECTION_ID = os.getenv("MEMOIRE_TECHNIQUE_GENERATED_COLLECTION_ID")
WEBFLOW_API_TOKEN = os.getenv("WEBFLOW_API_TOKEN")
SITE_ID = os.getenv("SITE_ID")
ALLOWED_EXTENSIONS = {'pdf'}
WEBFLOW_GET_USER_ENDPOINT = 'https://api.webflow.com/v2/collections'


def allowed_file(filename):
    """
    Vérifie si le fichier a une extension autorisée.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_user_data_from_webflow(user_id):
    # Construire l'URL avec l'ID de l'utilisateur
    url = f"{WEBFLOW_GET_USER_ENDPOINT}/{COLLECTION_ID}/items/{user_id}"

    headers = {
        'Authorization': f'Bearer {WEBFLOW_API_TOKEN}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers)
        print(f"Statut de la réponse Webflow: {response.status_code}")
        print(f"Contenu de la réponse Webflow: {response.text}")
        # Vérifier si la requête a réussi
        if response.status_code == 200:
            # Décoder la réponse JSON
            return response.json()
        else:
            print(f"Erreur: statut de réponse {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête : {e}")
        raise e


    
def get_thread_id(nom_entreprise, filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            thread_ids = json.load(f)
    else:
        thread_ids = {}

    thread_id = thread_ids.get(nom_entreprise)
    return thread_id


def save_thread_id(nom_entreprise, thread_id, filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            thread_ids = json.load(f)
    else:
        thread_ids = {}

    thread_ids[nom_entreprise] = thread_id

    with open(filename, 'w') as f:
        json.dump(thread_ids, f)


def reset_file(filename):
        # Dictionnaire vide
    empty_dict = {}

    # Réinitialiser le fichier avec un dictionnaire vide
    with open(filename, 'w') as file:
        json.dump(empty_dict, file)


# Fonction pour remplacer \n par \u000A dans chaque text du JSON
def replace_newlines_in_text(data):
    # Parcourir chaque dictionnaire dans la liste
    for item in data:
        if "text" in item:
            # Remplacer \n par \u000A dans chaque texte
            item["text"] = str(item["text"]).replace("\n", "\u000A")
    return data


def generate_file_hash(file_path, hash_algorithm="md5"):
    """
    Génère un hash à partir d'un fichier PDF local.

    :param file_path: Chemin du fichier pour lequel le hash doit être généré
    :param hash_algorithm: Algorithme de hachage à utiliser (md5 ou sha256)
    :return: Le hash du fichier sous forme de chaîne hexadécimale
    """
    hash_func = hashlib.md5() if hash_algorithm == "md5" else hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def create_asset(file_path):
    file_name = os.path.basename(file_path)
    file_hash = generate_file_hash(file_path, hash_algorithm="md5")

    # En-têtes pour l'appel à l'API Webflow
    headers = {
        "Authorization": f"Bearer {WEBFLOW_API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Étape 1 : Obtenir les détails d'upload
    response = requests.post(
        f"https://api.webflow.com/v2/sites/{SITE_ID}/assets",
        headers=headers,
        json={
            "fileName": file_name,
            "fileHash": file_hash,
        },
    )

    #if response.status_code != 201:
    #    print(f"Erreur lors de la création de l'asset : {response.json()}")
    #    return None

    # Récupérer les détails d'upload
    data = response.json()
    upload_url = data.get('uploadUrl')
    upload_fields = data.get('uploadDetails')
    file_id = data.get('id')

    if not all([upload_url, upload_fields, file_id]):
        print("Détails d'upload manquants dans la réponse de l'API.")
        return None

    # Étape 2 : Uploader le fichier sur S3
    with open(file_path, 'rb') as f:
        files = {'file': (file_name, f, 'application/pdf')}
        # Les champs de formulaire doivent être inclus dans 'data'
        response = requests.post(upload_url, data=upload_fields, files=files)
    
    if response.status_code != 201:
        print(f"Erreur lors de l'upload du fichier sur S3 : {response.text}")
        return None

    # Étape 3 : Confirmer le succès de l'upload
    # À ce stade, l'asset est disponible sur Webflow
    asset_url = data.get('hostedUrl') or data.get('assetUrl')

    if asset_url:
        print(f"Asset créé avec succès : {asset_url}")
        return asset_url
    else:
        print("Impossible de récupérer l'URL de l'asset.")
        return None

def send_pdf_file(output_pdf_file, user_id):
    """
    Envoie un fichier PDF en tant qu'asset sur Webflow et ajoute un item dans la collection avec l'URL de l'asset et l'ID utilisateur.

    :param output_pdf_file: Chemin du fichier PDF local à envoyer
    :param user_id: Identifiant de l'utilisateur pour référence
    :return: True si l'opération réussit, False sinon
    """
    # Vérification de l'existence du fichier
    if not os.path.exists(output_pdf_file):
        print(f"Le fichier {output_pdf_file} n'existe pas.")
        return False

    # Création de l'asset et récupération de son URL
    asset_url = create_asset(output_pdf_file)
    if not asset_url:
        return False

    # Nom du fichier pour l'item
    file_name_with_ext = os.path.basename(output_pdf_file)
    file_name, file_extension = os.path.splitext(file_name_with_ext)
    
    # Génération du slug sans l'extension du fichier
    slug = file_name.replace(" ", "-").lower()
    
    # Supprimer les caractères non autorisés dans le slug
    slug = re.sub(r'[^a-z0-9_-]', '', slug)
    
    # Vérification que le slug commence par un caractère alphanumérique ou un underscore
    if not re.match(r'^[_a-zA-Z0-9]', slug):
        slug = f"slug-{slug}"

    headers = {
        "Authorization": f"Bearer {WEBFLOW_API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Création de l'item live dans la collection
    response = requests.post(
        f"https://api.webflow.com/v2/collections/{MEMOIRE_TECHNIQUE_GENERATED_COLLECTION_ID}/items/live",
        headers=headers,
        json={
            "isArchived": False,
            "isDraft": False,
            "fieldData": {
                "name": file_name_with_ext,  # Conserver l'extension dans le nom
                "slug": slug,
                "user-id": user_id,
                "pdf-2": asset_url
            }
        },
    )

    # Vérification de la réponse pour la création de l'item
    if response.status_code in [200, 201]:
        print("L'entrée a été ajoutée avec succès à la collection en mode live.")
        return True
    else:
        print(f"Erreur lors de la création de l'entrée dans la collection : {response.json()}")
        return False

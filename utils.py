# utils.py

import requests
import json
import os


ALLOWED_EXTENSIONS = {'pdf'}
# XANO_API_KEY = 'votre_cle_api_xano'
XANO_GET_USER_ENDPOINT = 'https://x8ki-letl-twmt.n7.xano.io/api:k69uEWXD/get_user_data'


def allowed_file(filename):
    """
    Vérifie si le fichier a une extension autorisée.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_user_data_from_xano(nom_entreprise):
    params = {
        'nom_entreprise': nom_entreprise
    }
    print(nom_entreprise)
    try:
        response = requests.get(XANO_GET_USER_ENDPOINT, params=params)
        #response.raise_for_status()
        print(response)
        if response.status_code == 200:
        # Décoder la réponse JSON
            return response.json()
    except requests.exceptions.RequestException as e:
        raise e

    
def get_thread_id(nom_entreprise, filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            thread_ids = json.load(f)
    else:
        thread_ids = {}
    print("milieu get thread_id")

    thread_id = thread_ids.get(nom_entreprise)
    print("fin_get_thread_id")
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
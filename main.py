from flask import Flask, request, jsonify
import os
import copy
import openai
import json
import requests
import threading
from queue import Queue
# Si local
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from utils import (
    generate_slug, 
    get_user_data_from_webflow, 
    get_thread_id, 
    save_thread_id,
    reset_file,
    send_pdf_file
)
from openai_api import (
    upload_file_to_openai,
    add_file_to_vector_store,
    run_assistant_interaction,
    create_thread,
    delete_file_in_openai,
)
from prompts import prompts, prompts_dossier
from download_file import download_from_asset_id
from pdf_generator import generate_pdf
from organigramme import generer_organigramme
from import_img import supprimer_images
import logging

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,  # Niveau de log
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),  # Sauvegarde les logs dans un fichier
        logging.StreamHandler()  # Affiche les logs dans la console
    ]
)


# Si local
load_dotenv()

app = Flask(__name__)

# Configuration
CONSULT_FOLDER = 'dossiers_consultations'
MEMOIRES_FOLDER = 'memoires_techniques'

# ID du vector store
VECTOR_STORE_ID = 'vs_vM8RUnO08wYP2Bg9wMRppEO4'
VECTOR_STORE_ID_ANALYSE_DOSSIER = 'vs_JEHExsSUFDlcOhPccPrLd4BT'  # Pour les dossiers de consultation

# ID Assistant
ASSISTANT_ID = 'asst_r6VpwkiZjhYzKkL1hIEsByzB'
ASSISTANT_ID_ANALYSE_DOSSIER = 'asst_f9Ebulahc8qf2vjsaxCPTgTr'

# Chemins des fichiers pour stocker les thread_id
THREAD_ID_FILE = 'thread_ids.json'
THREAD_ID_ANALYSE_DOSSIER_FILE = 'thread_ids_dossier.json'

# Clés API
openai.api_key = os.getenv('OPENAI_API_KEY')
BEARER_TOKEN = "61735865-8b6d-4cf4-8ceb-cb4a3901c357"

DOSSIER_CONSULTATION_COLLECTION_ID = os.getenv("DOSSIER_CONSULTATION_COLLECTION_ID")
WEBFLOW_API_TOKEN = os.getenv("WEBFLOW_API_TOKEN")

# Créer une queue globale et un verrou
task_queue = Queue()
processing_lock = threading.Lock()
is_processing = False

def worker():
    """Worker qui traite les tâches de la queue en série"""
    global is_processing
    while True:
        # Attendre une nouvelle tâche
        task = task_queue.get()
        if task is None:
            break
        
        user_id, file_id = task
        try:
            with processing_lock:
                is_processing = True
            with app.app_context():  # Assure le contexte de l'application
                process_asset(user_id, file_id)
        except Exception as e:
            logging.error(f"Erreur dans le worker: {str(e)}")
        finally:
            with processing_lock:
                is_processing = False
            task_queue.task_done()

# Démarrer le worker dans un thread séparé
worker_thread = threading.Thread(target=worker, daemon=True)
worker_thread.start()

def process_asset(user_id, file_id):
    consultation_file_id = None
    memoire_file_id = None
    
    try:
        # Récupère les données de l'utilisateur depuis Webflow
        user_data = get_user_data_from_webflow(user_id)

        if not user_data:
            raise ValueError('Données utilisateur introuvables')

        # Extraction des informations de l'utilisateur
        user_info = user_data
        field_data = user_info.get('fieldData', {})

        nom_entreprise = field_data.get('nom-entreprise')
        prenom = field_data.get('prenom')
        nom = field_data.get('nom')
        asset_id = field_data.get('memoire-technique-3')

        if not all([nom_entreprise, prenom, nom]):
            raise ValueError('Données utilisateur incomplètes')
        
        # Crée le nom de fichier selon la convention
        filename = f"{prenom}-{nom}-{nom_entreprise}-dossier-consultation.pdf"
        filename = secure_filename(filename)

        # Assure que les dossiers existent
        os.makedirs(CONSULT_FOLDER, exist_ok=True)
        os.makedirs(MEMOIRES_FOLDER, exist_ok=True)

        # Enregistre le fichier dans le dossier spécifié
        file_path = os.path.join(CONSULT_FOLDER, filename)
        download_from_asset_id(file_id, file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f'Le fichier de consultation n\'a pas pu être téléchargé: {file_path}')

        # Envoyer dossier consultation dans Webflow
        webflow_url = f"https://api.webflow.com/v2/collections/{DOSSIER_CONSULTATION_COLLECTION_ID}/items/live"
        headers = {
            "Authorization": f"Bearer {WEBFLOW_API_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "fieldData": {
                "user-id": user_id,
                "asset-id": file_id,
                "name": filename,
                "slug": generate_slug(filename)
            }
        }

        try:
            response = requests.post(webflow_url, headers=headers, json=data)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ValueError(f'Erreur lors de l\'envoi du dossier de consultation à l\'API Webflow: {str(e)}')

        # Chemin du fichier memoire technique
        memoire_filename = f"{prenom}-{nom}-{nom_entreprise}-memoire-technique.pdf"
        memoire_file_path = os.path.join(MEMOIRES_FOLDER, memoire_filename)

        # test asset_id
        # asset_id = "80f58944-8cd0-447d-b324-24b310bf99ae"

        # Enregistrer memoire technique
        download_from_asset_id(asset_id, memoire_file_path)

        if not os.path.exists(memoire_file_path):
            raise FileNotFoundError(f'Le fichier memoire technique associé est introuvable: {memoire_file_path}')

        # Upload du fichier dossier de consultation à OpenAI
        consultation_file_id = upload_file_to_openai(file_path, 'dossier-consultation.pdf', purpose='assistants')
        logging.info(f"consultation_file_id obtenu : {consultation_file_id}")

        # Upload du fichier mémoire technique à OpenAI
        memoire_file_id = upload_file_to_openai(memoire_file_path, 'memoire-technique.pdf', purpose='assistants')
        logging.info(f"memoire_file_id obtenu : {memoire_file_id}")

        """
        # Ajout des fichiers au vector store
        add_file_to_vector_store(VECTOR_STORE_ID_ANALYSE_DOSSIER, consultation_file_id)
        add_file_to_vector_store(VECTOR_STORE_ID, consultation_file_id)
        add_file_to_vector_store(VECTOR_STORE_ID, memoire_file_id)
        """
        try:
            response1 = add_file_to_vector_store(VECTOR_STORE_ID_ANALYSE_DOSSIER, consultation_file_id)
            logging.info(f"Ajout consultation_file_id au VECTOR_STORE_ID_ANALYSE_DOSSIER réussi : {response1}")
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout de consultation_file_id au VECTOR_STORE_ID_ANALYSE_DOSSIER : {e}")

        try:
            response2 = add_file_to_vector_store(VECTOR_STORE_ID, consultation_file_id)
            logging.info(f"Ajout consultation_file_id au VECTOR_STORE_ID réussi : {response2}")
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout de consultation_file_id au VECTOR_STORE_ID : {e}")

        try:
            response3 = add_file_to_vector_store(VECTOR_STORE_ID, memoire_file_id)
            logging.info(f"Ajout memoire_file_id au VECTOR_STORE_ID réussi : {response3}")
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout de memoire_file_id au VECTOR_STORE_ID : {e}")


        # Récupérer ou créer le thread_id pour le traitement du dossier de consultation
        thread_id_dossier = get_thread_id(nom_entreprise, THREAD_ID_ANALYSE_DOSSIER_FILE)
        if not thread_id_dossier:
            thread_id_dossier = create_thread()
            save_thread_id(nom_entreprise, thread_id_dossier, THREAD_ID_ANALYSE_DOSSIER_FILE)

        # Dictionnaire pour stocker les réponses du dossier de consultation
        assistant_responses_dossier = {}

        # Exécution des prompts pour le dossier de consultation
        for key, prompt in prompts_dossier.items():
            response = run_assistant_interaction(ASSISTANT_ID_ANALYSE_DOSSIER, prompt, thread_id_dossier)
            assistant_responses_dossier[key] = response

        print (f"Assistant reponses dossier : {assistant_responses_dossier}")

        # Récupérer ou créer le thread_id pour les prompts successifs
        thread_id = get_thread_id(nom_entreprise, THREAD_ID_FILE)
        if not thread_id:
            thread_id = create_thread()
            save_thread_id(nom_entreprise, thread_id, THREAD_ID_FILE)

        print (f"Thread ID : {thread_id}")

        # Dictionnaire pour stocker les réponses et variables pour remplacer les placeholders
        assistant_responses = {}
        variables = {
            'nom_projet': assistant_responses_dossier.get('nom_projet', ''),
            'infos_dossier_consultation': assistant_responses_dossier.get('infos_dossier_consultation', ''),
            'requis_dossier_consultation': assistant_responses_dossier.get('requis_dossier_consultation', ''),
            'documents_a_fournir': assistant_responses_dossier.get('documents_a_fournir', ''),
            'nom_entreprise': nom_entreprise
        }

        # Exécution des prompts successifs
        for key, prompt in prompts.items():
            formatted_prompt = prompt.format(**variables)
            response = run_assistant_interaction(ASSISTANT_ID, formatted_prompt, thread_id)
            assistant_responses[key] = response

            if key == 'moyens_humains':
                generer_organigramme(response)

            # Mise à jour des variables si nécessaire
            if key in ['nom_projet', 'infos_dossier_consultation', 'requis_dossier_consultation', 'documents_a_fournir']:
                variables[key] = response

        # Chemin du template
        template_path = 'template_memoire_technique.pdf'

        # Chemin de sortie du PDF final
        output_pdf_path = f"{prenom}-{nom}-{nom_entreprise}-memoire-technique-final.pdf"

        # Préparer les informations supplémentaires pour le PDF
        variables.update({
            'adresse': field_data.get('adresse', 'Adresse de l\'entreprise'),
            'numero_siren': field_data.get('numero_siren', 'Numéro de SIREN'),
            'chiffre_affaire': field_data.get('chiffre-affaire', 'Chiffre d\'affaires'),
            'code postal': field_data.get('code-postal', 'XXXXX'),
            'ville': field_data.get('ville', 'VILLE'),
            'email': field_data.get('email', 'xxxx@xxxxxx.fr')
        })
        # Séquence qui crée un fichier temporaire pour les positions modifiées

        with open('positions_data.json', 'r') as f:
            positions_data = json.load(f)

        # Faire une copie profonde (deep copy) des données
        positions_data_temp = copy.deepcopy(positions_data)

        # Les modifications que tu souhaites faire sur positions_data_temp
        for item in positions_data_temp:
            text_key = item['text']

            # Remplacer le texte par la donnée appropriée
            if text_key in variables:
                item['text'] = variables[text_key]
            elif text_key in assistant_responses:
                item['text'] = assistant_responses[text_key]
            else:
                # Si le texte n'est pas une variable, on le laisse tel quel
                pass

        # Écrire les données modifiées dans un nouveau fichier temporaire
        with open('positions_data_temp.json', 'w') as f:
            json.dump(positions_data_temp, f, indent=4)

        # Génération du PDF final
        try:
            generate_pdf(template_path, output_pdf_path, positions_data_temp, variables, memoire_file_path)
            if not os.path.exists(output_pdf_path):
                raise FileNotFoundError("Le PDF final n'a pas été généré")
        except Exception as e:
            raise Exception(f"Erreur lors de la génération du PDF: {str(e)}")

        # Envoi du PDF
        try:
            pdf_sent = send_pdf_file(output_pdf_path, user_id)
            if not pdf_sent:
                raise Exception("Échec de l'envoi du fichier PDF")
            logging.info(f"PDF envoyé avec succès pour l'utilisateur {user_id}")
        except Exception as e:
            raise Exception(f"Erreur lors de l'envoi du PDF: {str(e)}")

        return {
            "status": "success",
            "message": "Le mémoire technique a été généré avec succès.",
            "file_path": output_pdf_path
        }
    except Exception as e:
        logging.error(f"Erreur dans process_asset: {str(e)}")
        raise
    finally:
        # Nettoyage des fichiers OpenAI
        try:
            if consultation_file_id:
                delete_file_in_openai(consultation_file_id)
                logging.info(f"Fichier consultation {consultation_file_id} supprimé avec succès")
        except Exception as e:
            logging.error(f"Erreur lors de la suppression du fichier consultation {consultation_file_id}: {e}")

        try:
            if memoire_file_id:
                delete_file_in_openai(memoire_file_id)
                logging.info(f"Fichier mémoire {memoire_file_id} supprimé avec succès")
        except Exception as e:
            logging.error(f"Erreur lors de la suppression du fichier mémoire {memoire_file_id}: {e}")

        # Nettoyage des fichiers thread_id et images temporaires
        try:
            reset_file(THREAD_ID_FILE)
            reset_file(THREAD_ID_ANALYSE_DOSSIER_FILE)
            supprimer_images('images-memoire-technique-temp')
        except Exception as e:
            logging.error(f"Erreur lors du nettoyage final: {e}")

@app.route('/webhook/generer_memoire_technique', methods=['POST'])
def generer_memoire_technique():
    # Vérifie le token Bearer dans l'en-tête Authorization
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header.split()[0] != 'Bearer' or auth_header.split()[1] != BEARER_TOKEN:
        return jsonify({'status': 'error', 'message': 'Token Bearer invalide ou manquant'}), 403

    # Récupère le User ID depuis la requête
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'User ID manquant'}), 400

    file_id = request.json.get('asset_id')
    if not file_id:
        return jsonify({'status': 'error', 'message': 'Asset ID manquant'}), 400

    # Ajouter la tâche à la queue
    task_queue.put((user_id, file_id))
    
    # Vérifier si une tâche est en cours de traitement
    with processing_lock:
        currently_processing = is_processing

    # Préparer le message de réponse
    status_message = "Tâche ajoutée à la file d'attente. "
    if currently_processing:
        status_message += "Une autre tâche est en cours de traitement. Votre demande sera traitée dès que possible."
    else:
        status_message += "Le traitement va commencer immédiatement."

    return jsonify({
        'status': 'success',
        'message': status_message,
        'asset_id': file_id,
        'queue_size': task_queue.qsize()
    }), 200

# Ajouter une route pour vérifier le statut de la queue
@app.route('/status', methods=['GET'])
def get_status():
    with processing_lock:
        currently_processing = is_processing
    
    return jsonify({
        'is_processing': currently_processing,
        'queue_size': task_queue.qsize()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

from flask import Flask, request, jsonify
import os
import copy
import openai
import json
import requests
# Si local
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from utils import (
    allowed_file, 
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

# Si local
load_dotenv()

app = Flask(__name__)

# Configuration
CONSULT_FOLDER = 'dossiers_consultations'
MEMOIRES_FOLDER = 'memoires_techniques'

# ID du vector store
VECTOR_STORE_ID = 'vs_IyGzkG7HGPqpIFtuzr0UgiCR'
VECTOR_STORE_ID_ANALYSE_DOSSIER = 'vs_lc0RVpKtJO4pF5SVNJCssvTs'  # Pour les dossiers de consultation

# ID Assistant
ASSISTANT_ID = 'asst_IF9ukfPwD72IhQCRjJQM9dkf'
ASSISTANT_ID_ANALYSE_DOSSIER = 'asst_gb47ytL6g9zf04Hu8SFi7he6'

# Chemins des fichiers pour stocker les thread_id
THREAD_ID_FILE = 'thread_ids.json'
THREAD_ID_ANALYSE_DOSSIER_FILE = 'thread_ids_dossier.json'

# Clés API
openai.api_key = os.getenv('OPENAI_API_KEY')
BEARER_TOKEN = "61735865-8b6d-4cf4-8ceb-cb4a3901c357"

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

    # Récupère les données de l'utilisateur depuis Webflow
    user_data = get_user_data_from_webflow(user_id)

    if not user_data:
        return jsonify({'status': 'error', 'message': 'Données utilisateur introuvables'}), 400

    # Extraction des informations de l'utilisateur
    user_info = user_data
    field_data = user_info.get('fieldData', {})

    nom_entreprise = field_data.get('nom-entreprise')
    prenom = field_data.get('prenom')
    nom = field_data.get('nom')
    asset_id = field_data.get('memoire-technique-3')

    if not all([nom_entreprise, prenom, nom]):
        return jsonify({'status': 'error', 'message': 'Données utilisateur incomplètes'}), 400
    
    # Crée le nom de fichier selon la convention
    filename = f"{prenom}-{nom}-{nom_entreprise}-dossier-consultation.pdf"
    filename = secure_filename(filename)

    # Enregistre le fichier dans le dossier spécifié
    file_path = os.path.join(CONSULT_FOLDER, filename)
    download_from_asset_id(file_id, file_path)

    # Chemin du fichier memoire technique
    memoire_filename = f"{prenom}-{nom}-{nom_entreprise}-memoire-technique.pdf"
    memoire_file_path = os.path.join(MEMOIRES_FOLDER, memoire_filename)

    # test asset_id
    asset_id = "80f58944-8cd0-447d-b324-24b310bf99ae"

    # Enregistrer memoire technique
    download_from_asset_id(asset_id, memoire_file_path)
    '''
    try:
    # Requête pour télécharger le fichier PDF
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Vérifie si la requête a réussi
        
        # Téléchargement et écriture du fichier en chunks pour éviter la surcharge de mémoire
        with open(memoire_file_path, 'wb') as pdf_file:
            for chunk in response.iter_content(chunk_size=8192):
                pdf_file.write(chunk)
        
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement du fichier : {e}")
        return None

    if not os.path.exists(memoire_file_path):
        return jsonify({'status': 'error', 'message': f'Le fichier memoire technique associé est introuvable : {memoire_file_path}'}), 400
    '''

    try:
        # Upload du fichier dossier de consultation à OpenAI
        consultation_file_id = upload_file_to_openai(file_path, 'dossier-consultation.pdf', purpose='assistants')

        # Upload du fichier mémoire technique à OpenAI
        memoire_file_id = upload_file_to_openai(memoire_file_path, 'memoire-technique.pdf', purpose='assistants')

        # Ajout des fichiers au vector store
        add_file_to_vector_store(VECTOR_STORE_ID_ANALYSE_DOSSIER, consultation_file_id)
        add_file_to_vector_store(VECTOR_STORE_ID, consultation_file_id)
        add_file_to_vector_store(VECTOR_STORE_ID, memoire_file_id)

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

        # Récupérer ou créer le thread_id pour les prompts successifs
        thread_id = get_thread_id(nom_entreprise, THREAD_ID_FILE)
        if not thread_id:
            thread_id = create_thread()
            save_thread_id(nom_entreprise, thread_id, THREAD_ID_FILE)

        # Dictionnaire pour stocker les réponses et variables pour remplacer les placeholders
        assistant_responses = {}
        variables = {
            'nom_projet': assistant_responses_dossier.get('nom_projet', ''),
            'infos_dossier_consultation': assistant_responses_dossier.get('infos_dossier_consultation', ''),
            'requis_dossier_consultation': assistant_responses_dossier.get('requis_dossier_consultation', ''),
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
            if key in ['nom_projet', 'infos_dossier_consultation', 'requis_dossier_consultation']:
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
        generate_pdf(template_path, output_pdf_path, positions_data_temp, variables, memoire_file_path)

        send_pdf_file(output_pdf_path, user_id)
        delete_file_in_openai(consultation_file_id)
        delete_file_in_openai(memoire_file_id)
        reset_file(THREAD_ID_FILE)
        reset_file(THREAD_ID_ANALYSE_DOSSIER_FILE)
        supprimer_images('images-memoire-technique-temp')

        return jsonify({
            "status": "success",
            "message": "Le mémoire technique a été généré avec succès.",
            "file_path": output_pdf_path  # Facultatif, en fonction de vos besoins
        })
    except FileNotFoundError as e:
        return jsonify({'status': 'error', 'message': f'Fichier non trouvé: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Une erreur est survenue: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

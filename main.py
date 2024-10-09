from flask import Flask, request, jsonify, send_file
import requests
import os
import copy
import openai
import json
from werkzeug.utils import secure_filename
from utils import (
    allowed_file, 
    get_user_data_from_xano, 
    get_thread_id, 
    save_thread_id,
    reset_file
)
from openai_api import (
    upload_file_to_openai,
    add_file_to_vector_store,
    run_assistant_interaction,
    create_thread,
    delete_file_in_openai,
)
from prompts import prompts, prompts_dossier
from pdf_generator import generate_pdf
from organigramme import generer_organigramme


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

# Remplacez par votre endpoint API Xano réel
XANO_API_ENDPOINT_USERS = 'https://x8ki-letl-twmt.n7.xano.io/api:k69uEWXD/Add_User'
XANO_API_ENDPOINT_SEND_FILE = 'https://x8ki-letl-twmt.n7.xano.io/api:k69uEWXD/upload/image'

# Clés API
# XANO_API_KEY = 'votre_cle_api_xano'
openai.api_key = "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"

@app.route('/webhook-test/creer-nouveau-utilisateur', methods=['POST'])
def creer_nouveau_utilisateur():
    data = request.get_json()

    # Extraction des données reçues
    nom_entreprise = data.get('nom entreprise')
    prenom = data.get('prénom')
    nom = data.get('nom')
    email = data.get('email')
    role = data.get('role')
    annee_creation = data.get('année création')
    activite = data.get('activité')
    code_NAF = data.get('code NAF')
    adresse = data.get('adresse')
    ville = data.get('ville')
    code_postal = data.get('code postal')
    effectif = data.get('effectif')
    chiffre_affaire = data.get('numero_siren')
    numero_siren = data.get('numero_siren')

    # Préparation des données pour Xano
    payload = {
        'nom_entreprise': nom_entreprise,
        'prenom': prenom,
        'nom': nom,
        'email': email,
        'role': role,
        'annee_creation': annee_creation,
        'activite': activite,
        'code_NAF': code_NAF,
        'adresse': adresse,
        'ville': ville,
        'code_postal': code_postal,
        'effectif': effectif,
        'numero_siren': numero_siren,
        'chiffre_affaire': chiffre_affaire
    }

    headers = {
        'Content-Type': 'application/json',
        # 'Authorization': f'Bearer {XANO_API_KEY}'
    }

    # Envoi des données à Xano
    try:
        response = requests.post(XANO_API_ENDPOINT_USERS, json=payload, headers=headers)
        response.raise_for_status()
        return jsonify({'status': 'success', 'data': response.json()}), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500



@app.route('/webhook-test/enregistrer-memoire-technique', methods=['POST'])
def enregistrer_memoire_technique():
    # Vérifie si le fichier est présent dans la requête
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'Aucun fichier fourni'}), 400

    file = request.files['file']

    # Vérifie si un fichier a été sélectionné
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Aucun fichier sélectionné'}), 400

    if file and allowed_file(file.filename):
        # Récupère les données supplémentaires
        nom_entreprise = request.form.get('nom entreprise')
        prenom = request.form.get('prénom')
        nom = request.form.get('nom')

        if not all([nom_entreprise, prenom, nom]):
            return jsonify({'status': 'error', 'message': 'Données manquantes'}), 400

        # Crée le nom de fichier selon la convention
        filename = f"{prenom}-{nom}-{nom_entreprise}-memoire-technique.pdf"
        filename = secure_filename(filename)

        # Enregistre le fichier dans le dossier spécifié
        file_path = os.path.join(MEMOIRES_FOLDER, filename)
        file.save(file_path)

        # Envoie le fichier à Xano : Besoin Xano Premium
        '''
        headers = {
            # 'Authorization': f'Bearer {XANO_API_KEY}'
        }
        data = {
            'nom_entreprise': nom_entreprise,
            'prenom': prenom,
            'nom': nom
        }

        try:
            # Utilisation du bloc 'with' pour ouvrir le fichier
            with open(file_path, 'rb') as f:
                files = {
                    'file': (filename, f, 'application/pdf')
                }
                response = requests.post(XANO_API_ENDPOINT_SEND_FILE, headers=headers, files=files, data=data)
            response.raise_for_status()
            return jsonify({'status': 'success', 'message': 'Fichier envoyé à Xano avec succès'}), 200
        except requests.exceptions.RequestException as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
        '''
        
        # Uniquement la ligne qui suit, à supprimer après avoir fait l'intégration avec Xano premium
        return jsonify({'status': 'success', 'message': 'Memoire technique bien enregistre'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Type de fichier non autorisé. Seuls les PDF sont acceptés.'}), 400



@app.route('/webhook-test/generer_memoire_technique', methods=['POST'])
def generer_memoire_technique():
    # Vérifie si le fichier est présent dans la requête
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'Aucun fichier fourni'}), 400

    file = request.files['file']

    # Vérifie si un fichier a été sélectionné
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Aucun fichier sélectionné'}), 400

    if file and allowed_file(file.filename):
        # Récupère les données supplémentaires
        nom_entreprise = request.form.get('nom entreprise')
        prenom = request.form.get('prénom')
        nom = request.form.get('nom')

        if not all([nom_entreprise, prenom, nom]):
            return jsonify({'status': 'error', 'message': 'Données manquantes'}), 400

        # Crée le nom de fichier selon la convention
        filename = f"{prenom}-{nom}-{nom_entreprise}-dossier-consultation.pdf"
        filename = secure_filename(filename)

        # Enregistre le fichier dans le dossier spécifié
        file_path = os.path.join(CONSULT_FOLDER, filename)
        file.save(file_path)

        # Chemin du fichier memoire technique
        memoire_filename = f"{prenom}-{nom}-{nom_entreprise}-memoire-technique.pdf"
        memoire_file_path = os.path.join(MEMOIRES_FOLDER, memoire_filename)

        if not os.path.exists(memoire_file_path):
            return jsonify({'status': 'error', 'message': f'Le fichier memoire technique associé est introuvable : {memoire_file_path}'}), 400

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

            # Récupération des données depuis Xano
            user_data = get_user_data_from_xano(nom_entreprise)

            # Récupérer ou créer le thread_id
            thread_id = get_thread_id(nom_entreprise, THREAD_ID_FILE)
            if not thread_id:
                # Si aucun thread_id n'existe pour cette entreprise, en créer un nouveau
                thread_id = create_thread()
                save_thread_id(nom_entreprise, thread_id, THREAD_ID_FILE)

            assistant_responses = {}

            # Variables pour remplacer les placeholders
            variables = {
                'nom_projet': assistant_responses_dossier.get('nom_projet', ''),
                'infos_dossier_consultation': assistant_responses_dossier.get('infos_dossier_consultation', ''),
                'requis_dossier_consultation': assistant_responses_dossier.get('requis_dossier_consultation', ''),
                'nom_entreprise': nom_entreprise
            }

            # Exécution des prompts successifs
            for key, prompt in prompts.items():
                # Remplacement des placeholders dans le prompt
                formatted_prompt = prompt.format(**variables)

                # Interaction avec l'Assistant API
                response = run_assistant_interaction(ASSISTANT_ID, formatted_prompt, thread_id)

                # Stockage de la réponse
                assistant_responses[key] = response

                if key == 'moyens_humains':
                    generer_organigramme(response)

                # Mise à jour des variables si nécessaire
                if key in ['nom_projet', 'infos_dossier_consultation', 'requis_dossier_consultation']:
                    variables[key] = response

            template_path = 'template_memoire_technique.pdf'

            # Chemin de sortie du PDF final
            output_pdf_path = f"{prenom}-{nom}-{nom_entreprise}-memoire-technique-final.pdf"

            # Lire les données de positions depuis le fichier JSON
            with open('positions_data.json', 'r', encoding='utf-8') as f:
                positions_data = json.load(f)

            if user_data and isinstance(user_data[0], dict):
                user_dict = user_data[0]
            # Préparer les variables supplémentaires
            variables.update({
                'adresse': user_dict.get('adresse', 'Adresse de l\'entreprise'),
                'numero_siren': user_dict.get('numero_siren', 'Numéro de SIREN'),
                'chiffre_affaire': user_dict.get('chiffre_affaire', 'Chiffre d\'affaires'),
                'code postal': user_dict.get('code postal', 'XXXXX'),
                'ville': user_dict.get('ville', 'VILLE'),
                'email': user_dict.get('email', 'xxxx@xxxxxx.fr')
            })

            # Séquence qui créer un fichier temp :

            # Lire le fichier JSON source
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


            # Séquence qui modifie directement le fichier positions_data.json :
            """ 
            # Mettre à jour les données de positions avec les textes appropriés
            for item in positions_data:
                text_key = item.get('text')

                # Remplacer le texte par la donnée appropriée
                if text_key in variables:
                    item['text'] = variables[text_key]
                elif text_key in assistant_responses:
                    item['text'] = assistant_responses[text_key]
                # elif text_key.startswith("Nom "):
                #    num = text_key.split(" ")[1]
                #    item['text'] = user_data.get(f'nom_{num}', f'Nom {num}')
                # elif text_key.startswith("Poste "):
                #    num = text_key.split(" ")[1]
                #    item['text'] = user_data.get(f'poste_{num}', f'Poste {num}')
                else:
                    # Si le texte n'est pas une variable, on le laisse tel quel
                    pass
            """

            # Générer le PDF
            generate_pdf(template_path, output_pdf_path, positions_data_temp, variables)
            
            if os.path.exists('positions_data_temp.json'):
                os.remove('positions_data_temp.json')
            
            delete_file_in_openai(consultation_file_id)
            delete_file_in_openai(memoire_file_id)

            reset_file(THREAD_ID_FILE)
            reset_file(THREAD_ID_ANALYSE_DOSSIER_FILE)

            return send_file(output_pdf_path, as_attachment=True, mimetype='application/pdf')

            '''
            return jsonify({
                'status': 'success',
                'message': 'Processus terminé avec succès',
                'assistant_responses': assistant_responses,
                'pdf_generated': output_pdf_path
            }), 200

            '''
        except FileNotFoundError as e:
            return jsonify({'status': 'error', 'message': f'Fichier non trouvé: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Une erreur est survenue: {str(e)}'}), 500

    else:
        return jsonify({'status': 'error', 'message': 'Type de fichier non autorisé. Seuls les PDF sont acceptés.'}), 400



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

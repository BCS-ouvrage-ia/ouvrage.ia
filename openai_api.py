# openai_api.py

import openai
from pydantic import BaseModel
from typing import List
import time
import os
from openai import OpenAI

OPENAI_API_KEY = "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"
openai.api_key = "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"

# Modèle Pydantic pour représenter une personne avec son nom et poste
class PersonExtraction(BaseModel):
    nom: str
    poste: str

# Modèle pour représenter une équipe de personnes
class TeamExtraction(BaseModel):
    team: List[PersonExtraction]

def upload_file_to_openai(file_path, file_path_openai, purpose='assistants'):
    # Renommer le fichier en `file_path_openai`
    os.rename(file_path, file_path_openai)
    
    try:
        # Envoyer le fichier renommé à OpenAI
        with open(file_path_openai, 'rb') as f:
            response = openai.files.create(
                file=f,
                purpose=purpose
            )
        file_id = response.id

    finally:
        # Renommer le fichier à son nom original `file_path` après l'envoi
        os.rename(file_path_openai, file_path)
    
    return file_id


def add_file_to_vector_store(vector_store_id, file_id):
    response = openai.beta.vector_stores.files.create(
        vector_store_id=vector_store_id,
        file_id=file_id
    )
    return response

def create_thread():
    response = openai.beta.threads.create()
    return response.id



def run_assistant_interaction(assistant_id, message_content, thread_id):
    # Créer un message dans le thread existant
    thread_message = openai.beta.threads.messages.create(
        thread_id,
        role="user",
        content=message_content,
    )

    # Créer un run
    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    run_id = run.id

    # Récupérer le run jusqu'à ce que le statut soit "completed"
    while True:
        run_info = openai.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
        status = run_info.status
        if status == 'completed':
            break
        elif status == 'failed':
            raise Exception('Le run a échoué')
        else:
            time.sleep(1)  # Attendre avant de vérifier à nouveau

    # Extraire la réponse de l'assistant
    thread_messages = openai.beta.threads.messages.list(thread_id)
    messages = thread_messages.data
    assistant_response = ''

    # Parcourir les messages pour trouver la réponse de l'assistant
    for message in messages:
        if message.role == 'assistant':
            content_parts = message.content
            for part in content_parts:
                if part.type == 'text':
                    text_value = part.text.value
                    assistant_response += text_value
            break

    return assistant_response


def delete_file_in_openai(file_id):
    response = openai.files.delete(
        file_id = file_id
    )

    return response


def create_and_run_thread(assistant_id, messages):
    response = openai.beta.threads.create_and_run(
        assistant_id=assistant_id,
        thread={
            "messages": messages
        }
    )
    thread_id = response['id']
    run_id = response['latest_run']['id']
    return thread_id, run_id


def retrieve_run(thread_id, run_id):
    response = openai.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run_id
    )
    return response


def extract_team_from_text(text: str) -> List[dict]:
    """
    Fonction pour extraire des informations sur les noms et les postes à partir d'un texte non structuré.
    
    Args:
        text (str): Texte non structuré contenant des informations sur les personnes et leurs postes.
    
    Returns:
        List[dict]: Liste de dictionnaires représentant les noms et postes extraits.
    """
    try:
        # Message à envoyer au modèle GPT pour extraction structurée
        completion = openai.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at structured data extraction. You will be given unstructured text about people and their roles in a company, and you should convert it into a structured JSON format like [{ \"nom\": \"nom1\", \"poste\": \"poste1\" }, { \"nom\": \"nom2\", \"poste\": \"poste2\" }, ...]."},
                {"role": "user", "content": text}
            ],
            response_format=TeamExtraction  # Utilisation du modèle TeamExtraction défini avec Pydantic
        )

        # Récupération de la réponse structurée
        extracted_team = completion.choices[0].message.parsed.team

        # Convertir les objets Pydantic en dictionnaires
        return [person.dict() for person in extracted_team]

    except Exception as e:
        print(f"Erreur lors de l'extraction : {e}")
        return []
    
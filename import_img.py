import os
import openai
import requests
from flask import Flask, send_from_directory
import shutil
# Si local
from dotenv import load_dotenv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from openai import OpenAI
import base64
import fitz

# Si local
load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

IMGBB_API_KEY = '6ab00e1783ac20da3c3a8dde22a83f7a'

def extraire_images(pdf_path, output_folder):
    # Ouvrir le fichier PDF
    pdf_file = fitz.open(pdf_path)
    # S'assurer que le dossier de sortie existe
    os.makedirs(output_folder, exist_ok=True)
    image_counter = 0

    # Parcourir les pages du PDF
    for page_index in range(len(pdf_file)):
        page = pdf_file[page_index]
        images = page.get_images(full=True)
        # Parcourir les images de la page
        for img_index, img in enumerate(images[:15]):
            xref = img[0]
            base_image = pdf_file.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_name = f"image_{page_index+1}_{img_index+1}.{image_ext}"
            image_path = os.path.join(output_folder, image_name)
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            image_counter +=1
    print(f"{image_counter} images extraites.")


def servir_image(filename):
    return send_from_directory('images-memoire-technique-temp', filename)


def upload_image_and_get_public_url(image_path):
    try:
        with open(image_path, "rb") as file:
            payload = {
                "key": IMGBB_API_KEY,
                "image": base64.b64encode(file.read()),
                "expiration": 600  # Optionnel : suppression après 10 minutes
            }
        response = requests.post("https://api.imgbb.com/1/upload", data=payload)
        if response.status_code == 200:
            data = response.json()
            return data['data']['url']
        else:
            print(f"Erreur lors de l'upload de l'image {image_path}: {response.text}")
            return None
    except Exception as e:
        print(f"Erreur inattendue lors de l'upload de l'image {image_path}: {e}")
        return None


def classifier_image(image_url):
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Cette image représente-t-elle un 'chantier', une 'machine/outil/engin', "
                            "ou est-elle 'autre'? Répondez uniquement par 'chantier', 'machine/outil/engin' ou 'autres'. Image URL: {image_url}"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        }
                    },
                ],
            }
        ],
        max_tokens=20,
    )

    content = response.choices[0].message.content.strip().lower()
    return content


def traiter_images(image_folder):
    chantier_folder = os.path.join(image_folder, 'chantier')
    moe_folder = os.path.join(image_folder, 'machine_outil_engins')
    autres_folder = os.path.join(image_folder, 'autres')
    os.makedirs(chantier_folder, exist_ok=True)
    os.makedirs(moe_folder, exist_ok=True)
    os.makedirs(autres_folder, exist_ok=True)

    for filename in os.listdir(image_folder):
        filepath = os.path.join(image_folder, filename)
        if not os.path.isfile(filepath) or not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue  # Ignore les fichiers non valides

        image_path = os.path.join(image_folder, filename)
        image_url = None  # Initialisation
        classification = None  # Initialisation

        # Étape 1 : Obtenir une URL publique
        try:
            image_url = upload_image_and_get_public_url(image_path)
            if not image_url:
                raise ValueError("URL publique non obtenue.")
        except Exception as e:
            print(f"Erreur lors de l'obtention de l'URL publique pour {filename}: {e}")
            continue  # Passe à l'image suivante

        # Étape 2 : Classifier l'image
        try:
            classification = classifier_image(image_url)
            if not classification:
                raise ValueError("Classification échouée.")
        except Exception as e:
            print(f"Erreur lors de la classification de l'image {filename}: {e}")
            classification = 'autres'  # Par défaut

        # Étape 3 : Déplacer l'image
        try:
            if 'chantier' in classification:
                dest_folder = chantier_folder
            elif any(keyword in classification for keyword in ['machine', 'outil', 'engin']):
                dest_folder = moe_folder
            elif 'autres' in classification:
                dest_folder = autres_folder
            else:
                print(f"Classification inconnue pour {filename}, passage au suivant.")
                continue  # Passe à l'image suivante
            shutil.move(image_path, os.path.join(dest_folder, filename))
        except Exception as e:
            print(f"Erreur lors du déplacement de l'image {filename}: {e}")

    
def supprimer_images(image_folder):
    for root, dirs, files in os.walk(image_folder):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                os.remove(os.path.join(root, file))

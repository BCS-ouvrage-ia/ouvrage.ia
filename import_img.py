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

# Remplacez 'VOTRE_CLE_API' par votre clé API OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Remplacez 'VOTRE_CLE_API_IMGBB' par votre clé API IMGBB
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
        for img_index, img in enumerate(images):
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
    with open(image_path, "rb") as file:
        payload = {
            "key": IMGBB_API_KEY,
            "image": base64.b64encode(file.read()),
            "expiration": 600  # Optionnel : l'image sera supprimée après 600 secondes (10 minutes)
        }
    response = requests.post("https://api.imgbb.com/1/upload", data=payload)
    if response.status_code == 200:
        data = response.json()
        return data['data']['url']
    else:
        print(f"Erreur lors de l'upload de l'image {image_path}: {response.text}")
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
        if not os.path.isfile(filepath):
            continue
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        image_path = os.path.join(image_folder, filename)
        
        try:
            # Obtenir une URL publique pour l'image
            image_url = upload_image_and_get_public_url(image_path)
        except Exception as e:
            print(f"Erreur lors de l'obtention de l'URL publique de l'image : {e}")
            image_url = None

        try:
            # Classifier l'image en utilisant l'URL obtenue
            classification = classifier_image(image_url)
        except Exception as e:
            print(f"Erreur lors de la classification de l'image : {e}")
            classification = 'autre'
        
        if 'chantier' in classification:
            dest_folder = chantier_folder
        elif 'machine' in classification or 'outil' in classification or 'engin' in classification:
            dest_folder = moe_folder
        elif 'autre' in classification:
            dest_folder = autres_folder
        else:
            print(f"Impossible de classifier {filename}, passage au suivant.")
            continue
        shutil.move(image_path, os.path.join(dest_folder, filename))
    
def supprimer_images(image_folder):
    for root, dirs, files in os.walk(image_folder):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                os.remove(os.path.join(root, file))

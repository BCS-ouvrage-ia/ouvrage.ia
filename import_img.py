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

    '''

    for filename in os.listdir(image_folder):
        filepath = os.path.join(image_folder, filename)
        if not os.path.isfile(filepath):
            continue
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        image_path = os.path.join(image_folder, filename)
        
        # Obtenir une URL publique pour l'image
        image_url = upload_image_and_get_public_url(image_path)
        
        print(f"Analyse de {filename}...")
        classification = classifier_image(image_url)
        print(f"Classification: {classification}")
        
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

        '''
    
def supprimer_images(image_folder):
    for root, dirs, files in os.walk(image_folder):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                os.remove(os.path.join(root, file))


def creer_pdf(output_pdf_path, chantier_folder, moe_folder):
    c = canvas.Canvas(output_pdf_path, pagesize=A4)
    width, height = A4

    # Page 1: Images de 'chantier'
    # Boucler dans le vide pour ajouter 20 pages blanches (ou pages existantes)
    for page_number in range(1, 21):
    # Cette boucle crée 20 pages sans contenu
        c.showPage()
    chantier_images = [f for f in os.listdir(chantier_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))][:3]
    y_position = height - inch
    for img_file in chantier_images:
        img_path = os.path.join(chantier_folder, img_file)
        c.drawImage(ImageReader(img_path), inch, y_position - 200, width=width - 2*inch, height=200, preserveAspectRatio=True)
        y_position -= 220
    c.showPage()

    # Page 2: Images de 'machine_outil_engins'
    for page_number in range(1, 24):
    # Cette boucle crée 20 pages sans contenu
        c.showPage()
    moe_images = [f for f in os.listdir(moe_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))][:3]
    y_position = height - inch
    for img_file in moe_images:
        img_path = os.path.join(moe_folder, img_file)
        c.drawImage(ImageReader(img_path), inch, y_position - 200, width=width - 2*inch, height=200, preserveAspectRatio=True)
        y_position -= 220
    c.showPage()

    c.save()


def add_img(pdf_path, output_pdf):
    image_folder = 'images-memoire-technique-temp'

    # Extraire les images du PDF
    extraire_images(pdf_path, image_folder)

    # Traiter les images
    traiter_images(image_folder)

    # Créer le nouveau PDF
    chantier_folder = os.path.join(image_folder, 'chantier')
    moe_folder = os.path.join(image_folder, 'machine_outil_engins')
    autres_folder = os.path.join(image_folder, 'autres')
    creer_pdf(output_pdf, chantier_folder, moe_folder)
    print(f"PDF créé : {output_pdf}")
    supprimer_images(image_folder)

    return
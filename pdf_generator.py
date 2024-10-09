# pdf_generator.py

import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from pdfrw import PdfReader, PdfWriter, PageMerge
import textwrap
import os
from PIL import Image
from utils import replace_newlines_in_text
from import_img import extraire_images, traiter_images


# Fonction pour découper le texte en lignes qui tiennent dans la largeur spécifiée
def wrap_text(c, text, width):
    # Séparer les lignes manuelles avec \n
    paragraphs = text.split('\n')
    
    wrapped_lines = []
    
    # Traiter chaque paragraphe séparé par un \n
    for paragraph in paragraphs:
        if paragraph.strip():  # Ne pas ajouter de wrapping pour les lignes vides (causées par \n)
            # Mesurer la largeur d'un caractère moyen, ici on prend 'M' comme référence
            font_size = c._fontsize  # Taille de la police actuelle
            font_name = c._fontname   # Nom de la police actuelle
            
            # Largeur maximale d'un "M", pour estimer le nombre de caractères par ligne
            max_char_width = c.stringWidth('M', font_name, font_size)
            
            # Nombre approximatif de caractères qui tiennent sur la largeur spécifiée
            num_chars_per_line = int(width // max_char_width)
            
            # Utilisation de textwrap pour découper le texte en plusieurs lignes
            wrapped_lines.extend(textwrap.wrap(paragraph, width=num_chars_per_line))
        else:
            wrapped_lines.append('')  # Ajouter une ligne vide pour un retour à la ligne explicite

    return wrapped_lines


def max_height(wrapped_lines, line_height, max_paragraph_height):
    """
    Tronque les lignes pour qu'elles ne dépassent pas la hauteur maximale spécifiée,
    et s'arrête au dernier saut de ligne (\n) inclus dans la zone valide.
    
    :param wrapped_lines: Liste des lignes wrapées du paragraphe
    :param line_height: Hauteur d'une ligne (en points)
    :param max_paragraph_height: Hauteur maximale du paragraphe (en points)
    :return: Liste tronquée des lignes si nécessaire, jusqu'au dernier \n
    """
    total_height = 0
    last_newline_index = -1

    for i, line in enumerate(wrapped_lines):
        total_height += line_height

        if line == '':  # Si c'est une ligne vide (indiquant un \n explicite)
            last_newline_index = i

        # Si on dépasse la hauteur maximale, on s'arrête
        if total_height > max_paragraph_height:
            break

    # Si on dépasse, on coupe au dernier saut de ligne ou bien à la limite des lignes incluses
    if total_height > max_paragraph_height:
        if last_newline_index != -1:
            return wrapped_lines[:last_newline_index + 1]
        else:
            max_lines = int(max_paragraph_height // line_height)
            return wrapped_lines[:max_lines]

    return wrapped_lines  # Retourner tout si ça ne dépasse pas


def remove_reference_pattern(text):
    """
    Supprime les motifs du type 'nXX:YY†sourcen' et les astérisques doubles '**' dans le texte.
    """
    # Regex pour trouver et supprimer 'nXX:YY†sourcen'
    pattern_reference = r"\d+:\d+†source"
    # Supprimer les motifs 'nXX:YY†sourcen'
    text = re.sub(pattern_reference, "", text)

    # Supprimer toutes les occurrences de '**'
    pattern_asterisks = r"\*\*"  # Correspond aux doubles astérisques
    text = re.sub(pattern_asterisks, "", text)

    return text


def generate_pdf(template_path, output_path, positions_data, variables, memoire_file_path):

        # Remplacer les \n par \u000A dans les textes de positions_data
    positions_data = replace_newlines_in_text(positions_data)

    print(positions_data)

    # Lire le template PDF pour obtenir le nombre de pages
    template_pdf = PdfReader(template_path)
    num_pages = len(template_pdf.pages)

    # Créer un PDF temporaire avec le même nombre de pages
    temp_pdf_path = 'temp_overlay.pdf'
    c = canvas.Canvas(temp_pdf_path, pagesize=letter)

    # Obtenir la hauteur de la page
    page_width, page_height = A4

    print("étape 1 generate_pdf")
    #print(type(positions_data))
    #print(positions_data)

    # Créer un mapping des numéros de pages aux éléments à dessiner
    pages_content = {}  # clé : numéro de page, valeur : liste d'éléments
    for item in positions_data:
        page_num = int(item.get('pages', '0'))
        if page_num not in pages_content:
            pages_content[page_num] = []
        pages_content[page_num].append(item)

    print("étape 2 generate_pdf")

    image_folder = 'images-memoire-technique-temp'

    # Extraire les images du PDF
    extraire_images(memoire_file_path, image_folder)

    # Traiter les images
    traiter_images(image_folder)

    # Générer le contenu pour chaque page
    for page_num in range(num_pages):
        # Vérifier s'il y a des éléments pour cette page
        items = pages_content.get(page_num, [])
        if items:
            for item in items:
                # Extraire les données
                text = item.get('text')
                x = item.get('x')
                y = item.get('y')
                width = item.get('width')  # Chaque placeholder a son propre width
                height = item.get('height')
                alignment = item.get('alignment', 'left')
                color = item.get('color', '#000000')
                size = item.get('size', 12)
                font_name = item.get('fontName', 'Helvetica')
                font_bold = item.get('fontBold', False)

                if font_bold:
                    font_name += '-Bold'

                print("étape 3 generate_pdf")

                # Remplacer les variables dans le texte
                if text in variables:
                    text = variables[text]
                else:
                    text = variables.get(text, text)

                print("étape 4 generate_pdf")

                # Convertir la couleur hexadécimale en objet couleur
                color = HexColor(color)

                # Étape 1 : Supprimer les motifs "nXX:YY†sourcen"
                cleaned_text = remove_reference_pattern(text)

                # Définir la police et la taille
                c.setFont(font_name, size)
                c.setFillColor(color)

                # Ajuster le positionnement en fonction de l'origine de ReportLab
                y = page_height - y  # Inverser l'axe vertical

                print("étape 5 generate_pdf")

                # Découper le texte pour qu'il tienne dans la largeur spécifiée pour chaque placeholder
                wrapped_text_lines = wrap_text(c, str(cleaned_text), width)
                line_height = 20   #c._leading  # La hauteur d'une ligne de texte (espace entre les lignes)

                truncated_lines = max_height(wrapped_text_lines, line_height, height)

                for line in truncated_lines:
                    if line == '':
                        y -= line_height  # Retour à la ligne sans espace supplémentaire
                        continue
                    if alignment == 'center':
                        c.drawCentredString(x + width / 2, y, line)
                    elif alignment == 'right':
                        c.drawRightString(x + width, y, line)
                    else:
                        c.drawString(x, y, line)

                    # Déplacer le `y` vers le bas pour la ligne suivante
                    y -= int(line_height)
                    print(f"étape 6 generate_pdf. y : {y}")
                
        if page_num == 11:  # Python compte à partir de 0, donc la page 12 est indexée par 11
            try:
                image_width = 520  # Largeur de l'image
                image_height = 400  # Hauteur de l'image
                
                # Calcul des coordonnées pour centrer l'image
                image_x = (page_width - image_width) / 2  # Centrer horizontalement
                image_y = (page_height - image_height) / 2  # Centrer verticalement
                
                # Tenter de dessiner l'image
                c.drawImage('organigramme.png', image_x, image_y, image_width, image_height)
                print(f"Organigramme ajouté à la page {page_num + 1}")

            except FileNotFoundError:
                print(f"Erreur : Le fichier 'organigramme.png' n'a pas été trouvé.")
            except OSError as e:
                print(f"Erreur : Impossible de charger l'image. Détails : {e}")
            except Exception as e:
                print(f"Une erreur inattendue s'est produite lors de l'ajout de l'image : {e}")
        
        moe_folder = 'images-memoire-technique-temp/machine_outil_engins'
        chantier_folder = 'images-memoire-technique-temp/chantier'

        if page_num == 14:
            try:
                moe_images = [f for f in os.listdir(moe_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))][:3]
                y_position = 750  # Position initiale de y (proche du haut de la page)
                for img_file in moe_images:
                    img_path = os.path.join(moe_folder, img_file)
                    image = Image.open(img_path)
                        # Obtenir la taille de l'image en pixels
                    img_width, img_height = image.size
                        # Convertir la taille de l'image de pixels à points (1 pouce = 72 points)
                        # En supposant que l'image est en 72 DPI par défaut si aucune information n'est fournie
                    img_width_pt = img_width * 72.0 / image.info.get('dpi', (72, 72))[0]
                    img_height_pt = img_height * 72.0 / image.info.get('dpi', (72, 72))[1]
                    c.drawImage(ImageReader(img_path), inch, y_position - img_height_pt, width=img_width_pt, height=img_height_pt)
                    y_position -= (img_height_pt + inch)
            except:
                print("erreur images machine outil engins page 15")
        
        if page_num == 22:
            try:
                chantier_images = [f for f in os.listdir(chantier_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))][:3]
                y_position = 750  # Position initiale de y (proche du haut de la page)
                for img_file in chantier_images:
                    img_path = os.path.join(chantier_folder, img_file)
                    image = Image.open(img_path)
                        # Obtenir la taille de l'image en pixels
                    img_width, img_height = image.size
                        # Convertir la taille de l'image de pixels à points (1 pouce = 72 points)
                        # En supposant que l'image est en 72 DPI par défaut si aucune information n'est fournie
                    img_width_pt = img_width * 72.0 / image.info.get('dpi', (72, 72))[0]
                    img_height_pt = img_height * 72.0 / image.info.get('dpi', (72, 72))[1]
                    c.drawImage(ImageReader(img_path), inch, y_position - img_height_pt, width=img_width_pt, height=img_height_pt)
                    y_position -= (img_height_pt + inch)
            except:
                print("erreur images chantiers page 23")
                
        # Passer à la page suivante
        c.showPage()
    

    # Finaliser le PDF temporaire
    c.save()

    print("étape save temporaire")

    # Lire le PDF temporaire
    overlay_pdf = PdfReader(temp_pdf_path)

    print("étape 7 generate_pdf")

    # Fusionner les deux PDFs
    for page_num in range(num_pages):
        template_page = template_pdf.pages[page_num]
        if page_num < len(overlay_pdf.pages):
            overlay_page = overlay_pdf.pages[page_num]
            merger = PageMerge(template_page)
            merger.add(overlay_page).render()

    # Écrire le PDF final
    PdfWriter().write(output_path, template_pdf)

    # Supprimer le fichier temporaire
    os.remove(temp_pdf_path)


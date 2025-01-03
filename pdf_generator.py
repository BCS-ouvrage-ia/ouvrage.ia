# pdf_generator.py

import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from pdfrw import PdfReader, PdfWriter, PageMerge
import textwrap
import os
from PIL import Image
from utils import replace_newlines_in_text
from import_img import extraire_images, traiter_images


def wrap_text(c, text, width):
    paragraphs = text.split('\n')
    wrapped_lines = []
    for paragraph in paragraphs:
        if paragraph.strip():
            font_size = c._fontsize
            font_name = c._fontname
            max_char_width = c.stringWidth('M', font_name, font_size)
            num_chars_per_line = int(width // max_char_width)
            wrapped_lines.extend(textwrap.wrap(paragraph, width=num_chars_per_line))
        else:
            wrapped_lines.append('')
    return wrapped_lines

def max_height(wrapped_lines, line_height, max_paragraph_height):
    total_height = 0
    last_newline_index = -1

    for i, line in enumerate(wrapped_lines):
        total_height += line_height
        if line == '':
            last_newline_index = i
        if total_height > max_paragraph_height:
            break

    if total_height > max_paragraph_height:
        if last_newline_index != -1:
            truncated_lines = wrapped_lines[:last_newline_index + 1]
        else:
            max_lines = int(max_paragraph_height // line_height)
            truncated_lines = wrapped_lines[:max_lines]
    else:
        truncated_lines = wrapped_lines

    if truncated_lines and (truncated_lines[-1] == '' or truncated_lines[-1].strip().endswith(':')):
        truncated_lines = truncated_lines[:-1]

    return truncated_lines

def remove_reference_pattern(text):
    pattern_reference = r"\d+:\d+†source"
    text = re.sub(pattern_reference, "", text)
    pattern_asterisks = r"\*\*"
    text = re.sub(pattern_asterisks, "", text)
    return text

def place_images_vertically_on_page(c, images, page_width, page_height):
    """
    Place les images verticalement, 3 images par page.
    Chaque image est redimensionnée proportionnellement pour tenir dans la zone définie.
    Utilisation de preserveAspectRatio=True pour conserver le ratio.
    """
    if not images:
        return
    num_images = len(images)
    images_per_page = 3

    # On réduit ici l'espace vertical maximal par image afin d'éviter le chevauchement
    # Ajout de marge supplémentaire sur la page
    max_img_height = (page_height - 4 * inch) / images_per_page
    horizontal_margin = inch
    usable_width = page_width - (2 * horizontal_margin)
    y_position = page_height - inch

    for img_path in images:
        try:
            with Image.open(img_path) as image:
                img_width, img_height = image.size

                # Calcul du ratio
                ratio_w = usable_width / float(img_width)
                ratio_h = max_img_height / float(img_height)
                scale_ratio = min(ratio_w, ratio_h)

                new_width = img_width * scale_ratio
                new_height = img_height * scale_ratio

                x_position = (page_width - new_width) / 2.0

                # Utilisation de preserveAspectRatio et anchor pour maintenir les proportions
                c.drawImage(
                    ImageReader(img_path),
                    x_position,
                    y_position - new_height,
                    width=new_width,
                    height=new_height,
                    preserveAspectRatio=True,
                    anchor='c'
                )

                # Déplacement du point de dessin pour l'image suivante
                y_position = y_position - new_height - inch

        except Exception as e:
            print(f"Erreur lors du traitement de l'image {img_path} : {e}")
            continue

def generate_pdf(template_path, output_path, positions_data, variables, memoire_file_path):
    positions_data = replace_newlines_in_text(positions_data)

    template_pdf = PdfReader(template_path)
    num_pages = len(template_pdf.pages)

    temp_pdf_path = 'temp_overlay.pdf'
    c = canvas.Canvas(temp_pdf_path, pagesize=A4)
    page_width, page_height = A4

    pages_content = {}
    for item in positions_data:
        page_num = int(item.get('pages', '0'))
        if page_num not in pages_content:
            pages_content[page_num] = []
        pages_content[page_num].append(item)

    image_folder = 'images-memoire-technique-temp'

    # Extraction et traitement des images
    try:
        # Extraction et traitement des images avec gestion des erreurs
        try:
            extraire_images(memoire_file_path, image_folder)
        except Exception as e:
            print(f"Erreur lors de l'extraction des images : {e}")

        try:
            traiter_images(image_folder)
        except Exception as e:
            print(f"Erreur lors du traitement des images : {e}")

        moe_folder = os.path.join(image_folder, 'machine_outil_engins')
        all_images = [
            os.path.join(moe_folder, f)
            for f in os.listdir(moe_folder)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]
    except Exception as e:
        print(f"Erreur critique dans le traitement des images : {e}")
        all_images = []
        
    # On suppose qu'on a au moins 12 images
    first_6_images = all_images[0:6]
    first_3_page_15 = first_6_images[0:3]  # Page 15 (index 14)
    next_3_page_16 = first_6_images[3:6]   # Page 16 (index 15)

    second_6_images = all_images[6:12]
    first_3_page_24 = second_6_images[0:3]  # Page 24 (index 23)
    next_3_page_25 = second_6_images[3:6]   # Page 25 (index 24)

    for page_num in range(num_pages):
        items = pages_content.get(page_num, [])
        if items:
            for item in items:
                text = item.get('text')
                x = item.get('x')
                y = item.get('y')
                width = item.get('width')
                height = item.get('height')
                alignment = item.get('alignment', 'left')
                color = item.get('color', '#000000')
                size = item.get('size', 12)
                font_name = item.get('fontName', 'Helvetica')
                font_bold = item.get('fontBold', False)

                if font_bold:
                    font_name += '-Bold'

                if text in variables:
                    text = variables[text]
                else:
                    text = variables.get(text, text)

                color = HexColor(color)
                cleaned_text = remove_reference_pattern(text)

                c.setFont(font_name, size)
                c.setFillColor(color)

                # Conversion pour alignement vertical sur page A4
                y = page_height - y

                wrapped_text_lines = wrap_text(c, str(cleaned_text), width)
                line_height = 20
                if item.get('text') == 'planning':
                    # Gestion multi-pages
                    available_height = height
                    for line in wrapped_text_lines:
                        if available_height < line_height:
                            c.showPage()
                            c.setFont(font_name, size)
                            c.setFillColor(color)
                            available_height = height
                            y = page_height - item.get('y')

                        if line == '':
                            y -= line_height
                            available_height -= line_height
                            continue

                        if alignment == 'center':
                            c.drawCentredString(x + width / 2, y, line)
                        elif alignment == 'right':
                            c.drawRightString(x + width, y, line)
                        else:
                            c.drawString(x, y, line)

                        y -= line_height
                        available_height -= line_height
                else:
                    truncated_lines = max_height(wrapped_text_lines, line_height, height)
                    for line in truncated_lines:
                        if line == '':
                            y -= line_height
                            continue
                        if alignment == 'center':
                            c.drawCentredString(x + width / 2, y, line)
                        elif alignment == 'right':
                            c.drawRightString(x + width, y, line)
                        else:
                            c.drawString(x, y, line)
                        y -= int(line_height)

        # Organigramme page 12 (index 11)
        if page_num == 11:
            try:
                image_width = 520
                image_height = 400
                image_x = (page_width - image_width) / 2
                image_y = (page_height - image_height) / 2
                c.drawImage('organigramme.png', image_x, image_y, image_width, image_height, preserveAspectRatio=True, anchor='c')
            except FileNotFoundError:
                print("Erreur : Le fichier 'organigramme.png' n'a pas été trouvé.")
            except OSError as e:
                print(f"Erreur lors du chargement de l'image : {e}")
            except Exception as e:
                print(f"Erreur inattendue lors de l'ajout de l'image : {e}")

        # Pages 15 (index 14) et 16 (index 15)
        if page_num == 14:  # Page 15
            place_images_vertically_on_page(c, first_3_page_15, page_width, page_height)
        if page_num == 15:  # Page 16
            place_images_vertically_on_page(c, next_3_page_16, page_width, page_height)

        # Pages 24 (index 23) et 25 (index 24)
        if page_num == 23:  # Page 24
            place_images_vertically_on_page(c, first_3_page_24, page_width, page_height)
        if page_num == 24:  # Page 25
            place_images_vertically_on_page(c, next_3_page_25, page_width, page_height)

        c.showPage()

    c.save()

    overlay_pdf = PdfReader(temp_pdf_path)

    for page_num in range(num_pages):
        template_page = template_pdf.pages[page_num]
        if page_num < len(overlay_pdf.pages):
            overlay_page = overlay_pdf.pages[page_num]
            merger = PageMerge(template_page)
            merger.add(overlay_page).render()

    PdfWriter().write(output_path, template_pdf)
    os.remove(temp_pdf_path)


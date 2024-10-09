from __future__ import annotations
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import json
import openai
from graphviz import Digraph
from openai_api import extract_team_from_text

# Si local
load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')


def generate_design(employee: Employee, dot=None):
    if dot is None:
        dot = Digraph(comment='Organigramme')
    label = f"{employee.nom}\n({employee.poste})"
    dot.node(employee.nom, label)
    if employee.subordinates:
        for sub in employee.subordinates:
            sub_label = f"{sub.nom}\n({sub.poste})"
            dot.node(sub.nom, sub_label)
            dot.edge(employee.nom, sub.nom)
            generate_design(sub, dot)
    return dot


class Employee(BaseModel):
    nom: str
    poste: str
    subordinates: Optional[List[Employee]] = None


def generer_organigramme(data):

    data = extract_team_from_text(data)

    # Création du prompt
    prompt = f"""
    Vous êtes un expert en extraction de données structurées. Vous allez recevoir une liste d'employés avec leurs noms et postes, et vous devez les convertir en une structure hiérarchique selon le modèle donné.

    Voici la liste des employés au format JSON :

    {json.dumps(data, ensure_ascii=False)}

    Générez la hiérarchie en respectant le format du modèle Employee, qui est défini comme suit :

    class Employee(BaseModel):
        nom: str
        poste: str
        subordinates: Optional[List[Employee]] = None

    Assurez-vous que la hiérarchie est correctement structurée et que le JSON est bien formaté.
    """

    response = openai.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Vous êtes un assistant utile qui fournit des données au format JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format=Employee,
    )

    # Extraire le résultat parsé
    hierarchy = response.choices[0].message.parsed

    dot = generate_design(hierarchy)
    dot.render('organigramme', format='png', cleanup=True)

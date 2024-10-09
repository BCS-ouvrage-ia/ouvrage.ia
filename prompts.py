# prompts.py

prompts_dossier = {
                "nom_projet": "Extrait le nom du projet de l'appel d’offre suivant : dossier-consultation.pdf.\nTu renverras uniquement le nom de l'appel d'offre brut.",
                "infos_dossier_consultation": "Extrait les principales informations du dossier de consultation suivant : dossier-consultation.pdf.\nLes informations à extraire (si présentes) :\n- Nom du client / contractant\n- Secteur d'activité / marché\n- Date limite de dépôt de candidature\n- Date début du chantier\n- Date maximum fin de chantier",
                "requis_dossier_consultation": "Analyse les exigences principales et secondaires du dossier de consultation suivant : dossier-consultation.pdf. Sois exhaustif."
            }


prompts = {
    "historique": """Tu es un expert en rédaction de mémoires techniques dans le secteur du BTP en France, spécialisé dans les réponses aux appels d’offres publics pour remporter des marchés.

Ton objectif est de rédiger une partie spécifique du mémoire technique pour le projet suivant : {nom_projet}. Le dossier de consultation relatif à cet appel d’offre est disponible dans le fichier 'dossier-consultation.pdf', et voici les informations clés extraites du dossier de consultation :
{infos_dossier_consultation}

Tu dois rédiger la section « Historique » du mémoire technique de la société {nom_entreprise}.

Cette section devra inclure :
- La date de création de l’entreprise
- Son secteur d’activité
- Toute autre information pertinente, que tu pourras extraire du fichier 'memoire-technique.pdf'.

Assure-toi que le texte respecte les normes de rédaction des mémoires techniques dans le secteur du BTP, tout en restant clair, précis et pertinent vis-à-vis de l’appel d’offre.""",
    "expertise": """Rédige la section « Expertise » du mémoire technique de la société {nom_entreprise}. Cette section doit s’inscrire dans la continuité de la partie « Historique » mais sans répéter les informations déjà mentionnées dans cette dernière. L'objectif est de mettre en avant les compétences, les domaines de spécialisation et l’expérience spécifique de l’entreprise.

Appuie-toi sur les informations pertinentes issues du fichier 'memoire-technique.pdf' pour illustrer l’expertise technique, les projets réalisés, et la capacité de l’entreprise à répondre aux exigences du marché. Utilise des termes tels que "expérience", "spécialisés", "experts", et d’autres mots clés qui renforcent l'image d'une entreprise compétente et fiable dans le secteur.

Veille à ce que ce paragraphe, d'une longueur de 10 à 15 lignes, réponde précisément aux attentes du règlement de consultation, tout en évitant les répétitions avec la section « Historique ».""",
    "vision_et_valeurs": """Rédige la partie « Vision et Valeurs » du mémoire technique de la société {nom_entreprise}. Ce mémoire technique doit répondre au dossier de consultation suivant : dossier-consultation.pdf
Exemple :
"Attirée par les défis, et soucieuse d’apprendre de chaque projet, notre entreprise s’engage à trouver une solution pour chaque problème. Pour cette raison, toutes nos réalisations sont garanties de résultats. Notre équipe qualifiée reste disponible pour vous assurer une assistance 7j/7."
Ce paragraphe fera entre 5 et 10 lignes.""",
    "conformite": """Rédige la conclusion de l'introduction du mémoire technique pour la société {nom_entreprise}. Ce mémoire doit répondre précisément aux exigences du dossier de consultation : dossier-consultation.pdf. Tu t'assureras de mentionner la conformité aux attentes, le respect des modalités et délais de soumission, les visites obligatoires (si applicables), ainsi que les documents complémentaires fournis.
Utilise pour cela les prérequis extraits du dossier de consultation suivants :
"{requis_dossier_consultation}"
Ce paragraphe fera entre 5 et 10 lignes.""",
    "services_et_competences": """Rédige la partie « Détail des Services et des Compétences » du mémoire technique de la société {nom_entreprise}. Pour cela, liste les services, techniques, spécificités et domaines d'intervention spécifiques sous la forme de bullet points. Tu utiliseras les infos pertinentes récupérées à partir du fichier 'memoire-technique.pdf' pour répondre parfaitement au règlement de consultation suivant : dossier-consultation.pdf""",
    "competences_techniques_specifiques": """Rédige la partie « Compétences Techniques Spécifiques » du mémoire technique de la société {nom_entreprise}. Tu utiliseras les infos pertinentes récupérées à partir du fichier 'memoire-technique.pdf' pour répondre parfaitement au règlement de consultation suivant : dossier-consultation.pdf""",
    "moyens_humains": """Résume les noms, prénoms, postes, rôles et informations concernant tous les membres de l'équipe mentionnés dans le fichier 'memoire-technique.pdf'. Puis, propose un organigramme clair et structuré, illustrant la répartition des équipes et la hiérarchie au sein de l’organisation.""",
    "qualifications": """Rédige la section « Moyens Humains et Qualifications » du mémoire technique de la société {nom_entreprise}.
Décris la totalité des qualifications et les compétences des membres clés de la structure, en mettant l’accent sur leur expertise et leur adéquation aux exigences du projet.
Utilise les informations pertinentes extraites du fichier 'memoire-technique.pdf' pour détailler ces éléments, tout en t’assurant que les moyens humains présentés répondent parfaitement aux exigences spécifiées dans le règlement de consultation, notamment celles-ci :
"{requis_dossier_consultation}"
Veille à ce que la présentation des ressources humaines et des qualifications soit précise, pertinente et conforme aux attentes du règlement de consultation, afin de démontrer la capacité de l’entreprise à mener à bien le projet.""",
    "moyens_techniques": """Rédige la section « Moyens Techniques » du mémoire technique de la société {nom_entreprise}.
Dans cette partie, détaille les moyens matériels que l'entreprise met à disposition pour l’exécution des projets, en mettant en avant les équipements spécifiques, leur capacité, et leur adéquation aux besoins du projet. Insiste sur l'efficacité, la modernité et la pertinence de ces équipements par rapport aux défis techniques du marché.
Utilise les informations pertinentes issues du fichier 'memoire-technique.pdf' pour illustrer et justifier ces moyens matériels, tout en veillant à ce qu’ils répondent précisément aux exigences du règlement de consultation, notamment les prérequis suivants :
"{requis_dossier_consultation}"
Cette section doit démontrer que les moyens techniques présentés sont en parfaite adéquation avec les besoins du projet, tout en respectant les critères de performance et de qualité attendus.""",
    "engagement_qualite": """Rédige la partie « Engagements Qualité » du mémoire technique de la société {nom_entreprise}. Pour cela, tu mettras l'accent sur l'engagement de la société vers la qualité du chantier.
Tu utiliseras les infos pertinentes récupérées à partir du fichier 'memoire-technique.pdf' pour répondre parfaitement au règlement de consultation.
Pour rappel, Informations :
"{infos_dossier_consultation}"
et requis :
"{requis_dossier_consultation}"
""",
    "certifications": """Rédige la partie « Certifications Obtenues » du mémoire technique de la société {nom_entreprise}.
Pour cela, tu citeras la totalité des certifications obtenues à partir du fichier 'memoire-technique.pdf' pour répondre parfaitement au règlement de consultation.
Pour rappel, éléments requis :
"{requis_dossier_consultation}"
""",
    "respect_normes_securite": """Rédige la partie « Respect des Normes de Sécurité » du mémoire technique de la société {nom_entreprise}.
Pour cela, tu citeras la totalité des normes de sécurité à mettre en place pour répondre parfaitement au règlement de consultation.""",
    "respect_environnement": """Rédige la partie « Respect de l'Environnement » du mémoire technique de la société {nom_entreprise}.
Pour cela, tu citeras la totalité des normes et bonnes pratiques à mettre en place sur un chantier pour répondre parfaitement au règlement de consultation.""",
    "references_et_realisations_passees": """Rédige la partie « Références et Réalisations Passées » du mémoire technique.
Pour cela, tu citeras la totalité des références et réalisations passées de la société {nom_entreprise} obtenues à partir du fichier 'memoire-technique.pdf' pour répondre parfaitement au règlement de consultation.""",
    "partenariats_strategiques": """Rédige la partie « Partenariats Stratégiques » du mémoire technique.
Pour cela, tu citeras tous les partenariats de la société {nom_entreprise} obtenus à partir du fichier 'memoire-technique.pdf', puis tu complèteras avec la description de la politique de partenariat de la société pour répondre parfaitement au règlement de consultation.""",
    "temoignages": """Rédige la partie « Témoignages » du mémoire technique.
Pour cela, tu citeras la totalité des témoignages reçus par la société {nom_entreprise} obtenus à partir du fichier 'memoire-technique.pdf'. Tu présenteras les témoignages sous la forme de liste, avec le maximum d'informations à chaque fois : nom, prénom, société, chantier réalisé, témoignage... pour répondre parfaitement au règlement de consultation.""",
    "methode_gestion_projet": """Rédige la partie « Approche de Gestion de Projet » du mémoire technique de la société {nom_entreprise}. Pour cela, tu rédigeras une méthodologie de gestion de projet idéale.
Tu utiliseras les infos pertinentes récupérées à partir du fichier 'memoire-technique.pdf' pour répondre parfaitement au règlement de consultation.
Pour rappel, Informations :
"{infos_dossier_consultation}"
et requis :
"{requis_dossier_consultation}"
""",
    "planning": """Rédige la partie « Planning » du mémoire technique de la société {nom_entreprise}. Pour cela, tu rédigeras un planning complet et détaillé pour la réalisation de ce projet.
Tu utiliseras les infos pertinentes récupérées à partir du fichier 'memoire-technique.pdf' pour répondre parfaitement au règlement de consultation."""
}

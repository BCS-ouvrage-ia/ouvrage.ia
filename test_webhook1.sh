curl -X POST \
   https://ouvrage-ia-1.onrender.com/webhook-test/creer-nouveau-utilisateur \
  -H 'Content-Type: application/json' \
  -d '{
        "nom entreprise": "Entreprise XYZ",
        "prénom": "Jean",
        "nom": "Dupont",
        "email": "jean.dupont@example.com",
        "role": "Administrateur",
        "année création": "2000",
        "activité": "Informatique",
        "code NAF": "6201Z",
        "adresse": "123 Rue de la Paix",
        "ville": "Paris",
        "code postal": "75001",
        "effectif": "50",
        "numero_siren": "625 635 72",
        "chiffre_affaire": "5M"
      }'

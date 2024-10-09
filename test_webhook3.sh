curl -X POST \
   https://5011-2a02-842a-5d00-8601-cc62-a06f-8d43-2ea6.ngrok-free.app/webhook-test/generer_memoire_technique \
  -F "nom entreprise=Entreprise_XYZ" \
  -F "prénom=Jean" \
  -F "nom=Dupont" \
  -F "file=@docs_test/dossier-consultation.pdf"

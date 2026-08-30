#!/bin/bash
set -e

echo "Régénération du site..."
python scripts/generate_site.py

echo "Démarrage du serveur sur le port 8000..."
cd site && python -m http.server 8000

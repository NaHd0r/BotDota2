#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour mettre à jour le mapping des séries et des matchs
"""

import os
import json
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CACHE_DIR = "cache"
SERIES_MAPPING_FILE = os.path.join(CACHE_DIR, "series_matches_mapping.json")

def load_series_mapping():
    """Charge le fichier de mapping séries-matchs"""
    try:
        with open(SERIES_MAPPING_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.warning(f"Fichier de mapping non trouvé ou invalide, création d'un nouveau fichier")
        return {}

def save_series_mapping(mapping_data):
    """Sauvegarde le fichier de mapping séries-matchs"""
    with open(SERIES_MAPPING_FILE, 'w') as f:
        json.dump(mapping_data, f, indent=2)
    logger.info(f"Fichier de mapping séries-matchs mis à jour")

if __name__ == "__main__":
    # Charger le mapping existant
    mapping = load_series_mapping()
    
    # Ajouter le match 8258081694 à la série s_8258012658
    if "s_8258012658" in mapping:
        if "8258081694" not in mapping["s_8258012658"]:
            mapping["s_8258012658"].append("8258081694")
            logger.info(f"Match 8258081694 ajouté à la série s_8258012658")
        else:
            logger.info(f"Le match 8258081694 est déjà dans la série s_8258012658")
    else:
        mapping["s_8258012658"] = ["8258012658", "8258081694"]
        logger.info(f"Nouvelle série s_8258012658 créée avec les matchs 8258012658 et 8258081694")
    
    # Afficher le mapping mis à jour
    logger.info(f"Mapping mis à jour: {mapping}")
    
    # Sauvegarder le mapping
    save_series_mapping(mapping)
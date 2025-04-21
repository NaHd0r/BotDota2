#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour mettre à jour automatiquement le cache live avec les matchs terminés.
Ce script vérifie si des matchs sont terminés et les enrichit avec les données 
d'OpenDota pour maintenir l'affichage dans le frontend.
"""

import os
import json
import time
import logging
import sys
import requests
from datetime import datetime

# Import des modules locaux
from dota_service import parse_duration_to_seconds, format_duration
from enrich_live_match import enrich_match_in_live_cache

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fichiers de cache
CACHE_DIR = "cache"
LIVE_CACHE_FILE = os.path.join(CACHE_DIR, "live_series_cache.json")
MATCH_DATA_CACHE_FILE = os.path.join(CACHE_DIR, "match_data_cache.json")
COMPLETED_SERIES_CACHE_FILE = os.path.join(CACHE_DIR, "completed_series_cache.json")

def load_cache(file_path):
    """Charge un fichier de cache JSON"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du cache {file_path}: {str(e)}")
        return {}

def save_cache(file_path, data):
    """Sauvegarde un fichier de cache JSON"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache {file_path}: {str(e)}")
        return False

def check_recently_finished_matches():
    """
    Vérifie si des matchs ont été récemment terminés et les enrichit
    avec les données d'OpenDota.
    
    Returns:
        Liste des matchs enrichis
    """
    # Charger le cache live
    live_cache = load_cache(LIVE_CACHE_FILE)
    
    # Récupérer le timestamp actuel
    current_time = int(time.time())
    
    # Liste pour stocker les matchs enrichis
    enriched_matches = []
    
    # Vérifier chaque série dans le cache live
    for series_id, series_data in live_cache.items():
        # S'assurer que series_data['matches'] est un dictionnaire
        matches = series_data.get('matches')
        if not isinstance(matches, dict):
            logger.warning(f"Format de matches invalide pour la série {series_id}")
            continue
            
        # Vérifier chaque match dans la série
        for match_id, match_data in matches.items():
            # Vérifier si le match est terminé mais n'a pas été enrichi avec les données OpenDota
            if match_data.get('match_state', {}).get('phase') == 'finished':
                # Vérifier si les scores et la durée sont corrects
                if match_data.get('radiant_score', 0) == 0 and match_data.get('dire_score', 0) == 0:
                    logger.info(f"Match {match_id} terminé mais sans scores, enrichissement nécessaire")
                    if enrich_match_in_live_cache(match_id):
                        enriched_matches.append(match_id)
                # Ou si la durée est à 0:00
                elif match_data.get('duration') == "0:00":
                    logger.info(f"Match {match_id} terminé mais sans durée, enrichissement nécessaire")
                    if enrich_match_in_live_cache(match_id):
                        enriched_matches.append(match_id)
    
    return enriched_matches

if __name__ == "__main__":
    logger.info("Vérification des matchs récemment terminés...")
    enriched_matches = check_recently_finished_matches()
    
    if enriched_matches:
        logger.info(f"{len(enriched_matches)} match(s) enrichi(s) avec succès: {', '.join(enriched_matches)}")
    else:
        logger.info("Aucun match récemment terminé à enrichir.")
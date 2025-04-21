#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour corriger l'affichage du numéro de jeu dans les séries
en fonction des scores de série. En particulier, force l'affichage
de GAME 3 SUR 3 lorsque le score est 1-1 dans une série Best of 3.
"""

import os
import json
import logging
import time

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fichiers de cache
CACHE_DIR = "cache"
LIVE_CACHE_FILE = os.path.join(CACHE_DIR, "live_series_cache.json")

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

def fix_series_game_number():
    """
    Corrige le numéro de jeu dans les séries en direct.
    - Si le score est 1-1 dans un Bo3, force l'affichage de GAME 3
    - Si le score est 2-2 dans un Bo5, force l'affichage de GAME 5
    """
    # Charger le cache live
    live_cache = load_cache(LIVE_CACHE_FILE)
    changes_made = False
    
    # Vérifier chaque série dans le cache live
    for series_id, series_data in live_cache.items():
        # Récupérer le type de série (Bo3, Bo5, etc.)
        series_type = series_data.get('series_type', 0)
        
        # Récupérer les scores actuels
        radiant_score = series_data.get('radiant_score', 0)
        dire_score = series_data.get('dire_score', 0)
        
        # Si c'est un Bo3 et que le score est 1-1
        if series_type == 1 and radiant_score == 1 and dire_score == 1:
            # Force l'affichage de GAME 3
            logger.info(f"Correction de la série {series_id}: Score 1-1, forçage GAME 3")
            
            # Vérifier si un match en cours existe dans la série
            matches = series_data.get('matches', {})
            for match_id, match_data in matches.items():
                # Si un match est en cours (pas terminé)
                if match_data.get('match_state', {}).get('phase') != 'finished':
                    logger.info(f"Match en cours trouvé: {match_id}, correction du numéro de jeu")
                    # Forcer le numéro de jeu à 3
                    match_data['game_number'] = 3
                    match_data['game_display'] = "GAME 3 SUR 3"
                    
                    # S'assurer que les données de série stockées sont correctes
                    if 'series_info' not in match_data:
                        match_data['series_info'] = {}
                    
                    match_data['series_info']['radiant_series_wins'] = 1
                    match_data['series_info']['dire_series_wins'] = 1
                    match_data['series_info']['game_number'] = 3
                    
                    changes_made = True
                    
        # Si c'est un Bo5 et que le score est 2-2
        elif series_type == 2 and radiant_score == 2 and dire_score == 2:
            # Force l'affichage de GAME 5
            logger.info(f"Correction de la série {series_id}: Score 2-2, forçage GAME 5")
            
            # Vérifier si un match en cours existe dans la série
            matches = series_data.get('matches', {})
            for match_id, match_data in matches.items():
                # Si un match est en cours (pas terminé)
                if match_data.get('match_state', {}).get('phase') != 'finished':
                    logger.info(f"Match en cours trouvé: {match_id}, correction du numéro de jeu")
                    # Forcer le numéro de jeu à 5
                    match_data['game_number'] = 5
                    match_data['game_display'] = "GAME 5 SUR 5"
                    
                    # S'assurer que les données de série stockées sont correctes
                    if 'series_info' not in match_data:
                        match_data['series_info'] = {}
                    
                    match_data['series_info']['radiant_series_wins'] = 2
                    match_data['series_info']['dire_series_wins'] = 2
                    match_data['series_info']['game_number'] = 5
                    
                    changes_made = True
    
    # Sauvegarder le cache si des modifications ont été faites
    if changes_made:
        logger.info("Sauvegarde des modifications dans le cache live")
        save_cache(LIVE_CACHE_FILE, live_cache)
        return True
    else:
        logger.info("Aucune série à corriger")
        return False

if __name__ == "__main__":
    logger.info("Correction des numéros de jeu dans les séries en direct...")
    fixed = fix_series_game_number()
    
    if fixed:
        logger.info("Corrections appliquées avec succès")
    else:
        logger.info("Aucune correction nécessaire")
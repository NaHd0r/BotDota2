#!/usr/bin/env python
"""
Script pour nettoyer complètement les caches et recréer une entrée propre
pour la série 8257889151 avec toutes les informations nécessaires.
"""

import json
import os
import logging
import time

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
CACHE_DIR = 'cache'
COMPLETED_SERIES_CACHE = os.path.join(CACHE_DIR, 'completed_series_cache.json')
LIVE_SERIES_CACHE = os.path.join(CACHE_DIR, 'live_series_cache.json')
SERIES_CACHE = os.path.join(CACHE_DIR, 'series_cache.json')
SERIES_MAPPING = os.path.join(CACHE_DIR, 'series_matches_mapping.json')

# ID de la série et des matchs à corriger
SERIES_ID = "8257889151"
FIRST_MATCH_ID = "8257889151"
CURRENT_MATCH_ID = "8257938792"

def create_new_series_entry():
    """
    Crée une entrée propre pour la série 8257889151 dans tous les caches
    """
    # Données du premier match (terminé)
    first_match_data = {
        "match_id": FIRST_MATCH_ID,
        "radiant_team": {
            "team_id": "8969893",
            "name": "Hellspawn"
        },
        "dire_team": {
            "team_id": "9086888",
            "name": "Azure Dragons"
        },
        "radiant_score": 39,
        "dire_score": 33,
        "duration": "47:07",
        "total_kills": 72,
        "winner": "radiant",
        "start_time": 1744881923,
        "league_id": 17911,
        "match_phase": "finished",
        "game_number": 1,
        "timestamp": 1744881923
    }
    
    # Données du match en cours
    current_match_data = {
        "match_id": CURRENT_MATCH_ID,
        "radiant_team": {
            "team_id": "9086888",
            "name": "Azure Dragons"
        },
        "dire_team": {
            "team_id": "8969893",
            "name": "Hellspawn"
        },
        "radiant_score": 37,
        "dire_score": 26,
        "duration": "43:01",
        "total_kills": 63,
        "winner": None,
        "match_phase": "game",
        "start_time": int(time.time()) - 43*60,
        "league_id": 17911,
        "game_number": 2,
        "timestamp": int(time.time()) - 43*60
    }
    
    # Créer/réinitialiser le cache série principale
    series_cache = {}
    series_cache[SERIES_ID] = {
        "series_id": SERIES_ID,
        "radiant_team_id": "8969893",
        "dire_team_id": "9086888",
        "radiant_team_name": "Hellspawn",
        "dire_team_name": "Azure Dragons",
        "radiant_score": 1,  # Score actuel de la série (Hellspawn a gagné le premier match)
        "dire_score": 0,
        "previous_matches": [
            {
                "match_id": FIRST_MATCH_ID,
                "radiant_team_name": "Hellspawn",
                "dire_team_name": "Azure Dragons",
                "radiant_score": 39,
                "dire_score": 33,
                "duration": "47:07",
                "total_kills": 72,
                "game_number": 1,
                "winner": "radiant",
                "timestamp": 1744881923
            }
        ],
        "series_type": 1  # BO3
    }
    
    # Créer/réinitialiser le cache des séries en direct
    live_series_cache = {}
    live_series_cache[SERIES_ID] = {
        "series_id": SERIES_ID,
        "radiant_team_id": "8969893",
        "dire_team_id": "9086888",
        "radiant_team_name": "Hellspawn",
        "dire_team_name": "Azure Dragons",
        "radiant_score": 1,
        "dire_score": 0,
        "matches": [
            first_match_data,  # Premier match (terminé)
            current_match_data  # Match en cours
        ],
        "series_type": 1,  # BO3
        "completed": False
    }
    
    # Créer/réinitialiser le cache des séries complétées
    completed_series_cache = {}
    completed_series_cache[FIRST_MATCH_ID] = {
        "series_id": FIRST_MATCH_ID,
        "radiant_team_id": "8969893",
        "dire_team_id": "9086888",
        "radiant_team_name": "Hellspawn",
        "dire_team_name": "Azure Dragons",
        "radiant_score": 1,
        "dire_score": 0,
        "matches": [first_match_data],
        "series_type": 0,  # Marqué comme BO1 car c'est un match unique dans ce cache
        "completed": True,
        "completion_time": 1744881923 + 47*60
    }
    
    # Créer/réinitialiser le mapping des séries
    series_mapping = {}
    series_mapping[SERIES_ID] = {
        "series_id": SERIES_ID,
        "series_name": "Hellspawn vs Azure Dragons",
        "team1_name": "Hellspawn",
        "team2_name": "Azure Dragons",
        "matches": [
            {
                "game_number": 1,
                "match_id": FIRST_MATCH_ID
            },
            {
                "game_number": 2,
                "match_id": CURRENT_MATCH_ID
            }
        ],
        "league_id": "17911",
        "scrape_time": int(time.time())
    }
    
    # Sauvegarder tous les fichiers cache
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    with open(SERIES_CACHE, 'w') as f:
        json.dump(series_cache, f, indent=2)
    logger.info(f"Fichier {SERIES_CACHE} recréé avec succès")
    
    with open(LIVE_SERIES_CACHE, 'w') as f:
        json.dump(live_series_cache, f, indent=2)
    logger.info(f"Fichier {LIVE_SERIES_CACHE} recréé avec succès")
    
    with open(COMPLETED_SERIES_CACHE, 'w') as f:
        json.dump(completed_series_cache, f, indent=2)
    logger.info(f"Fichier {COMPLETED_SERIES_CACHE} recréé avec succès")
    
    with open(SERIES_MAPPING, 'w') as f:
        json.dump(series_mapping, f, indent=2)
    logger.info(f"Fichier {SERIES_MAPPING} recréé avec succès")
    
    return True

if __name__ == "__main__":
    logger.info("Démarrage de la réinitialisation des caches")
    
    # Supprimer l'ancien cache si nécessaire
    if os.path.exists(SERIES_CACHE):
        os.rename(SERIES_CACHE, f"{SERIES_CACHE}.bak")
        logger.info(f"Backup créé: {SERIES_CACHE}.bak")
        
    if os.path.exists(LIVE_SERIES_CACHE):
        os.rename(LIVE_SERIES_CACHE, f"{LIVE_SERIES_CACHE}.bak")
        logger.info(f"Backup créé: {LIVE_SERIES_CACHE}.bak")
        
    if os.path.exists(COMPLETED_SERIES_CACHE):
        os.rename(COMPLETED_SERIES_CACHE, f"{COMPLETED_SERIES_CACHE}.bak")
        logger.info(f"Backup créé: {COMPLETED_SERIES_CACHE}.bak")
        
    if os.path.exists(SERIES_MAPPING):
        os.rename(SERIES_MAPPING, f"{SERIES_MAPPING}.bak")
        logger.info(f"Backup créé: {SERIES_MAPPING}.bak")
    
    # Créer de nouveaux caches propres
    if create_new_series_entry():
        logger.info("Tous les caches ont été réinitialisés avec succès")
    else:
        logger.error("Erreur lors de la réinitialisation des caches")
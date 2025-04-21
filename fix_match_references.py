#!/usr/bin/env python3
"""
Script pour corriger les références entre les matchs d'une même série.
Ce script lie explicitement les trois matchs de la série entre Azure Dragons et Immortal Squad.
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes
CACHE_DIR = "cache"
LIVE_DATA_FILE = os.path.join(CACHE_DIR, "live_data.json")

# IDs des matchs de la série
MAIN_SERIES_ID = "s_8259450653"
MATCH_IDS = ["8259450653", "8259522321", "8259581999"]

def load_cache_file(file_path: str) -> Dict[str, Any]:
    """Charge un fichier de cache JSON"""
    if not os.path.exists(file_path):
        logger.error(f"Le fichier {file_path} n'existe pas")
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Erreur lors du chargement du cache {file_path}: {e}")
        return {}

def save_cache_file(file_path: str, data: Dict[str, Any]) -> bool:
    """Sauvegarde un fichier de cache JSON"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Cache sauvegardé dans {file_path}")
        return True
    except IOError as e:
        logger.error(f"Erreur lors de la sauvegarde du cache {file_path}: {e}")
        return False

def fix_series_match_links() -> bool:
    """Corrige les liens entre les matchs de la série spécifiée"""
    # Charger le cache
    cache_data = load_cache_file(LIVE_DATA_FILE)
    if not cache_data:
        return False
    
    # Vérifier si la série existe
    if MAIN_SERIES_ID not in cache_data.get("series", {}):
        logger.error(f"Série {MAIN_SERIES_ID} non trouvée dans le cache")
        return False
    
    # Récupérer la série
    series_data = cache_data["series"][MAIN_SERIES_ID]
    
    # Mettre à jour la liste des match_ids
    series_data["match_ids"] = MATCH_IDS
    logger.info(f"Série {MAIN_SERIES_ID} mise à jour avec les matchs: {', '.join(MATCH_IDS)}")
    
    # Mettre à jour chaque match pour pointer vers cette série
    for match_id in MATCH_IDS:
        if match_id not in cache_data.get("matches", {}):
            logger.warning(f"Match {match_id} non trouvé dans le cache")
            continue
        
        match_data = cache_data["matches"][match_id]
        
        # Mettre à jour le match_type pour pointer vers la série principale
        if "match_type" not in match_data:
            match_data["match_type"] = {}
        
        match_data["match_type"]["series_id"] = MAIN_SERIES_ID
        cache_data["matches"][match_id] = match_data
        logger.info(f"Match {match_id} mis à jour pour pointer vers la série {MAIN_SERIES_ID}")
    
    # Reconstruire la liste des previous_matches avec les données des matchs
    previous_matches = []
    for i, match_id in enumerate(MATCH_IDS, 1):
        match_data = cache_data["matches"].get(match_id)
        if not match_data:
            continue
        
        # Construire l'entrée pour previous_matches
        previous_match = {
            "match_id": match_id,
            "radiant_team_name": match_data.get("radiant_team_name"),
            "dire_team_name": match_data.get("dire_team_name"),
            "radiant_score": match_data.get("radiant_score", 0),
            "dire_score": match_data.get("dire_score", 0),
            "duration": match_data.get("duration", "00:00"),
            "total_kills": match_data.get("radiant_score", 0) + match_data.get("dire_score", 0),
            "game_number": i,
            "winner": match_data.get("winner"),
            "timestamp": match_data.get("start_time", int(time.time()))
        }
        previous_matches.append(previous_match)
    
    # Mettre à jour la série avec les matchs précédents
    series_data["previous_matches"] = previous_matches
    cache_data["series"][MAIN_SERIES_ID] = series_data
    
    # Sauvegarder le cache mis à jour
    if save_cache_file(LIVE_DATA_FILE, cache_data):
        logger.info(f"Série {MAIN_SERIES_ID} mise à jour avec {len(previous_matches)} matchs précédents")
        return True
    
    return False

def main() -> None:
    """Fonction principale"""
    print("Script de correction des références entre matchs d'une série")
    print("========================================================")
    
    if fix_series_match_links():
        print(f"Série {MAIN_SERIES_ID} mise à jour avec succès")
    else:
        print(f"Échec de la mise à jour de la série {MAIN_SERIES_ID}")
    
    print("\nMise à jour terminée. Veuillez rafraîchir l'interface pour voir les changements.")

if __name__ == "__main__":
    main()
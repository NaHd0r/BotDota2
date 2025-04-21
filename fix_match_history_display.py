#!/usr/bin/env python3
"""
Script pour corriger l'affichage de l'historique des matchs d'une série.

Ce script va vérifier que tous les matchs d'une série sont bien disponibles dans
l'API /match-history avec les bonnes informations et les bons game_number.
"""

import logging
import json
import time
import os
from typing import Dict, List, Any, Optional

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
CACHE_DIR = "cache"
LIVE_DATA_FILE = os.path.join(CACHE_DIR, "live_data.json")

# Série et matchs à corriger (config manuelle)
SERIES_ID = "s_8259450653"  # Série à corriger
MATCH_IDS = ["8259450653", "8259522321", "8259581999"]  # IDs des matchs dans l'ordre

def load_cache(file_path: str) -> Dict[str, Any]:
    """Charge le cache JSON depuis un fichier"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"matches": {}, "series": {}}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du cache {file_path}: {e}")
        return {"matches": {}, "series": {}}

def save_cache(file_path: str, data: Dict[str, Any]) -> bool:
    """Sauvegarde le cache JSON dans un fichier"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Cache sauvegardé dans {file_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache {file_path}: {e}")
        return False

def fix_match_history_display():
    """
    Corrige l'affichage de l'historique des matchs pour une série donnée.
    
    Cette fonction s'assure que tous les matchs d'une série sont correctement
    liés et affichés dans l'API /match-history.
    """
    # Charger le cache live
    cache_data = load_cache(LIVE_DATA_FILE)
    if not cache_data:
        logger.error("Le cache est vide")
        return False
    
    # Vérifier si la série existe
    if "series" not in cache_data or SERIES_ID not in cache_data["series"]:
        logger.error(f"La série {SERIES_ID} n'existe pas dans le cache")
        return False
    
    # Récupérer les données de la série
    series_data = cache_data["series"][SERIES_ID]
    
    # S'assurer que les match_ids sont à jour et dans le bon ordre
    series_data["match_ids"] = MATCH_IDS.copy()
    logger.info(f"Match IDs mis à jour pour la série {SERIES_ID}: {', '.join(MATCH_IDS)}")
    
    # Vérifier si le champ previous_matches existe et contient tous les matchs
    if "previous_matches" not in series_data or len(series_data["previous_matches"]) < len(MATCH_IDS):
        # Initialiser ou réinitialiser le champ previous_matches
        series_data["previous_matches"] = []
        
        # Pour chaque match de la série, créer une entrée dans previous_matches
        for i, match_id in enumerate(MATCH_IDS, 1):
            match_data = None
            
            # Chercher d'abord dans les matchs du cache
            if "matches" in cache_data and match_id in cache_data["matches"]:
                match_data = cache_data["matches"][match_id]
                logger.info(f"Match {match_id} trouvé dans le cache")
            
            # Si le match n'est pas trouvé ou manque des données essentielles, créer une entrée minimale
            if not match_data:
                logger.warning(f"Match {match_id} non trouvé dans le cache, création d'une entrée minimale")
                match_data = {
                    "match_id": match_id,
                    "radiant_score": 0,
                    "dire_score": 0,
                    "duration": "0:00",
                    "start_time": int(time.time()),
                    "radiant_team": {"team_name": "Équipe Radiant"},
                    "dire_team": {"team_name": "Équipe Dire"}
                }
            
            # Créer l'entrée pour previous_matches
            previous_match = {
                "match_id": match_id,
                "radiant_team_name": match_data.get("radiant_team", {}).get("team_name", "Équipe Radiant"),
                "dire_team_name": match_data.get("dire_team", {}).get("team_name", "Équipe Dire"),
                "radiant_score": match_data.get("radiant_score", 0),
                "dire_score": match_data.get("dire_score", 0),
                "duration": match_data.get("duration", "0:00"),
                "total_kills": match_data.get("radiant_score", 0) + match_data.get("dire_score", 0),
                "game_number": i,
                "winner": match_data.get("winner"),
                "timestamp": match_data.get("start_time", int(time.time()))
            }
            
            series_data["previous_matches"].append(previous_match)
            logger.info(f"Match {match_id} (game {i}) ajouté à previous_matches")
    
    # Mettre à jour les game_number pour s'assurer qu'ils sont cohérents
    for i, match in enumerate(series_data["previous_matches"], 1):
        match["game_number"] = i
    
    # S'assurer que les matchs sont triés par game_number
    series_data["previous_matches"].sort(key=lambda x: x["game_number"])
    
    # Mettre à jour les données de la série dans le cache
    cache_data["series"][SERIES_ID] = series_data
    
    # Sauvegarder le cache
    return save_cache(LIVE_DATA_FILE, cache_data)

def main():
    """Fonction principale"""
    print("===== Correction de l'affichage de l'historique des matchs =====")
    print(f"Série: {SERIES_ID}")
    print(f"Matchs: {', '.join(MATCH_IDS)}")
    
    if fix_match_history_display():
        print("Correction terminée avec succès!")
    else:
        print("Échec de la correction!")
    
    print("\nVérifiez l'API /match-history pour voir les matchs corrigés.")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script pour associer manuellement le match 8260477281 à la série s_8260525679
et le créer dans le cache LIVE s'il n'existe pas déjà
"""

import json
import logging
import os
from typing import Dict, Any

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
CACHE_DIR = "./cache"
LIVE_SERIES_CACHE = os.path.join(CACHE_DIR, "live_series_cache.json")
LIVE_DATA_CACHE = os.path.join(CACHE_DIR, "live_data.json")

def load_cache(file_path: str) -> Dict[str, Any]:
    """Charge un fichier de cache JSON"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Erreur lors du chargement du cache {file_path}: {e}")
        return {}

def save_cache(file_path: str, cache_data: Dict[str, Any]) -> bool:
    """Sauvegarde un fichier de cache JSON"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Cache sauvegardé: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache {file_path}: {e}")
        return False

def switch_series_manually():
    """
    Change manuellement l'ID de série du match 8260477281 de s_8260477281 à s_8260525679
    et le crée dans le cache LIVE s'il n'existe pas déjà
    """
    # Paramètres
    match_id = "8260477281"
    old_series_id = "s_8260477281"
    new_series_id = "s_8260525679"
    
    # 1. Mettre à jour le cache des séries
    series_cache = load_cache(LIVE_SERIES_CACHE)
    
    # Vérifier que la série existe
    if "series" not in series_cache:
        logger.error("Le cache des séries n'a pas d'entrée 'series'")
        return False
    
    if old_series_id not in series_cache["series"]:
        logger.warning(f"La série {old_series_id} n'existe plus dans le cache")
    else:
        # Retirer le match de l'ancienne série
        if match_id in series_cache["series"][old_series_id]["match_ids"]:
            series_cache["series"][old_series_id]["match_ids"].remove(match_id)
            logger.info(f"Match {match_id} retiré de la série {old_series_id}")
        
        # Si l'ancienne série est vide, la supprimer
        if len(series_cache["series"][old_series_id]["match_ids"]) == 0:
            del series_cache["series"][old_series_id]
            logger.info(f"Série vide {old_series_id} supprimée")
    
    if new_series_id not in series_cache["series"]:
        logger.error(f"La série {new_series_id} n'existe pas dans le cache")
        return False
    
    # Ajouter le match à la nouvelle série
    if match_id not in series_cache["series"][new_series_id]["match_ids"]:
        series_cache["series"][new_series_id]["match_ids"].append(match_id)
        logger.info(f"Match {match_id} ajouté à la série {new_series_id}")
    
    # Sauvegarder le cache des séries
    if not save_cache(LIVE_SERIES_CACHE, series_cache):
        logger.error("Erreur lors de la sauvegarde du cache des séries")
        return False
    
    # 2. Mettre à jour le cache des données live
    live_data = load_cache(LIVE_DATA_CACHE)
    
    # S'assurer que le dictionnaire matches existe
    if "matches" not in live_data:
        live_data["matches"] = {}
    
    # Créer ou mettre à jour le match dans le cache live
    if match_id not in live_data["matches"]:
        # Créer une entrée basique pour le match
        live_data["matches"][match_id] = {
            "match_id": match_id,
            "series_id": new_series_id,
            "radiant_team": {
                "team_id": series_cache["series"][new_series_id].get("radiant_team_id", "unknown"),
                "team_name": series_cache["series"][new_series_id].get("radiant_team_name", "Équipe Radiant")
            },
            "dire_team": {
                "team_id": series_cache["series"][new_series_id].get("dire_team_id", "unknown"),
                "team_name": series_cache["series"][new_series_id].get("dire_team_name", "Équipe Dire")
            },
            "match_type": {
                "series_id": new_series_id,
                "series_type": series_cache["series"][new_series_id].get("series_type", 1)
            },
            "state": "finished",
            "radiant_score": 0,
            "dire_score": 0,
            "duration": "00:00"
        }
        logger.info(f"Match {match_id} créé dans le cache live avec série {new_series_id}")
    else:
        # Mettre à jour l'ID de série du match existant
        live_data["matches"][match_id]["series_id"] = new_series_id
        if "match_type" in live_data["matches"][match_id]:
            live_data["matches"][match_id]["match_type"]["series_id"] = new_series_id
        logger.info(f"Match {match_id} mis à jour dans le cache live avec série {new_series_id}")
    
    # Sauvegarder les modifications du cache live
    if not save_cache(LIVE_DATA_CACHE, live_data):
        logger.error("Erreur lors de la sauvegarde du cache live")
        return False
    
    logger.info(f"Opération terminée avec succès pour le match {match_id} et la série {new_series_id}")
    return True

if __name__ == "__main__":
    if switch_series_manually():
        print("Changement de série réussi!")
    else:
        print("Échec du changement de série.")
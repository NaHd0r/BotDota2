"""
Script pour forcer l'état d'un match spécifique dans les caches.
Utilisé pour corriger manuellement le statut d'un match.
"""

import json
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chemin des fichiers de cache
LIVE_CACHE = "./cache/live_data.json"
SERIES_CACHE = "./cache/live_series_cache.json"
HISTORY_CACHE = "./cache/historical_data.json"

def load_cache(file_path):
    """Charge un fichier de cache JSON"""
    try:
        if not os.path.exists(file_path):
            logger.warning(f"Le fichier {file_path} n'existe pas.")
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Cache {file_path} chargé avec succès.")
        return data
    except Exception as e:
        logger.error(f"Erreur lors du chargement du cache {file_path}: {e}")
        return {}

def save_cache(file_path, data):
    """Sauvegarde un fichier de cache JSON"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Cache {file_path} sauvegardé avec succès.")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache {file_path}: {e}")
        return False

def force_match_state(match_id, new_state="finished", winner="dire"):
    """
    Force l'état d'un match spécifique dans tous les caches.
    
    Args:
        match_id (str): ID du match à modifier
        new_state (str): Nouvel état à définir ("draft", "game" ou "finished")
        winner (str): Vainqueur si l'état est "finished" ("radiant" ou "dire")
    """
    match_id = str(match_id)  # Assure que l'ID est une chaîne
    changes_made = False
    
    # Mettre à jour dans live_data.json si présent
    live_data = load_cache(LIVE_CACHE)
    if match_id in live_data:
        logger.info(f"Match {match_id} trouvé dans le cache live_data.json")
        live_data[match_id]["status"] = new_state
        if new_state == "finished":
            live_data[match_id]["winner"] = winner
        save_cache(LIVE_CACHE, live_data)
        changes_made = True
    
    # Mettre à jour dans live_series_cache.json si présent
    series_data = load_cache(SERIES_CACHE)
    updated_in_series = False
    
    # Structure spéciale avec un niveau supplémentaire "series"
    if "series" in series_data and isinstance(series_data["series"], dict):
        logger.info("Format de cache avec niveau 'series' détecté")
        series_dict = series_data["series"]
    else:
        logger.info("Format de cache standard détecté")
        series_dict = series_data
    
    # Vérifier dans les matchs actuels des séries
    for series_id, series_info in series_dict.items():
        if isinstance(series_info, dict) and match_id == str(series_info.get("match_id", "")):
            logger.info(f"Match {match_id} trouvé comme match actuel dans la série {series_id}")
            series_info["status"] = new_state
            if new_state == "finished":
                series_info["winner"] = winner
            updated_in_series = True
        
        # Vérifier dans les matchs précédents
        if isinstance(series_info, dict) and "previous_matches" in series_info:
            for prev_match in series_info["previous_matches"]:
                if isinstance(prev_match, dict) and str(prev_match.get("match_id", "")) == match_id:
                    logger.info(f"Match {match_id} trouvé dans les matchs précédents de la série {series_id}")
                    prev_match["status"] = new_state
                    if new_state == "finished":
                        prev_match["winner"] = winner
                    updated_in_series = True
    
    if updated_in_series:
        save_cache(SERIES_CACHE, series_data)
        changes_made = True
    
    # Mettre à jour dans historical_data.json si présent
    historical_data = load_cache(HISTORY_CACHE)
    if match_id in historical_data and isinstance(historical_data[match_id], dict):
        logger.info(f"Match {match_id} trouvé dans le cache historical_data.json")
        historical_data[match_id]["status"] = new_state
        if new_state == "finished":
            historical_data[match_id]["winner"] = winner
        save_cache(HISTORY_CACHE, historical_data)
        changes_made = True
    
    if changes_made:
        logger.info(f"Match {match_id} mis à jour avec succès: état={new_state}, vainqueur={winner if new_state=='finished' else 'N/A'}")
    else:
        logger.warning(f"Match {match_id} non trouvé dans aucun cache. Aucune modification effectuée.")

if __name__ == "__main__":
    # Forcer l'état du match 8261232219 à "finished" avec "dire" comme vainqueur
    force_match_state("8261232219", new_state="finished", winner="dire")
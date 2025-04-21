#!/usr/bin/env python3
"""
Script pour standardiser toutes les valeurs de status et status_tag dans les caches
en utilisant uniquement les formes minuscules simples (draft, game, finished)
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
HISTORICAL_DATA_CACHE = os.path.join(CACHE_DIR, "historical_data.json")

# Map de standardisation
STATUS_MAP = {
    "DRAFT": "draft",
    "draft": "draft",
    "pregame": "draft",
    
    "EN JEU": "game",
    "live": "game",
    "game": "game",
    "IN GAME": "game",
    
    "TERMINÉ": "finished",
    "FINISHED": "finished",
    "finished": "finished",
    "TERMINE": "finished",
    "postgame": "finished",
    "après-match": "finished"
}

def load_cache(file_path: str) -> Dict[str, Any]:
    """Charge un fichier de cache JSON"""
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
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

def standardize_match_status(match_data: Dict[str, Any]) -> bool:
    """
    Standardise les valeurs de status et status_tag dans un match
    
    Args:
        match_data (dict): Données du match à standardiser
        
    Returns:
        bool: True si des modifications ont été effectuées, False sinon
    """
    modified = False
    
    # Standardiser le champ status
    if 'status' in match_data:
        current_status = match_data['status']
        if current_status in STATUS_MAP:
            new_status = STATUS_MAP[current_status]
            if current_status != new_status:
                match_data['status'] = new_status
                modified = True
                logger.info(f"Status modifié: '{current_status}' -> '{new_status}'")
    
    # Standardiser le champ status_tag
    if 'status_tag' in match_data:
        current_tag = match_data['status_tag']
        if current_tag in STATUS_MAP:
            new_tag = STATUS_MAP[current_tag]
            if current_tag != new_tag:
                match_data['status_tag'] = new_tag
                modified = True
                logger.info(f"Status tag modifié: '{current_tag}' -> '{new_tag}'")
    
    return modified

def process_previous_matches(series_data):
    """
    Traite les matchs précédents dans une série
    """
    modified = False
    
    if "previous_matches" in series_data:
        for match in series_data["previous_matches"]:
            if standardize_match_status(match):
                modified = True
    
    return modified

def standardize_live_cache():
    """
    Standardise les statuts dans le cache des matchs en direct
    """
    live_cache = load_cache(LIVE_SERIES_CACHE)
    if not live_cache:
        return False
    
    modified = False
    
    # Parcourir les séries et leurs matchs
    if "series" in live_cache:
        for series_id, series_data in live_cache["series"].items():
            if process_previous_matches(series_data):
                modified = True
    
    # Parcourir les matchs indépendants
    if "matches" in live_cache:
        for match_id, match_data in live_cache["matches"].items():
            if standardize_match_status(match_data):
                modified = True
    
    if modified:
        save_cache(LIVE_SERIES_CACHE, live_cache)
        logger.info("Cache des séries en direct mis à jour avec des statuts standardisés")
    
    return modified

def standardize_live_data_cache():
    """
    Standardise les statuts dans le cache des données en direct
    """
    live_data = load_cache(LIVE_DATA_CACHE)
    if not live_data:
        return False
    
    modified = False
    
    # Parcourir les matchs
    if "matches" in live_data:
        for match_id, match_data in live_data["matches"].items():
            if standardize_match_status(match_data):
                modified = True
    
    if modified:
        save_cache(LIVE_DATA_CACHE, live_data)
        logger.info("Cache des données en direct mis à jour avec des statuts standardisés")
    
    return modified

def standardize_historical_data():
    """
    Standardise les statuts dans les données historiques
    """
    historical_data = load_cache(HISTORICAL_DATA_CACHE)
    if not historical_data:
        return False
    
    modified = False
    
    # Parcourir les matchs historiques
    if "matches" in historical_data:
        for match_id, match_data in historical_data["matches"].items():
            if standardize_match_status(match_data):
                modified = True
            
            # Vérifier les données imbriquées si présentes
            if "data" in match_data and isinstance(match_data["data"], dict):
                if standardize_match_status(match_data["data"]):
                    modified = True
    
    if modified:
        save_cache(HISTORICAL_DATA_CACHE, historical_data)
        logger.info("Cache des données historiques mis à jour avec des statuts standardisés")
    
    return modified

if __name__ == "__main__":
    logger.info("Début de la standardisation des valeurs de statut")
    
    live_cache_modified = standardize_live_cache()
    live_data_modified = standardize_live_data_cache()
    historical_data_modified = standardize_historical_data()
    
    if live_cache_modified or live_data_modified or historical_data_modified:
        logger.info("Standardisation terminée avec des modifications")
        print("Standardisation des statuts terminée avec succès !")
    else:
        logger.info("Standardisation terminée sans modifications")
        print("Standardisation terminée, aucune modification nécessaire.")
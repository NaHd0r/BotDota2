#!/usr/bin/env python
"""
Script pour standardiser la structure des caches et corriger les problèmes
de nommage et de structure dans les différents fichiers de cache.

Ce script analyse les fichiers de cache actuels, harmonise les noms de champs
et restructure les données pour assurer la cohérence entre tous les caches.
"""

import json
import os
import logging
import time
from typing import Dict, Any, List, Optional, Union

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

# Mapping de normalisation des champs
# Clé: nom de champ original, Valeur: nom de champ standardisé
FIELD_MAPPING = {
    # Champs de l'entité série
    "radiant_id": "radiant_team_id",
    "dire_id": "dire_team_id",
    
    # Champs de la durée
    "duration_formatted": "duration",
    
    # Champs d'état du match
    "draft_phase": "match_phase",
    
    # Équipes (pour champs plats)
    "radiant_team_id": "radiant_team_id",
    "dire_team_id": "dire_team_id",
    
    # Équipes (pour structures imbriquées)
    "radiant_team": {
        "team_id": "radiant_team_id",
        "name": "radiant_team_name"
    },
    "dire_team": {
        "team_id": "dire_team_id",
        "name": "dire_team_name"
    }
}

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Charge un fichier JSON"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du fichier {filepath}: {e}")
        return {}

def save_json_file(filepath: str, data: Dict[str, Any]) -> bool:
    """Sauvegarde des données dans un fichier JSON"""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Fichier {filepath} sauvegardé avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du fichier {filepath}: {e}")
        return False

def normalize_field_name(original_name: str) -> str:
    """Normalise un nom de champ en utilisant le mapping"""
    return FIELD_MAPPING.get(original_name, original_name)

def normalize_series_entry(series_data: Dict[str, Any], is_completed: bool = False) -> Dict[str, Any]:
    """Normalise une entrée de série dans le cache"""
    normalized = {}
    
    # Normaliser les champs au niveau de la série
    for key, value in series_data.items():
        # Traiter les champs d'équipe spéciaux
        if key == "radiant_id":
            normalized["radiant_team_id"] = value
        elif key == "dire_id":
            normalized["dire_team_id"] = value
        # Ignorer les structures imbriquées pour le moment
        elif isinstance(value, dict) or isinstance(value, list):
            normalized[key] = value
        else:
            normalized_key = normalize_field_name(key)
            normalized[normalized_key] = value
    
    # Assurer la cohérence de l'état de complétion
    if is_completed:
        normalized["completed"] = True
        if "completion_time" not in normalized:
            normalized["completion_time"] = int(time.time())
    else:
        if "completed" not in normalized:
            normalized["completed"] = False
    
    # Assurer la cohérence du type de série
    if "series_type" not in normalized:
        normalized["series_type"] = 1  # Par défaut BO3
    
    return normalized

def normalize_match_data(match_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise les données d'un match"""
    normalized = {}
    
    # Normaliser les champs standards
    for key, value in match_data.items():
        # Traiter les structures imbriquées spéciales
        if key == "radiant_team" and isinstance(value, dict):
            if "team_id" in value:
                normalized["radiant_team_id"] = value["team_id"]
            if "name" in value:
                normalized["radiant_team_name"] = value["name"]
            # Garder aussi la structure originale
            normalized[key] = value
        elif key == "dire_team" and isinstance(value, dict):
            if "team_id" in value:
                normalized["dire_team_id"] = value["team_id"]
            if "name" in value:
                normalized["dire_team_name"] = value["name"]
            # Garder aussi la structure originale
            normalized[key] = value
        # Normaliser les champs de durée
        elif key == "duration":
            # Si c'est un nombre, c'est en secondes
            if isinstance(value, (int, float)):
                normalized["duration_seconds"] = value
                minutes = int(value // 60)
                seconds = int(value % 60)
                normalized["duration"] = f"{minutes:02d}:{seconds:02d}"
            else:
                normalized["duration"] = value
        # Normaliser les champs d'état du match
        elif key == "draft_phase":
            if value:
                normalized["match_phase"] = "draft"
            else:
                normalized["match_phase"] = "game"
        elif key == "match_outcome":
            if value == 0:
                # Pas encore déterminé
                if "match_phase" not in normalized:
                    normalized["match_phase"] = "game"
            elif value == 2:  # Radiant win
                normalized["match_phase"] = "finished"
                normalized["winner"] = "radiant"
            elif value == 3:  # Dire win
                normalized["match_phase"] = "finished"
                normalized["winner"] = "dire"
            # Garder aussi la valeur originale
            normalized[key] = value
        else:
            # Copier directement les autres champs
            normalized[key] = value
    
    # S'assurer que les champs critiques existent
    if "match_id" not in normalized:
        logger.warning("Match sans ID trouvé, ajout d'un ID généré")
        normalized["match_id"] = f"gen_{int(time.time())}"
    
    if "start_time" not in normalized and "timestamp" in normalized:
        normalized["start_time"] = normalized["timestamp"]
    elif "start_time" not in normalized:
        normalized["start_time"] = int(time.time())
    
    if "total_kills" not in normalized and "radiant_score" in normalized and "dire_score" in normalized:
        normalized["total_kills"] = normalized["radiant_score"] + normalized["dire_score"]
    
    return normalized

def normalize_previous_match_data(match_data: Dict[str, Any], game_number: int = 1) -> Dict[str, Any]:
    """Normalise les données d'un match précédent (pour series_cache)"""
    normalized = {
        "match_id": match_data.get("match_id"),
        "radiant_team_name": match_data.get("radiant_team_name"),
        "dire_team_name": match_data.get("dire_team_name"),
        "radiant_score": match_data.get("radiant_score", 0),
        "dire_score": match_data.get("dire_score", 0),
        "duration": match_data.get("duration", "00:00"),
        "total_kills": match_data.get("radiant_score", 0) + match_data.get("dire_score", 0),
        "game_number": game_number,
        "winner": match_data.get("winner"),
        "timestamp": match_data.get("start_time", match_data.get("timestamp", int(time.time())))
    }
    return normalized

def update_live_series_cache() -> None:
    """Met à jour le cache des séries en direct avec des champs standardisés"""
    live_cache = load_json_file(LIVE_SERIES_CACHE)
    updated_cache = {}
    
    for series_id, series_data in live_cache.items():
        # Normaliser l'entrée de la série
        normalized_series = normalize_series_entry(series_data, is_completed=series_data.get("completed", False))
        
        # Normaliser les matchs
        if "matches" in normalized_series:
            normalized_matches = []
            for match_data in normalized_series["matches"]:
                normalized_match = normalize_match_data(match_data)
                normalized_matches.append(normalized_match)
            normalized_series["matches"] = normalized_matches
        
        # Ajouter la série mise à jour au cache
        updated_cache[series_id] = normalized_series
    
    # Sauvegarder le cache mis à jour
    if save_json_file(LIVE_SERIES_CACHE, updated_cache):
        logger.info(f"Cache des séries en direct mis à jour avec succès ({len(updated_cache)} séries)")
    else:
        logger.error("Échec de la mise à jour du cache des séries en direct")

def update_completed_series_cache() -> None:
    """Met à jour le cache des séries complétées avec des champs standardisés"""
    completed_cache = load_json_file(COMPLETED_SERIES_CACHE)
    updated_cache = {}
    
    for series_id, series_data in completed_cache.items():
        # Normaliser l'entrée de la série (toujours complétée)
        normalized_series = normalize_series_entry(series_data, is_completed=True)
        
        # Normaliser les matchs
        if "matches" in normalized_series:
            normalized_matches = []
            for match_data in normalized_series["matches"]:
                normalized_match = normalize_match_data(match_data)
                normalized_matches.append(normalized_match)
            normalized_series["matches"] = normalized_matches
        
        # Ajouter la série mise à jour au cache
        updated_cache[series_id] = normalized_series
    
    # Sauvegarder le cache mis à jour
    if save_json_file(COMPLETED_SERIES_CACHE, updated_cache):
        logger.info(f"Cache des séries complétées mis à jour avec succès ({len(updated_cache)} séries)")
    else:
        logger.error("Échec de la mise à jour du cache des séries complétées")

def update_series_cache() -> None:
    """Met à jour le cache principal des séries avec des champs standardisés"""
    series_cache = load_json_file(SERIES_CACHE)
    updated_cache = {}
    
    for series_id, series_data in series_cache.items():
        # Normaliser l'entrée de la série
        normalized_series = normalize_series_entry(series_data)
        
        # Normaliser les matchs précédents
        if "previous_matches" in normalized_series:
            normalized_prev_matches = []
            for i, match_data in enumerate(normalized_series["previous_matches"]):
                normalized_match = normalize_previous_match_data(match_data, game_number=i+1)
                normalized_prev_matches.append(normalized_match)
            normalized_series["previous_matches"] = normalized_prev_matches
        
        # Ajouter la série mise à jour au cache
        updated_cache[series_id] = normalized_series
    
    # Sauvegarder le cache mis à jour
    if save_json_file(SERIES_CACHE, updated_cache):
        logger.info(f"Cache principal des séries mis à jour avec succès ({len(updated_cache)} séries)")
    else:
        logger.error("Échec de la mise à jour du cache principal des séries")

def main():
    """Fonction principale pour la mise à jour de tous les caches"""
    logger.info("Démarrage de la mise à jour de la structure des caches")
    
    # Mise à jour du cache des séries en direct
    update_live_series_cache()
    
    # Mise à jour du cache des séries complétées
    update_completed_series_cache()
    
    # Mise à jour du cache principal des séries
    update_series_cache()
    
    logger.info("Mise à jour de la structure des caches terminée")

if __name__ == "__main__":
    main()
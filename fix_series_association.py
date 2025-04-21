#!/usr/bin/env python3
"""
Correction de l'association entre matchs et séries

Ce script corrige les problèmes d'association entre matchs et séries en:
1. Identifiant les matchs qui appartiennent à la même série mais ont des IDs de série différents
2. Fusionnant ces séries pour maintenir un ID cohérent
3. Mettant à jour tous les caches pertinents
"""

import json
import logging
import os
import time
from typing import Dict, List, Any, Set, Tuple

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
CACHE_DIR = "./cache"
LIVE_SERIES_CACHE = os.path.join(CACHE_DIR, "live_series_cache.json")
SERIES_MAPPING_CACHE = os.path.join(CACHE_DIR, "series_matches_mapping.json")
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

def identify_series_by_teams() -> Dict[str, List[str]]:
    """
    Identifie les séries qui impliquent les mêmes équipes
    
    Returns:
        Dict où les clés sont des identifiants uniques de paires d'équipes 
        et les valeurs sont des listes d'IDs de série
    """
    live_data = load_cache(LIVE_DATA_CACHE)
    matches = live_data.get("matches", {})
    
    # Dictionnaire pour stocker les équipes par ID de série
    series_teams = {}
    # Dictionnaire pour grouper les séries par équipes
    teams_to_series = {}
    
    # Extraire les équipes pour chaque série
    for match_id, match_data in matches.items():
        series_id = match_data.get("series_id")
        if not series_id:
            continue
        
        # Obtenir les IDs d'équipe
        radiant_team_id = match_data.get("radiant_team", {}).get("team_id")
        dire_team_id = match_data.get("dire_team", {}).get("team_id")
        
        if not radiant_team_id or not dire_team_id:
            continue
            
        # Créer une clé de paire d'équipes (toujours dans le même ordre pour cohérence)
        teams_key = f"{min(radiant_team_id, dire_team_id)}_{max(radiant_team_id, dire_team_id)}"
        
        # Stocker l'association série -> équipes
        series_teams[series_id] = (radiant_team_id, dire_team_id)
        
        # Grouper les séries par paires d'équipes
        if teams_key not in teams_to_series:
            teams_to_series[teams_key] = []
        if series_id not in teams_to_series[teams_key]:
            teams_to_series[teams_key].append(series_id)
    
    # Filtrer pour ne garder que les paires d'équipes avec plusieurs séries
    return {k: v for k, v in teams_to_series.items() if len(v) > 1}

def merge_series(series_groups: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Fusionne les séries qui impliquent les mêmes équipes
    
    Args:
        series_groups: Dictionnaire où les clés sont des identifiants uniques de paires d'équipes 
                      et les valeurs sont des listes d'IDs de série
    
    Returns:
        Dictionnaire mappant les anciens IDs de série aux nouveaux
    """
    series_mapping = {}
    
    for teams_key, series_ids in series_groups.items():
        if not series_ids:
            continue
            
        # Trier les séries par ID (pour prendre toujours la plus ancienne)
        # Assumer que les IDs sont de la forme s_XXXXXXXX où XXXXXXXX est un nombre
        sorted_series_ids = sorted(series_ids, key=lambda x: int(x.replace("s_", "")))
        
        # Le premier ID de série devient l'ID principal
        primary_series_id = sorted_series_ids[0]
        
        logger.info(f"Fusion des séries pour les équipes {teams_key}:")
        logger.info(f"  - Série principale: {primary_series_id}")
        
        # Créer le mapping pour les autres séries
        for secondary_series_id in sorted_series_ids[1:]:
            series_mapping[secondary_series_id] = primary_series_id
            logger.info(f"  - Série fusionnée: {secondary_series_id} -> {primary_series_id}")
    
    return series_mapping

def update_live_series_cache(series_mapping: Dict[str, str]) -> bool:
    """
    Met à jour le cache des séries en direct
    
    Args:
        series_mapping: Dictionnaire mappant les anciens IDs de série aux nouveaux
    
    Returns:
        True si la mise à jour a réussi, False sinon
    """
    live_series_cache = load_cache(LIVE_SERIES_CACHE)
    
    # Mise à jour du cache des séries
    series_data = live_series_cache.get("series", {})
    modified = False
    
    for old_series_id, new_series_id in series_mapping.items():
        if old_series_id in series_data:
            # Récupérer les données de l'ancienne série
            old_series = series_data.get(old_series_id, {})
            
            # Récupérer ou créer la nouvelle série
            if new_series_id not in series_data:
                series_data[new_series_id] = {
                    "series_id": new_series_id,
                    "match_ids": [],
                    "series_type": old_series.get("series_type", 1),
                    "radiant_score": 0,
                    "dire_score": 0,
                    "last_updated": int(time.time())
                }
            
            # Fusionner les matchs
            for match_id in old_series.get("match_ids", []):
                if match_id not in series_data[new_series_id]["match_ids"]:
                    series_data[new_series_id]["match_ids"].append(match_id)
            
            # Mettre à jour les scores (prendre les plus élevés)
            series_data[new_series_id]["radiant_score"] = max(
                series_data[new_series_id].get("radiant_score", 0),
                old_series.get("radiant_score", 0)
            )
            series_data[new_series_id]["dire_score"] = max(
                series_data[new_series_id].get("dire_score", 0),
                old_series.get("dire_score", 0)
            )
            
            # Supprimer l'ancienne série
            del series_data[old_series_id]
            modified = True
    
    # Sauvegarder les modifications
    if modified:
        live_series_cache["series"] = series_data
        return save_cache(LIVE_SERIES_CACHE, live_series_cache)
    
    return True

def update_matches_in_live_data(series_mapping: Dict[str, str]) -> bool:
    """
    Met à jour les références aux séries dans les données des matchs
    
    Args:
        series_mapping: Dictionnaire mappant les anciens IDs de série aux nouveaux
    
    Returns:
        True si la mise à jour a réussi, False sinon
    """
    live_data = load_cache(LIVE_DATA_CACHE)
    matches = live_data.get("matches", {})
    modified = False
    
    for match_id, match_data in matches.items():
        # Mettre à jour l'ID de série dans le match si nécessaire
        series_id = match_data.get("series_id")
        if series_id in series_mapping:
            new_series_id = series_mapping[series_id]
            match_data["series_id"] = new_series_id
            
            # Mettre à jour également le match_type si présent
            if "match_type" in match_data and "series_id" in match_data["match_type"]:
                match_data["match_type"]["series_id"] = new_series_id
            
            modified = True
            logger.info(f"Match {match_id}: ID de série mis à jour {series_id} -> {new_series_id}")
    
    # Sauvegarder les modifications
    if modified:
        return save_cache(LIVE_DATA_CACHE, live_data)
    
    return True

def update_series_matches_mapping(series_mapping: Dict[str, str]) -> bool:
    """
    Met à jour le mapping entre séries et matchs
    
    Args:
        series_mapping: Dictionnaire mappant les anciens IDs de série aux nouveaux
    
    Returns:
        True si la mise à jour a réussi, False sinon
    """
    mapping_cache = load_cache(SERIES_MAPPING_CACHE)
    
    # Créer une copie pour éviter de modifier pendant l'itération
    new_mapping = mapping_cache.copy()
    modified = False
    
    # Pour chaque série dans le mapping
    for series_id, matches in mapping_cache.items():
        if series_id in series_mapping:
            new_series_id = series_mapping[series_id]
            
            # Ajouter les matchs à la nouvelle série
            if new_series_id not in new_mapping:
                new_mapping[new_series_id] = []
            
            for match_id in matches:
                if match_id not in new_mapping[new_series_id]:
                    new_mapping[new_series_id].append(match_id)
            
            # Supprimer l'ancienne série
            if series_id in new_mapping:
                del new_mapping[series_id]
                
            modified = True
            logger.info(f"Mapping: Série {series_id} fusionnée avec {new_series_id}")
    
    # Sauvegarder les modifications
    if modified:
        return save_cache(SERIES_MAPPING_CACHE, new_mapping)
    
    return True

def main():
    """Fonction principale"""
    logger.info("Démarrage de la correction des associations de séries...")
    
    # 1. Identifier les séries qui impliquent les mêmes équipes
    series_groups = identify_series_by_teams()
    
    if not series_groups:
        logger.info("Aucune série à fusionner trouvée")
        return
    
    logger.info(f"Trouvé {len(series_groups)} groupes de séries à fusionner")
    
    # 2. Fusionner les séries
    series_mapping = merge_series(series_groups)
    
    if not series_mapping:
        logger.info("Aucune série à mapper")
        return
    
    logger.info(f"Créé un mapping pour {len(series_mapping)} séries")
    
    # 3. Mettre à jour les caches
    logger.info("Mise à jour du cache des séries en direct...")
    if update_live_series_cache(series_mapping):
        logger.info("Cache des séries en direct mis à jour avec succès")
    
    logger.info("Mise à jour des données des matchs...")
    if update_matches_in_live_data(series_mapping):
        logger.info("Données des matchs mises à jour avec succès")
    
    logger.info("Mise à jour du mapping séries-matchs...")
    if update_series_matches_mapping(series_mapping):
        logger.info("Mapping séries-matchs mis à jour avec succès")
    
    logger.info("Correction des associations de séries terminée")

if __name__ == "__main__":
    main()
"""
Script pour mettre à jour manuellement les mappings de séries et de matchs.
Ce script permet d'ajouter facilement des matchs à une série et de créer des associations
entre des IDs de matchs et des séries Dotabuff.
"""

import os
import json
import logging
import time
from typing import Dict, List, Any

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
CACHE_DIR = "cache"
SERIES_MAPPING_FILE = os.path.join(CACHE_DIR, "series_matches_mapping.json")
MATCH_SERIES_FILE = os.path.join(CACHE_DIR, "match_to_series_mapping.json")

def load_series_mapping() -> Dict:
    """
    Charge le mapping des séries depuis le fichier de cache
    
    Returns:
        Dictionnaire contenant le mapping des séries
    """
    try:
        if os.path.exists(SERIES_MAPPING_FILE):
            with open(SERIES_MAPPING_FILE, 'r') as f:
                mapping = json.load(f)
                logger.info(f"Mapping des séries chargé, {len(mapping)} séries trouvées")
                return mapping
        else:
            logger.warning(f"Fichier de mapping {SERIES_MAPPING_FILE} non trouvé, création d'un nouveau mapping")
            return {}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du mapping des séries: {e}")
        return {}

def save_series_mapping(mapping: Dict) -> bool:
    """
    Sauvegarde le mapping des séries dans le fichier de cache
    
    Args:
        mapping: Dictionnaire contenant le mapping des séries
        
    Returns:
        Bool indiquant si la sauvegarde a réussi
    """
    try:
        # Créer le répertoire de cache s'il n'existe pas
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        with open(SERIES_MAPPING_FILE, 'w') as f:
            json.dump(mapping, f, indent=2)
            logger.info(f"Mapping des séries sauvegardé, {len(mapping)} séries")
            return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du mapping des séries: {e}")
        return False

def load_match_to_series_mapping() -> Dict:
    """
    Charge le mapping des matchs vers les séries depuis le fichier de cache
    
    Returns:
        Dictionnaire contenant le mapping des matchs vers les séries
    """
    try:
        if os.path.exists(MATCH_SERIES_FILE):
            with open(MATCH_SERIES_FILE, 'r') as f:
                mapping = json.load(f)
                logger.info(f"Mapping match→series chargé, {len(mapping)} matchs trouvés")
                return mapping
        else:
            logger.warning(f"Fichier de mapping {MATCH_SERIES_FILE} non trouvé, création d'un nouveau mapping")
            return {}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du mapping match→series: {e}")
        return {}

def save_match_to_series_mapping(mapping: Dict) -> bool:
    """
    Sauvegarde le mapping des matchs vers les séries dans le fichier de cache
    
    Args:
        mapping: Dictionnaire contenant le mapping des matchs vers les séries
        
    Returns:
        Bool indiquant si la sauvegarde a réussi
    """
    try:
        # Créer le répertoire de cache s'il n'existe pas
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        with open(MATCH_SERIES_FILE, 'w') as f:
            json.dump(mapping, f, indent=2)
            logger.info(f"Mapping match→series sauvegardé, {len(mapping)} matchs")
            return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du mapping match→series: {e}")
        return False

def add_series_with_matches(dotabuff_series_id: str, match_ids: List[str], team1_name: str = None, team2_name: str = None) -> Dict:
    """
    Ajoute une série Dotabuff avec ses matchs associés
    
    Args:
        dotabuff_series_id: ID de la série Dotabuff
        match_ids: Liste des IDs de matchs associés à cette série
        team1_name: Nom de l'équipe 1 (optionnel)
        team2_name: Nom de l'équipe 2 (optionnel)
        
    Returns:
        Dictionnaire indiquant le résultat de l'opération
    """
    try:
        # Charger les mappings existants
        series_mapping = load_series_mapping()
        match_to_series = load_match_to_series_mapping()
        
        # Créer ou mettre à jour l'entrée de série
        series_name = f"{team1_name} vs {team2_name}" if team1_name and team2_name else f"Série {dotabuff_series_id}"
        
        # Vérifier si la série existe déjà
        if dotabuff_series_id in series_mapping:
            logger.info(f"Mise à jour de la série existante {dotabuff_series_id}")
        else:
            logger.info(f"Création d'une nouvelle série {dotabuff_series_id}")
            series_mapping[dotabuff_series_id] = {
                "series_id": dotabuff_series_id,
                "series_name": series_name,
                "team1_name": team1_name or "Team 1",
                "team2_name": team2_name or "Team 2",
                "dotabuff_url": f"https://www.dotabuff.com/esports/series/{dotabuff_series_id}",
                "matches": [],
                "scrape_time": int(time.time())
            }
        
        # Ajouter les matchs à la série
        matches = []
        for i, match_id in enumerate(match_ids):
            # Ajouter au mapping match→series
            match_to_series[match_id] = dotabuff_series_id
            
            # Ajouter à la liste des matchs de la série
            matches.append({
                "match_id": match_id,
                "game_number": i + 1,
                "match_url": f"https://www.dotabuff.com/matches/{match_id}"
            })
        
        # Mettre à jour la liste des matchs dans la série
        if matches:
            series_mapping[dotabuff_series_id]["matches"] = matches
        
        # Sauvegarder les mappings
        save_series_mapping(series_mapping)
        save_match_to_series_mapping(match_to_series)
        
        return {
            "success": True,
            "series_id": dotabuff_series_id,
            "match_count": len(match_ids),
            "match_ids": match_ids
        }
    
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout de la série {dotabuff_series_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def list_mappings() -> Dict:
    """
    Liste tous les mappings de séries et de matchs
    
    Returns:
        Dictionnaire contenant des informations sur les mappings
    """
    try:
        series_mapping = load_series_mapping()
        match_to_series = load_match_to_series_mapping()
        
        return {
            "success": True,
            "series_count": len(series_mapping),
            "match_count": len(match_to_series),
            "series_keys": list(series_mapping.keys())[:5],  # Limiter à 5 pour la lisibilité
            "match_keys": list(match_to_series.keys())[:5]   # Limiter à 5 pour la lisibilité
        }
    
    except Exception as e:
        logger.error(f"Erreur lors de la liste des mappings: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def add_manual_examples():
    """
    Ajoute les exemples manuels basés sur les informations fournies.
    """
    # Premier exemple: Série 8257889151 avec ses trois matchs
    series_id_1 = "8257889151"
    matches_1 = ["8251760732", "8251881508", "8251980418"]
    
    logger.info(f"Ajout de l'exemple 1: Série {series_id_1} avec matchs {matches_1}")
    result_1 = add_series_with_matches(series_id_1, matches_1, "Team 1", "Team 2")
    
    # Deuxième exemple: Série 2666289 avec ses deux matchs
    series_id_2 = "2666289"
    matches_2 = ["8257889151", "8257938792"]
    
    logger.info(f"Ajout de l'exemple 2: Série {series_id_2} avec matchs {matches_2}")
    result_2 = add_series_with_matches(series_id_2, matches_2, "Team A", "Team B")
    
    # Afficher un résumé
    results = {
        "example_1": result_1,
        "example_2": result_2,
        "mappings": list_mappings()
    }
    
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    print("Mise à jour des mappings de séries avec les exemples manuels...")
    add_manual_examples()
    print("Terminé!")
#!/usr/bin/env python3
"""
Script dédié à la correction du problème spécifique avec la série s_8259450653
qui ne montre pas correctement tous les matchs liés à la série.

Ce script va extraire les données directement des fichiers cache et reconstruire
manuellement les liens entre les matchs de cette série spécifique.
"""

import os
import json
import logging
from typing import Dict, Any, List

# Configuration du logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes
CACHE_DIR = "cache"
LIVE_DATA_FILE = os.path.join(CACHE_DIR, "live_data.json")

# ID de série et des matchs liés à cette série
SERIES_ID = "s_8259450653"
MATCH_IDS = ["8259450653", "8259522321", "8259581999"]

def load_cache(file_path: str) -> Dict[str, Any]:
    """
    Charge un fichier de cache JSON
    
    Args:
        file_path (str): Chemin du fichier à charger
        
    Returns:
        dict: Données du cache ou dictionnaire vide en cas d'erreur
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        logger.error(f"Erreur lors du chargement du cache {file_path}: {e}")
        return {}

def save_cache(file_path: str, data: Dict[str, Any]) -> bool:
    """
    Sauvegarde un fichier de cache JSON
    
    Args:
        file_path (str): Chemin du fichier à sauvegarder
        data (dict): Données à sauvegarder
        
    Returns:
        bool: True si la sauvegarde a réussi, False sinon
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Cache sauvegardé dans {file_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache {file_path}: {e}")
        return False

def fix_series():
    """
    Corrige la série spécifique en reconstruisant les liens avec ses matchs
    
    Returns:
        bool: True si la correction a réussi, False sinon
    """
    # Charger le cache
    cache_data = load_cache(LIVE_DATA_FILE)
    if not cache_data or "series" not in cache_data or "matches" not in cache_data:
        logger.error("Le cache ne contient pas les données nécessaires")
        return False
    
    # Vérifier si la série existe
    if SERIES_ID not in cache_data["series"]:
        logger.error(f"La série {SERIES_ID} n'existe pas dans le cache")
        return False
    
    # Récupérer les données de la série
    series_data = cache_data["series"][SERIES_ID]
    
    # Mettre à jour la liste des matchs
    series_data["match_ids"] = MATCH_IDS
    
    # Préparer la liste des précédents matchs
    previous_matches = []
    
    # Pour chaque match
    for i, match_id in enumerate(MATCH_IDS, 1):
        if match_id not in cache_data["matches"]:
            logger.warning(f"Le match {match_id} n'existe pas dans le cache")
            continue
        
        match_data = cache_data["matches"][match_id]
        
        # Vérifier si le match a les données nécessaires
        radiant_score = match_data.get("radiant_score", 0)
        dire_score = match_data.get("dire_score", 0)
        duration = match_data.get("duration", "0:00")
        winner = match_data.get("winner")
        
        # Créer l'entrée pour previous_matches
        previous_match = {
            "match_id": match_id,
            "radiant_team_name": match_data.get("radiant_team_name"),
            "dire_team_name": match_data.get("dire_team_name"),
            "radiant_score": radiant_score,
            "dire_score": dire_score,
            "duration": duration,
            "total_kills": radiant_score + dire_score,
            "game_number": i,
            "winner": winner,
            "timestamp": match_data.get("start_time", 1744992210)  # Fallback à un temps récent
        }
        previous_matches.append(previous_match)
        
        # Mettre à jour le match pour pointer vers la série
        if "match_type" not in match_data:
            match_data["match_type"] = {}
        
        match_data["match_type"]["series_id"] = SERIES_ID
        match_data["match_type"]["series_type"] = 1  # Bo3
        match_data["match_type"]["series_max_value"] = 3
        match_data["match_type"]["series_current_value"] = i
        
        # Sauvegarder les changements au match
        cache_data["matches"][match_id] = match_data
        logger.info(f"Match {match_id} mis à jour pour la série {SERIES_ID}")
    
    # Mettre à jour la série avec les précédents matchs
    series_data["previous_matches"] = previous_matches
    cache_data["series"][SERIES_ID] = series_data
    
    # Sauvegarder le cache
    if save_cache(LIVE_DATA_FILE, cache_data):
        logger.info(f"Série {SERIES_ID} mise à jour avec {len(previous_matches)} matchs précédents")
        return True
    
    return False

def main():
    """Fonction principale"""
    print("===== Correction de la série spécifique =====")
    print(f"Série: {SERIES_ID}")
    print(f"Matchs: {', '.join(MATCH_IDS)}")
    
    if fix_series():
        print("Correction terminée avec succès!")
    else:
        print("Échec de la correction!")
    
    print("\nVérifiez l'interface pour voir si les changements sont appliqués.")

if __name__ == "__main__":
    main()
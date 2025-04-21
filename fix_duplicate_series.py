#!/usr/bin/env python3
"""
Script pour corriger les séries dupliquées en supprimant la série s_8261361161
qui contient des matchs incorrects et en gardant la série s_8261407829
qui contient les matchs actuels.
"""

import json
import logging
import os
from typing import Dict, Any

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
LIVE_SERIES_CACHE_PATH = 'cache/live_series_cache.json'
SERIES_MAPPING_PATH = 'cache/series_matches_mapping.json'

def load_cache(file_path: str) -> Dict[str, Any]:
    """
    Charge un fichier de cache JSON
    
    Args:
        file_path (str): Chemin du fichier à charger
        
    Returns:
        dict: Données du cache
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Erreur lors du chargement du cache {file_path}: {e}")
        if isinstance(e, FileNotFoundError):
            return {}
        # Pour JSONDecodeError, essayer de sauvegarder le fichier corrompu et créer un nouveau
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            try:
                os.rename(file_path, backup_path)
                logger.info(f"Cache corrompu sauvegardé sous {backup_path}")
            except Exception as backup_err:
                logger.error(f"Impossible de sauvegarder le cache corrompu: {backup_err}")
        return {}

def save_cache(file_path: str, cache_data: Dict[str, Any]) -> bool:
    """
    Sauvegarde un fichier de cache JSON
    
    Args:
        file_path (str): Chemin du fichier à sauvegarder
        cache_data (dict): Données à sauvegarder
        
    Returns:
        bool: True si succès, False sinon
    """
    try:
        # Créer le dossier parent si nécessaire
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(cache_data, file, indent=2, ensure_ascii=False)
        
        logger.info(f"Cache sauvegardé: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache {file_path}: {e}")
        return False

def fix_series():
    """
    Fonction principale pour corriger les séries dupliquées
    """
    # Charger les caches
    series_cache = load_cache(LIVE_SERIES_CACHE_PATH)
    series_mapping = load_cache(SERIES_MAPPING_PATH)
    
    # Afficher les informations sur les séries actuelles
    if 's_8261361161' in series_cache.get('series_data', {}):
        s1 = series_cache['series_data']['s_8261361161']
        logger.info(f"Série s_8261361161: {len(s1.get('match_ids', []))} matchs, {len(s1.get('previous_matches', []))} matchs précédents")
    else:
        logger.info("Série s_8261361161 non trouvée dans le cache live_series_cache.json")
    
    if 's_8261407829' in series_cache.get('series_data', {}):
        s2 = series_cache['series_data']['s_8261407829']
        logger.info(f"Série s_8261407829: {len(s2.get('match_ids', []))} matchs, {len(s2.get('previous_matches', []))} matchs précédents")
    else:
        logger.info("Série s_8261407829 non trouvée dans le cache live_series_cache.json")
    
    # 1. Supprimer la série s_8261361161 du cache live_series_cache.json
    if 's_8261361161' in series_cache.get('series_data', {}):
        del series_cache['series_data']['s_8261361161']
        logger.info("Série s_8261361161 supprimée du cache live_series_cache.json")
    
    # 2. Supprimer la série s_8261361161 du cache series_matches_mapping.json
    if 's_8261361161' in series_mapping:
        del series_mapping['s_8261361161']
        logger.info("Série s_8261361161 supprimée du cache series_matches_mapping.json")
    
    # 3. Sauvegarder les caches mis à jour
    if save_cache(LIVE_SERIES_CACHE_PATH, series_cache):
        logger.info("Cache live_series_cache.json mis à jour avec succès")
    else:
        logger.error("Erreur lors de la mise à jour du cache live_series_cache.json")
    
    if save_cache(SERIES_MAPPING_PATH, series_mapping):
        logger.info("Cache series_matches_mapping.json mis à jour avec succès")
    else:
        logger.error("Erreur lors de la mise à jour du cache series_matches_mapping.json")
    
    logger.info("Opération terminée")

if __name__ == "__main__":
    fix_series()
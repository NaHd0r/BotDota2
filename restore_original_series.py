#!/usr/bin/env python3
"""
Script pour restaurer la série s_8261361161 comme série principale et
y déplacer tous les matchs de la série s_8261407829, puis supprimer cette dernière.

La série s_8261361161 a été créée en premier et devrait être la série de référence.
"""

import json
import logging
import os
from typing import Dict, Any, List

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

def restore_original_series():
    """
    Fonction principale pour restaurer la série originale
    """
    # Charger les caches
    series_cache = load_cache(LIVE_SERIES_CACHE_PATH)
    series_mapping = load_cache(SERIES_MAPPING_PATH)
    
    # 1. Traitement du mapping series_matches_mapping.json
    s8261407829_exists = 's_8261407829' in series_mapping
    
    if s8261407829_exists:
        # Créer ou récupérer la série s_8261361161
        if 's_8261361161' not in series_mapping:
            series_mapping['s_8261361161'] = []
            logger.info("Série s_8261361161 créée dans le mapping")
        
        # Transférer les matchs de s_8261407829 à s_8261361161
        for match_id in series_mapping['s_8261407829']:
            if match_id not in series_mapping['s_8261361161']:
                series_mapping['s_8261361161'].append(match_id)
                logger.info(f"Match {match_id} transféré de s_8261407829 à s_8261361161 dans le mapping")
        
        # Supprimer la série s_8261407829
        del series_mapping['s_8261407829']
        logger.info("Série s_8261407829 supprimée du mapping")
    else:
        logger.warning("Série s_8261407829 non trouvée dans le mapping, rien à transférer")
    
    # 2. Traitement du cache live_series_cache.json
    if 'series' in series_cache:
        s8261407829_exists_live = 's_8261407829' in series_cache['series']
        
        if s8261407829_exists_live:
            # Récupérer les données de la série s_8261407829
            s8261407829_data = series_cache['series']['s_8261407829']
            
            # Créer la série s_8261361161 si elle n'existe pas
            if 's_8261361161' not in series_cache['series']:
                # Cloner les données de s_8261407829 mais changer l'ID
                s8261361161_data = s8261407829_data.copy()
                s8261361161_data['series_id'] = 's_8261361161'
                series_cache['series']['s_8261361161'] = s8261361161_data
                logger.info("Série s_8261361161 créée dans le cache live avec les données de s_8261407829")
            else:
                # Mettre à jour les champs importants de s_8261361161 avec ceux de s_8261407829
                series_cache['series']['s_8261361161']['match_ids'] = s8261407829_data.get('match_ids', [])
                series_cache['series']['s_8261361161']['previous_matches'] = s8261407829_data.get('previous_matches', [])
                series_cache['series']['s_8261361161']['radiant_score'] = s8261407829_data.get('radiant_score')
                series_cache['series']['s_8261361161']['dire_score'] = s8261407829_data.get('dire_score')
                series_cache['series']['s_8261361161']['series_type'] = s8261407829_data.get('series_type')
                series_cache['series']['s_8261361161']['last_updated'] = s8261407829_data.get('last_updated')
                logger.info("Série s_8261361161 mise à jour avec les données de s_8261407829")
            
            # Supprimer la série s_8261407829
            del series_cache['series']['s_8261407829']
            logger.info("Série s_8261407829 supprimée du cache live")
        else:
            logger.warning("Série s_8261407829 non trouvée dans le cache live, rien à transférer")
    
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
    restore_original_series()
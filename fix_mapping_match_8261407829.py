#!/usr/bin/env python3
"""
Script pour ajouter le match 8261407829 à la série s_8261407829 dans le mapping
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

def fix_mapping():
    """
    Fonction pour ajouter le match 8261407829 à la série s_8261407829 dans le mapping
    """
    # Charger le mapping
    series_mapping = load_cache(SERIES_MAPPING_PATH)
    
    # Vérifier si la série s_8261407829 existe
    if 's_8261407829' in series_mapping:
        # Vérifier si le match 8261407829 est déjà dans la liste
        if '8261407829' not in series_mapping['s_8261407829']:
            # Ajouter le match à la liste
            series_mapping['s_8261407829'].append('8261407829')
            logger.info("Match 8261407829 ajouté à la série s_8261407829 dans le mapping")
        else:
            logger.info("Le match 8261407829 est déjà présent dans la série s_8261407829")
    else:
        # Créer la série s_8261407829 si elle n'existe pas
        series_mapping['s_8261407829'] = ['8261361161', '8261407829']
        logger.info("Série s_8261407829 créée avec les matchs 8261361161 et 8261407829")
    
    # Sauvegarder le mapping mis à jour
    if save_cache(SERIES_MAPPING_PATH, series_mapping):
        logger.info("Mapping mis à jour avec succès")
    else:
        logger.error("Erreur lors de la mise à jour du mapping")
    
    logger.info("Opération terminée")

if __name__ == "__main__":
    fix_mapping()
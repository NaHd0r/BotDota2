"""
Script pour standardiser définitivement les états de jeu dans tous les caches.

Ce script va :
1. Adopter des valeurs standard pour tous les états de jeu
2. Éliminer les traductions et variantes françaises
3. Uniformiser les champs status et status_tag
"""

import json
import os
import logging
from typing import Dict, Any, List

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
LIVE_CACHE_FILE = 'cache/live_series_cache.json'
HISTORICAL_DATA_FILE = 'cache/historical_data.json'

# Standards à adopter (basés sur les valeurs de l'API Steam)
# Pour status (lowercase)
STANDARD_STATUS = {
    # Draft phase variants
    'draft': 'draft',
    'en draft': 'draft',
    'DRAFT': 'draft',
    'Draft': 'draft',
    'pregame': 'draft',
    # Game phase variants
    'game': 'game',
    'EN JEU': 'game',
    'en jeu': 'game',
    'en cours': 'game',
    'en_cours': 'game',
    'in_progress': 'game',
    'IN PROGRESS': 'game',
    'live': 'game',
    'GAME': 'game',
    'Game': 'game',
    # Finished phase variants
    'finished': 'finished',
    'terminé': 'finished',
    'TERMINÉ': 'finished',
    'terminée': 'finished',
    'TERMINÉE': 'finished',
    'fini': 'finished',
    'FINI': 'finished',
    'FINISHED': 'finished',
    'Finished': 'finished',
}

# Pour status_tag (maintenant aussi en lowercase pour plus de cohérence)
STANDARD_STATUS_TAG = {
    # Draft phase variants
    'draft': 'draft',
    'en draft': 'draft',
    'DRAFT': 'draft',
    'Draft': 'draft',
    'pregame': 'draft',
    # Game phase variants
    'game': 'game',
    'EN JEU': 'game',
    'en jeu': 'game',
    'en cours': 'game',
    'en_cours': 'game',
    'in_progress': 'game',
    'IN PROGRESS': 'game',
    'live': 'game',
    'GAME': 'game',
    'Game': 'game',
    # Finished phase variants
    'finished': 'finished',
    'terminé': 'finished',
    'TERMINÉ': 'finished',
    'terminée': 'finished',
    'TERMINÉE': 'finished',
    'fini': 'finished',
    'FINI': 'finished',
    'FINISHED': 'finished',
    'Finished': 'finished',
}

def load_cache(file_path: str) -> Dict[str, Any]:
    """Charge un fichier de cache JSON"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"Le fichier {file_path} n'existe pas. Création d'un cache vide.")
            return {}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du cache {file_path}: {e}")
        return {}

def save_cache(file_path: str, cache_data: Dict[str, Any]) -> bool:
    """Sauvegarde un fichier de cache JSON"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
        logger.info(f"Cache sauvegardé: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache {file_path}: {e}")
        return False

def standardize_match_states(match_data: Dict[str, Any]) -> bool:
    """
    Standardise les états d'un match selon les valeurs définies
    
    Args:
        match_data: Données du match à standardiser
        
    Returns:
        bool: True si des modifications ont été apportées
    """
    updated = False
    
    # Standardiser le status
    if 'status' in match_data and match_data['status'] in STANDARD_STATUS:
        old_value = match_data['status']
        match_data['status'] = STANDARD_STATUS[old_value]
        if old_value != match_data['status']:
            updated = True
            logger.info(f"Status standardisé: '{old_value}' -> '{match_data['status']}'")
    
    # Standardiser le status_tag
    if 'status_tag' in match_data and match_data['status_tag'] in STANDARD_STATUS_TAG:
        old_value = match_data['status_tag']
        match_data['status_tag'] = STANDARD_STATUS_TAG[old_value]
        if old_value != match_data['status_tag']:
            updated = True
            logger.info(f"Status_tag standardisé: '{old_value}' -> '{match_data['status_tag']}'")
    
    # S'assurer que les deux champs sont présents et cohérents
    if 'status' in match_data and 'status_tag' not in match_data:
        status = match_data['status']
        match_data['status_tag'] = STANDARD_STATUS_TAG.get(status, 'UNKNOWN')
        updated = True
        logger.info(f"Status_tag ajouté sur base du status: '{status}' -> '{match_data['status_tag']}'")
    
    elif 'status_tag' in match_data and 'status' not in match_data:
        status_tag = match_data['status_tag']
        match_data['status'] = STANDARD_STATUS.get(status_tag, 'unknown')
        updated = True
        logger.info(f"Status ajouté sur base du status_tag: '{status_tag}' -> '{match_data['status']}'")
    
    # Standardiser également dans les sous-structures
    if 'data' in match_data and isinstance(match_data['data'], dict):
        sub_updated = standardize_match_states(match_data['data'])
        if sub_updated:
            updated = True
    
    return updated

def standardize_live_cache() -> bool:
    """Standardise les états dans le cache live"""
    live_cache = load_cache(LIVE_CACHE_FILE)
    updated = False
    
    # Standardiser les matchs dans le cache live
    if 'matches' in live_cache:
        for match_id, match_data in live_cache['matches'].items():
            match_updated = standardize_match_states(match_data)
            if match_updated:
                updated = True
                logger.info(f"Match {match_id} standardisé")
    
    # Standardiser dans les séries
    if 'series' in live_cache:
        for series_id, series_data in live_cache['series'].items():
            # Standardiser les matchs précédents dans la série
            if 'previous_matches' in series_data:
                for i, prev_match in enumerate(series_data['previous_matches']):
                    prev_updated = standardize_match_states(prev_match)
                    if prev_updated:
                        updated = True
                        logger.info(f"Match précédent {i} dans série {series_id} standardisé")
    
    if updated:
        save_cache(LIVE_CACHE_FILE, live_cache)
    
    return updated

def standardize_historical_data() -> bool:
    """Standardise les états dans les données historiques"""
    historical_data = load_cache(HISTORICAL_DATA_FILE)
    updated = False
    
    # Standardiser les matchs dans l'historique
    if 'matches' in historical_data:
        for match_id, match_data in historical_data['matches'].items():
            match_updated = standardize_match_states(match_data)
            if match_updated:
                updated = True
                logger.info(f"Match historique {match_id} standardisé")
    
    if updated:
        save_cache(HISTORICAL_DATA_FILE, historical_data)
    
    return updated

def main():
    """Fonction principale du script"""
    logger.info("Démarrage de la standardisation des états de jeu")
    
    live_updated = standardize_live_cache()
    logger.info(f"Standardisation du cache live: {'Mise à jour effectuée' if live_updated else 'Aucune modification nécessaire'}")
    
    hist_updated = standardize_historical_data()
    logger.info(f"Standardisation des données historiques: {'Mise à jour effectuée' if hist_updated else 'Aucune modification nécessaire'}")
    
    logger.info("Standardisation des états de jeu terminée")

if __name__ == "__main__":
    main()
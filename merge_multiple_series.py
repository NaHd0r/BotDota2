"""
Script pour fusionner plusieurs séries en une seule

Ce script fusionne les séries s_8260632006 et s_8260717084 dans la série s_8260778197
"""

import json
import os
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
LIVE_CACHE_FILE = 'cache/live_series_cache.json'
HISTORICAL_DATA_FILE = 'cache/historical_data.json'
SERIES_MAPPING_FILE = 'cache/series_matches_mapping.json'

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

def merge_series_into_target(source_series_ids: List[str], target_series_id: str) -> bool:
    """
    Fusionne plusieurs séries en une seule série cible
    
    Args:
        source_series_ids (list): Liste des IDs de séries sources (seront supprimées après fusion)
        target_series_id (str): ID de la série cible (sera conservée)
        
    Returns:
        bool: True si la fusion a réussi, False sinon
    """
    try:
        # Charger les caches
        live_cache = load_cache(LIVE_CACHE_FILE)
        historical_data = load_cache(HISTORICAL_DATA_FILE)
        series_mapping = load_cache(SERIES_MAPPING_FILE)
        
        updated = False
        
        # 1. Fusionner les séries dans live_cache
        if 'series' in live_cache:
            target_series = live_cache['series'].get(target_series_id, {})
            
            # Si la série cible n'existe pas encore, créer un modèle vide
            if not target_series:
                logger.warning(f"La série cible {target_series_id} n'existe pas dans le cache live, création d'une série vide")
                target_series = {
                    'series_id': target_series_id,
                    'match_ids': [],
                    'radiant_score': 0,
                    'dire_score': 0,
                    'radiant_team': None,
                    'dire_team': None
                }
                live_cache['series'][target_series_id] = target_series
            
            for source_series_id in source_series_ids:
                if source_series_id in live_cache['series']:
                    source_series = live_cache['series'][source_series_id]
                    
                    # Transférer les match_ids
                    if 'match_ids' in source_series:
                        if 'match_ids' not in target_series:
                            target_series['match_ids'] = []
                        
                        for match_id in source_series.get('match_ids', []):
                            if match_id not in target_series['match_ids']:
                                target_series['match_ids'].append(match_id)
                                logger.info(f"Match {match_id} transféré de {source_series_id} à {target_series_id}")
                                updated = True
                    
                    # Mettre à jour le score si nécessaire
                    if 'radiant_score' in source_series and source_series['radiant_score'] > 0:
                        target_series['radiant_score'] = max(target_series.get('radiant_score', 0), source_series.get('radiant_score', 0))
                        updated = True
                    
                    if 'dire_score' in source_series and source_series['dire_score'] > 0:
                        target_series['dire_score'] = max(target_series.get('dire_score', 0), source_series.get('dire_score', 0))
                        updated = True
                    
                    # Mettre à jour les équipes si nécessaires
                    if not target_series.get('radiant_team') and source_series.get('radiant_team'):
                        target_series['radiant_team'] = source_series['radiant_team']
                        updated = True
                    
                    if not target_series.get('dire_team') and source_series.get('dire_team'):
                        target_series['dire_team'] = source_series['dire_team']
                        updated = True
                    
                    # Mettre à jour les références des matchs vers la série
                    if 'matches' in live_cache:
                        for match_id in source_series.get('match_ids', []):
                            if match_id in live_cache['matches']:
                                match_data = live_cache['matches'][match_id]
                                match_data['series_id'] = target_series_id
                                logger.info(f"Référence du match {match_id} mise à jour vers {target_series_id}")
                                updated = True
                    
                    # Supprimer la série source
                    del live_cache['series'][source_series_id]
                    logger.info(f"Série source {source_series_id} supprimée du cache live")
                    updated = True
                else:
                    logger.warning(f"Série source {source_series_id} non trouvée dans le cache live")
        
        # 2. Fusionner les séries dans historical_data
        if 'series' in historical_data:
            # Si la série cible n'existe pas encore en historique, la créer
            if target_series_id not in historical_data['series']:
                logger.warning(f"La série cible {target_series_id} n'existe pas dans l'historique, création d'une série vide")
                target_series = {
                    'series_id': target_series_id,
                    'match_ids': [],
                    'radiant_score': 0,
                    'dire_score': 0,
                    'radiant_team': None,
                    'dire_team': None
                }
                historical_data['series'][target_series_id] = target_series
            
            target_series = historical_data['series'][target_series_id]
            
            for source_series_id in source_series_ids:
                if source_series_id in historical_data['series']:
                    source_series = historical_data['series'][source_series_id]
                    
                    # Transférer les match_ids
                    if 'match_ids' in source_series:
                        if 'match_ids' not in target_series:
                            target_series['match_ids'] = []
                        
                        for match_id in source_series.get('match_ids', []):
                            if match_id not in target_series['match_ids']:
                                target_series['match_ids'].append(match_id)
                                logger.info(f"Match {match_id} transféré de {source_series_id} à {target_series_id} (historical)")
                                updated = True
                    
                    # Mettre à jour le score si nécessaire
                    if 'radiant_score' in source_series and source_series['radiant_score'] > 0:
                        target_series['radiant_score'] = max(target_series.get('radiant_score', 0), source_series.get('radiant_score', 0))
                        updated = True
                    
                    if 'dire_score' in source_series and source_series['dire_score'] > 0:
                        target_series['dire_score'] = max(target_series.get('dire_score', 0), source_series.get('dire_score', 0))
                        updated = True
                    
                    # Mettre à jour les équipes si nécessaires
                    if not target_series.get('radiant_team') and source_series.get('radiant_team'):
                        target_series['radiant_team'] = source_series['radiant_team']
                        updated = True
                    
                    if not target_series.get('dire_team') and source_series.get('dire_team'):
                        target_series['dire_team'] = source_series['dire_team']
                        updated = True
                    
                    # Mettre à jour les références des matchs vers la série
                    if 'matches' in historical_data:
                        for match_id in source_series.get('match_ids', []):
                            match_id_str = match_id
                            if not match_id_str.startswith('match_'):
                                match_id_str = f"match_{match_id}"
                                
                            if match_id_str in historical_data['matches']:
                                match_data = historical_data['matches'][match_id_str]
                                if 'data' in match_data:
                                    match_data['data']['series_id'] = target_series_id
                                    logger.info(f"Référence du match {match_id} mise à jour vers {target_series_id} (historical)")
                                    updated = True
                    
                    # Supprimer la série source
                    del historical_data['series'][source_series_id]
                    logger.info(f"Série source {source_series_id} supprimée des données historiques")
                    updated = True
                else:
                    logger.warning(f"Série source {source_series_id} non trouvée dans l'historique")
        
        # 3. Mettre à jour series_mapping
        # S'assurer que la série cible existe dans le mapping
        if target_series_id not in series_mapping:
            series_mapping[target_series_id] = []
        
        target_matches = series_mapping[target_series_id]
        
        for source_series_id in source_series_ids:
            if source_series_id in series_mapping:
                source_matches = series_mapping[source_series_id]
                
                # Ajouter les matchs de la source à la cible
                for match_id in source_matches:
                    if match_id not in target_matches:
                        target_matches.append(match_id)
                        logger.info(f"Match {match_id} ajouté à la série {target_series_id} dans series_mapping")
                        updated = True
                
                # Supprimer la série source
                del series_mapping[source_series_id]
                logger.info(f"Série source {source_series_id} supprimée de series_mapping")
                updated = True
            else:
                logger.warning(f"Série source {source_series_id} non trouvée dans series_mapping")
        
        # Sauvegarder les changements
        if updated:
            save_cache(LIVE_CACHE_FILE, live_cache)
            save_cache(HISTORICAL_DATA_FILE, historical_data)
            save_cache(SERIES_MAPPING_FILE, series_mapping)
            logger.info(f"Fusion des séries vers {target_series_id} terminée avec succès")
            return True
        else:
            logger.warning(f"Aucune modification effectuée lors de la fusion des séries")
            return False
        
    except Exception as e:
        logger.error(f"Erreur lors de la fusion des séries: {e}")
        return False

def main():
    """Fonction principale du script"""
    logger.info("Démarrage du script de fusion de séries multiples")
    
    # Définir les séries à fusionner
    source_series = ["s_8260632006", "s_8260717084"]
    target_series = "s_8260778197"
    
    # Exécuter la fusion
    success = merge_series_into_target(source_series, target_series)
    
    if success:
        logger.info(f"Fusion des séries {', '.join(source_series)} vers {target_series} terminée avec succès")
    else:
        logger.error(f"Échec de la fusion des séries {', '.join(source_series)} vers {target_series}")
    
    logger.info("Script terminé")

if __name__ == "__main__":
    main()
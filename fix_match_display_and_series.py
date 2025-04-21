"""
Script pour corriger l'affichage des matchs dans les séries et fusionner les séries séparées incorrectement

Ce script:
1. Corrige l'affichage du vainqueur dans les matchs terminés
2. Fusionne les séries s_8260632006 et s_8260717084 qui devraient être une seule série
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

def fix_match_winner_display() -> bool:
    """
    Corrige l'affichage du vainqueur dans les matchs terminés en s'assurant que le champ
    winner contient bien "radiant" ou "dire" et que le status est correctement défini.
    Utilise également le champ game_state pour déterminer le vainqueur.
    """
    historical_data = load_cache(HISTORICAL_DATA_FILE)
    live_cache = load_cache(LIVE_CACHE_FILE)
    
    updated = False
    
    # Parcourir les matchs dans historical_data
    if 'matches' in historical_data:
        for match_id, match_data in historical_data['matches'].items():
            if isinstance(match_data, dict) and 'data' in match_data:
                match_info = match_data['data']
                
                # Vérifier si le match est terminé mais n'a pas de vainqueur défini
                if 'winner' not in match_info or not match_info['winner']:
                    # Déterminer le vainqueur en fonction de radiant_win
                    if 'radiant_win' in match_info:
                        match_info['winner'] = 'radiant' if match_info['radiant_win'] else 'dire'
                        logger.info(f"Match {match_id}: vainqueur défini à {match_info['winner']} (basé sur radiant_win)")
                        updated = True
                    # Ou essayer de le déterminer à partir de game_state
                    elif 'game_state' in match_info:
                        game_state = match_info.get('game_state')
                        if game_state == 2:  # Victoire Radiant
                            match_info['winner'] = 'radiant'
                            match_info['radiant_win'] = True
                            logger.info(f"Match {match_id}: vainqueur défini à radiant (basé sur game_state={game_state})")
                            updated = True
                        elif game_state == 3:  # Victoire Dire
                            match_info['winner'] = 'dire'
                            match_info['radiant_win'] = False
                            logger.info(f"Match {match_id}: vainqueur défini à dire (basé sur game_state={game_state})")
                            updated = True
                
                # S'assurer que le status est correctement défini
                if 'status' not in match_data or match_data['status'] != 'finished':
                    is_finished = False
                    # Vérifier la durée
                    if 'duration' in match_info and match_info['duration']:
                        is_finished = True
                    # Vérifier le game_state (2=Radiant win, 3=Dire win)
                    elif 'game_state' in match_info and match_info['game_state'] in [2, 3]:
                        is_finished = True
                    
                    if is_finished:
                        match_data['status'] = 'finished'
                        match_data['status_tag'] = 'TERMINÉ'
                        logger.info(f"Match {match_id}: statut mis à jour à 'finished'")
                        updated = True
    
    # Également vérifier les matchs dans le cache live
    if 'matches' in live_cache:
        for match_id, match_data in live_cache['matches'].items():
            # Vérifier si le match est terminé mais sans vainqueur
            if 'winner' not in match_data:
                # Utiliser radiant_win si disponible
                if 'radiant_win' in match_data:
                    match_data['winner'] = 'radiant' if match_data['radiant_win'] else 'dire'
                    logger.info(f"Live cache - Match {match_id}: vainqueur défini à {match_data['winner']} (basé sur radiant_win)")
                    updated = True
                # Ou essayer de le déterminer à partir de game_state
                elif 'game_state' in match_data:
                    game_state = match_data.get('game_state')
                    if game_state == 2:  # Victoire Radiant
                        match_data['winner'] = 'radiant'
                        match_data['radiant_win'] = True
                        logger.info(f"Live cache - Match {match_id}: vainqueur défini à radiant (basé sur game_state={game_state})")
                        updated = True
                    elif game_state == 3:  # Victoire Dire
                        match_data['winner'] = 'dire'
                        match_data['radiant_win'] = False
                        logger.info(f"Live cache - Match {match_id}: vainqueur défini à dire (basé sur game_state={game_state})")
                        updated = True
            
            # S'assurer que le statut est correct pour les matchs terminés
            if 'status' not in match_data:
                is_finished = False
                # Vérifier la durée
                if 'duration' in match_data and match_data['duration']:
                    is_finished = True
                # Vérifier le game_state (2=Radiant win, 3=Dire win)
                elif 'game_state' in match_data and match_data['game_state'] in [2, 3]:
                    is_finished = True
                
                if is_finished:
                    match_data['status'] = 'finished'
                    match_data['status_tag'] = 'TERMINÉ'
                    logger.info(f"Live cache - Match {match_id}: statut mis à jour à 'finished'")
                    updated = True
    
    # Sauvegarder les changements
    if updated:
        save_cache(HISTORICAL_DATA_FILE, historical_data)
        save_cache(LIVE_CACHE_FILE, live_cache)
        logger.info("Correction de l'affichage des vainqueurs terminée")
    else:
        logger.info("Aucune correction nécessaire pour l'affichage des vainqueurs")
    
    return updated

def merge_series(source_series_id: str, target_series_id: str) -> bool:
    """
    Fusionne deux séries en déplaçant tous les matchs de la série source vers la série cible
    
    Args:
        source_series_id (str): ID de la série source (sera supprimée après fusion)
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
            if source_series_id in live_cache['series'] and target_series_id in live_cache['series']:
                source_series = live_cache['series'][source_series_id]
                target_series = live_cache['series'][target_series_id]
                
                # Transférer les match_ids
                if 'match_ids' in source_series:
                    if 'match_ids' not in target_series:
                        target_series['match_ids'] = []
                    
                    for match_id in source_series['match_ids']:
                        if match_id not in target_series['match_ids']:
                            target_series['match_ids'].append(match_id)
                            logger.info(f"Match {match_id} transféré de {source_series_id} à {target_series_id}")
                
                # Mettre à jour le score si nécessaire
                if 'radiant_score' in source_series and source_series['radiant_score'] > 0:
                    target_series['radiant_score'] = max(target_series.get('radiant_score', 0), source_series.get('radiant_score', 0))
                    updated = True
                
                if 'dire_score' in source_series and source_series['dire_score'] > 0:
                    target_series['dire_score'] = max(target_series.get('dire_score', 0), source_series.get('dire_score', 0))
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
        
        # 2. Fusionner les séries dans historical_data
        if 'series' in historical_data:
            if source_series_id in historical_data['series'] and target_series_id in historical_data['series']:
                source_series = historical_data['series'][source_series_id]
                target_series = historical_data['series'][target_series_id]
                
                # Transférer les match_ids
                if 'match_ids' in source_series:
                    if 'match_ids' not in target_series:
                        target_series['match_ids'] = []
                    
                    for match_id in source_series['match_ids']:
                        if match_id not in target_series['match_ids']:
                            target_series['match_ids'].append(match_id)
                            logger.info(f"Match {match_id} transféré de {source_series_id} à {target_series_id} (historical)")
                
                # Mettre à jour le score si nécessaire
                if 'radiant_score' in source_series and source_series['radiant_score'] > 0:
                    target_series['radiant_score'] = max(target_series.get('radiant_score', 0), source_series.get('radiant_score', 0))
                    updated = True
                
                if 'dire_score' in source_series and source_series['dire_score'] > 0:
                    target_series['dire_score'] = max(target_series.get('dire_score', 0), source_series.get('dire_score', 0))
                    updated = True
                
                # Mettre à jour les références des matchs vers la série
                if 'matches' in historical_data:
                    for match_id in source_series.get('match_ids', []):
                        if match_id in historical_data['matches']:
                            match_data = historical_data['matches'][match_id]
                            if 'data' in match_data:
                                match_data['data']['series_id'] = target_series_id
                                logger.info(f"Référence du match {match_id} mise à jour vers {target_series_id} (historical)")
                                updated = True
                
                # Supprimer la série source
                del historical_data['series'][source_series_id]
                logger.info(f"Série source {source_series_id} supprimée des données historiques")
                updated = True
        
        # 3. Mettre à jour series_mapping
        if source_series_id in series_mapping and target_series_id in series_mapping:
            source_matches = series_mapping[source_series_id]
            target_matches = series_mapping[target_series_id]
            
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
        
        # Sauvegarder les changements
        if updated:
            save_cache(LIVE_CACHE_FILE, live_cache)
            save_cache(HISTORICAL_DATA_FILE, historical_data)
            save_cache(SERIES_MAPPING_FILE, series_mapping)
            logger.info(f"Fusion des séries {source_series_id} vers {target_series_id} terminée avec succès")
            return True
        else:
            logger.warning(f"Aucune modification effectuée lors de la fusion des séries")
            return False
        
    except Exception as e:
        logger.error(f"Erreur lors de la fusion des séries: {e}")
        return False

def main():
    """Fonction principale du script"""
    logger.info("Démarrage du script de correction d'affichage et de fusion des séries")
    
    # 1. Corriger l'affichage des vainqueurs
    fix_match_winner_display()
    
    # 2. Fusionner les séries incorrectement séparées
    merge_series("s_8260632006", "s_8260717084")
    
    logger.info("Script terminé")

if __name__ == "__main__":
    main()
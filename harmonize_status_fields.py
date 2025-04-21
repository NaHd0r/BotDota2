"""
Script pour harmoniser les champs d'état dans les caches

Ce script normalise tous les champs d'état (status, status_tag, game_state) pour utiliser
uniquement la version anglaise afin de garantir que le déclenchement de
l'enrichissement des données fonctionne correctement.
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

# Mappings des états
STATUS_MAPPING = {
    # Français vers anglais
    "terminé": "finished",
    "TERMINÉ": "finished",
    "en_cours": "in_progress",
    "en cours": "in_progress",
    "draft": "draft",
    # Assurer la cohérence même si déjà en anglais
    "finished": "finished",
    "in_progress": "in_progress",
    "in progress": "in_progress",
    "game": "in_progress"
}

STATUS_TAG_MAPPING = {
    # Français vers anglais
    "TERMINÉ": "FINISHED",
    "EN COURS": "IN PROGRESS",
    "DRAFT": "DRAFT",
    # Assurer la cohérence même si déjà en anglais
    "FINISHED": "FINISHED", 
    "IN PROGRESS": "IN PROGRESS",
    "DRAFT": "DRAFT"
}

GAME_STATE_MAPPING = {
    # Valeurs numériques vers états textuels
    "0": "pre_game",
    "1": "in_progress", 
    "2": "radiant_win",
    "3": "dire_win",
    "4": "post_game",
    # Valeurs textuelles vers standardisées
    "pre_game": "pre_game",
    "in_progress": "in_progress",
    "radiant_win": "radiant_win",
    "dire_win": "dire_win",
    "post_game": "post_game"
}

WINNER_MAPPING = {
    # Français vers anglais
    "radiant": "radiant",
    "dire": "dire",
    "Radiant": "radiant",
    "Dire": "dire"
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

def harmonize_live_cache() -> bool:
    """
    Harmonise les champs d'état dans le cache live
    """
    live_cache = load_cache(LIVE_CACHE_FILE)
    updated = False
    
    if 'matches' in live_cache:
        for match_id, match_data in live_cache['matches'].items():
            # Harmoniser le champ status
            if 'status' in match_data:
                old_status = match_data['status']
                if old_status in STATUS_MAPPING:
                    match_data['status'] = STATUS_MAPPING[old_status]
                    logger.info(f"Match {match_id}: status '{old_status}' -> '{match_data['status']}'")
                    updated = True
            
            # Harmoniser le champ status_tag
            if 'status_tag' in match_data:
                old_tag = match_data['status_tag']
                if old_tag in STATUS_TAG_MAPPING:
                    match_data['status_tag'] = STATUS_TAG_MAPPING[old_tag]
                    logger.info(f"Match {match_id}: status_tag '{old_tag}' -> '{match_data['status_tag']}'")
                    updated = True
            
            # Harmoniser le champ game_state (si c'est une chaîne)
            if 'game_state' in match_data and isinstance(match_data['game_state'], str):
                old_state = match_data['game_state']
                if old_state in GAME_STATE_MAPPING:
                    match_data['game_state'] = GAME_STATE_MAPPING[old_state]
                    logger.info(f"Match {match_id}: game_state '{old_state}' -> '{match_data['game_state']}'")
                    updated = True
            
            # Harmoniser le champ winner
            if 'winner' in match_data:
                old_winner = match_data['winner']
                if old_winner in WINNER_MAPPING:
                    match_data['winner'] = WINNER_MAPPING[old_winner]
                    logger.info(f"Match {match_id}: winner '{old_winner}' -> '{match_data['winner']}'")
                    updated = True
    
    # Si la structure est différente, adapter en conséquence
    if updated:
        save_cache(LIVE_CACHE_FILE, live_cache)
        logger.info("Cache live harmonisé avec succès")
    else:
        logger.info("Aucune modification nécessaire dans le cache live")
    
    return updated

def harmonize_historical_data() -> bool:
    """
    Harmonise les champs d'état dans les données historiques
    """
    historical_data = load_cache(HISTORICAL_DATA_FILE)
    updated = False
    
    if 'matches' in historical_data:
        for match_id, match_data in historical_data['matches'].items():
            # Harmoniser le champ status au niveau supérieur
            if 'status' in match_data:
                old_status = match_data['status']
                if old_status in STATUS_MAPPING:
                    match_data['status'] = STATUS_MAPPING[old_status]
                    logger.info(f"Historical match {match_id}: status '{old_status}' -> '{match_data['status']}'")
                    updated = True
            
            # Harmoniser le champ status_tag au niveau supérieur
            if 'status_tag' in match_data:
                old_tag = match_data['status_tag']
                if old_tag in STATUS_TAG_MAPPING:
                    match_data['status_tag'] = STATUS_TAG_MAPPING[old_tag]
                    logger.info(f"Historical match {match_id}: status_tag '{old_tag}' -> '{match_data['status_tag']}'")
                    updated = True
            
            # Si les données du match sont dans un sous-champ "data"
            if 'data' in match_data and isinstance(match_data['data'], dict):
                match_info = match_data['data']
                
                # Harmoniser le champ status dans data
                if 'status' in match_info:
                    old_status = match_info['status']
                    if old_status in STATUS_MAPPING:
                        match_info['status'] = STATUS_MAPPING[old_status]
                        logger.info(f"Historical match {match_id} data: status '{old_status}' -> '{match_info['status']}'")
                        updated = True
                
                # Harmoniser le champ status_tag dans data
                if 'status_tag' in match_info:
                    old_tag = match_info['status_tag']
                    if old_tag in STATUS_TAG_MAPPING:
                        match_info['status_tag'] = STATUS_TAG_MAPPING[old_tag]
                        logger.info(f"Historical match {match_id} data: status_tag '{old_tag}' -> '{match_info['status_tag']}'")
                        updated = True
                
                # Harmoniser le champ game_state dans data (si c'est une chaîne)
                if 'game_state' in match_info and isinstance(match_info['game_state'], str):
                    old_state = match_info['game_state']
                    if old_state in GAME_STATE_MAPPING:
                        match_info['game_state'] = GAME_STATE_MAPPING[old_state]
                        logger.info(f"Historical match {match_id} data: game_state '{old_state}' -> '{match_info['game_state']}'")
                        updated = True
                
                # Harmoniser le champ winner dans data
                if 'winner' in match_info:
                    old_winner = match_info['winner']
                    if old_winner in WINNER_MAPPING:
                        match_info['winner'] = WINNER_MAPPING[old_winner]
                        logger.info(f"Historical match {match_id} data: winner '{old_winner}' -> '{match_info['winner']}'")
                        updated = True
    
    if updated:
        save_cache(HISTORICAL_DATA_FILE, historical_data)
        logger.info("Données historiques harmonisées avec succès")
    else:
        logger.info("Aucune modification nécessaire dans les données historiques")
    
    return updated

def update_status_for_match_enrichment() -> bool:
    """
    Met à jour spécifiquement les champs de statut pour s'assurer que l'enrichissement
    est correctement déclenché pour les matchs terminés
    """
    live_cache = load_cache(LIVE_CACHE_FILE)
    updated = False
    
    if 'matches' in live_cache:
        for match_id, match_data in live_cache['matches'].items():
            # Vérifier si le match est terminé en fonction des indicateurs
            is_finished = False
            
            # Vérifier si game_state indique une victoire
            if 'game_state' in match_data:
                game_state = match_data['game_state']
                if isinstance(game_state, int) and game_state in [2, 3]:
                    is_finished = True
                elif isinstance(game_state, str) and game_state in ['radiant_win', 'dire_win']:
                    is_finished = True
            
            # Vérifier s'il y a un winner
            if 'winner' in match_data and match_data['winner'] in ['radiant', 'dire']:
                is_finished = True
            
            # Vérifier s'il y a radiant_win
            if 'radiant_win' in match_data:
                is_finished = True
            
            # Appliquer le statut fini si détecté
            if is_finished:
                if 'status' not in match_data or match_data['status'] != 'finished':
                    match_data['status'] = 'finished'
                    logger.info(f"Match {match_id}: statut forcé à 'finished' pour l'enrichissement")
                    updated = True
                
                if 'status_tag' not in match_data or match_data['status_tag'] != 'FINISHED':
                    match_data['status_tag'] = 'FINISHED'
                    logger.info(f"Match {match_id}: status_tag forcé à 'FINISHED' pour l'enrichissement")
                    updated = True
    
    if updated:
        save_cache(LIVE_CACHE_FILE, live_cache)
        logger.info("Statuts mis à jour pour l'enrichissement")
    else:
        logger.info("Aucune mise à jour de statut nécessaire pour l'enrichissement")
    
    return updated

def get_active_series_and_matches():
    """
    Analyse les caches pour déterminer les séries et matchs actifs,
    et leur état d'enrichissement
    """
    live_cache = load_cache(LIVE_CACHE_FILE)
    
    active_series = {}
    active_matches = {}
    
    if 'series' in live_cache:
        for series_id, series_data in live_cache['series'].items():
            match_ids = series_data.get('match_ids', [])
            if match_ids:
                active_series[series_id] = {
                    'match_ids': match_ids,
                    'radiant_score': series_data.get('radiant_score', 0),
                    'dire_score': series_data.get('dire_score', 0)
                }
    
    if 'matches' in live_cache:
        for match_id, match_data in live_cache['matches'].items():
            status = match_data.get('status', 'unknown')
            winner = match_data.get('winner', None)
            radiant_win = match_data.get('radiant_win', None)
            game_state = match_data.get('game_state', None)
            
            active_matches[match_id] = {
                'status': status,
                'status_tag': match_data.get('status_tag', ''),
                'winner': winner,
                'radiant_win': radiant_win,
                'game_state': game_state,
                'series_id': match_data.get('series_id', None),
                'needs_enrichment': (status == 'finished' and not winner and not isinstance(radiant_win, bool))
            }
    
    logger.info(f"Séries actives: {len(active_series)}")
    for series_id, series_data in active_series.items():
        logger.info(f"  - Série {series_id}: {len(series_data['match_ids'])} matchs, score {series_data['radiant_score']}-{series_data['dire_score']}")
    
    logger.info(f"Matchs actifs: {len(active_matches)}")
    for match_id, match_data in active_matches.items():
        status_info = f"status={match_data['status']}, tag={match_data['status_tag']}"
        winner_info = f"winner={match_data['winner']}, radiant_win={match_data['radiant_win']}, game_state={match_data['game_state']}"
        enrichment = "BESOIN D'ENRICHISSEMENT" if match_data['needs_enrichment'] else "OK"
        
        logger.info(f"  - Match {match_id}: {status_info}, {winner_info}, série={match_data['series_id']}, {enrichment}")

def main():
    """Fonction principale du script"""
    logger.info("Démarrage du script d'harmonisation des champs d'état")
    
    # 1. Harmoniser les caches
    live_updated = harmonize_live_cache()
    historical_updated = harmonize_historical_data()
    
    # 2. Mettre à jour les statuts pour l'enrichissement
    enrichment_updated = update_status_for_match_enrichment()
    
    # 3. Analyser l'état actuel des matchs et séries
    get_active_series_and_matches()
    
    logger.info("Script terminé")

if __name__ == "__main__":
    main()
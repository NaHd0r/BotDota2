"""
Script pour corriger la cohérence des statuts dans les caches

Ce script permet de corriger les problèmes de cohérence entre les statuts
en français et en anglais pour s'assurer que l'enrichissement
fonctionne correctement.
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

def update_status_fields() -> bool:
    """
    Met à jour tous les champs de statut pour assurer la cohérence
    """
    # Charger les caches
    live_cache = load_cache(LIVE_CACHE_FILE)
    historical_data = load_cache(HISTORICAL_DATA_FILE)
    
    updated = False
    
    # 1. Mettre à jour les matchs dans le cache live
    if 'matches' in live_cache:
        for match_id, match_data in live_cache['matches'].items():
            # Normaliser le statut
            if 'status' in match_data:
                if match_data['status'] in ['terminé', 'TERMINÉ', 'terminée', 'TERMINÉE', 'fini', 'FINI']:
                    match_data['status'] = 'finished'
                    updated = True
                    logger.info(f"Match {match_id}: status mis à jour à 'finished'")
                elif match_data['status'] in ['en cours', 'en_cours', 'in_progress']:
                    match_data['status'] = 'game'
                    updated = True
                    logger.info(f"Match {match_id}: status mis à jour à 'game'")
            
            # Normaliser le status_tag
            if 'status_tag' in match_data:
                if match_data['status_tag'] in ['TERMINÉ', 'TERMINÉE', 'FINI', 'FINIE', 'terminé', 'terminée']:
                    match_data['status_tag'] = 'FINISHED'
                    updated = True
                    logger.info(f"Match {match_id}: status_tag mis à jour à 'FINISHED'")
                elif match_data['status_tag'] in ['EN COURS', 'IN PROGRESS']:
                    match_data['status_tag'] = 'GAME'
                    updated = True
                    logger.info(f"Match {match_id}: status_tag mis à jour à 'GAME'")
    
    # 2. Mettre à jour les matchs dans les données historiques
    if 'matches' in historical_data:
        for match_id, match_data in historical_data['matches'].items():
            # Normaliser le statut au niveau supérieur
            if 'status' in match_data:
                if match_data['status'] in ['terminé', 'TERMINÉ', 'terminée', 'TERMINÉE', 'fini', 'FINI']:
                    match_data['status'] = 'finished'
                    updated = True
                    logger.info(f"Historical match {match_id}: status mis à jour à 'finished'")
                elif match_data['status'] in ['en cours', 'en_cours', 'in_progress']:
                    match_data['status'] = 'game'
                    updated = True
                    logger.info(f"Historical match {match_id}: status mis à jour à 'game'")
            
            # Normaliser le status_tag au niveau supérieur
            if 'status_tag' in match_data:
                if match_data['status_tag'] in ['TERMINÉ', 'TERMINÉE', 'FINI', 'FINIE', 'terminé', 'terminée']:
                    match_data['status_tag'] = 'FINISHED'
                    updated = True
                    logger.info(f"Historical match {match_id}: status_tag mis à jour à 'FINISHED'")
                elif match_data['status_tag'] in ['EN COURS']:
                    match_data['status_tag'] = 'IN PROGRESS'
                    updated = True
                    logger.info(f"Historical match {match_id}: status_tag mis à jour à 'IN PROGRESS'")
            
            # Si les données du match sont dans un sous-champ "data"
            if 'data' in match_data and isinstance(match_data['data'], dict):
                match_info = match_data['data']
                
                # Normaliser le statut dans data
                if 'status' in match_info:
                    if match_info['status'] in ['terminé', 'TERMINÉ', 'terminée', 'TERMINÉE', 'fini', 'FINI']:
                        match_info['status'] = 'finished'
                        updated = True
                        logger.info(f"Historical match {match_id} data: status mis à jour à 'finished'")
                    elif match_info['status'] in ['en cours', 'en_cours', 'in_progress']:
                        match_info['status'] = 'game'
                        updated = True
                        logger.info(f"Historical match {match_id} data: status mis à jour à 'game'")
                
                # Normaliser le status_tag dans data
                if 'status_tag' in match_info:
                    if match_info['status_tag'] in ['TERMINÉ', 'TERMINÉE', 'FINI', 'FINIE', 'terminé', 'terminée']:
                        match_info['status_tag'] = 'FINISHED'
                        updated = True
                        logger.info(f"Historical match {match_id} data: status_tag mis à jour à 'FINISHED'")
                    elif match_info['status_tag'] in ['EN COURS']:
                        match_info['status_tag'] = 'IN PROGRESS'
                        updated = True
                        logger.info(f"Historical match {match_id} data: status_tag mis à jour à 'IN PROGRESS'")
    
    # Sauvegarder les caches mis à jour
    if updated:
        save_cache(LIVE_CACHE_FILE, live_cache)
        save_cache(HISTORICAL_DATA_FILE, historical_data)
        logger.info("Champs de statut mis à jour avec succès")
    else:
        logger.info("Aucune mise à jour nécessaire pour les champs de statut")
    
    return updated

def add_finished_status_to_completed_games() -> bool:
    """
    Ajoute le statut 'finished' aux matchs terminés qui n'ont pas de statut
    """
    # Charger les caches
    live_cache = load_cache(LIVE_CACHE_FILE)
    historical_data = load_cache(HISTORICAL_DATA_FILE)
    
    updated = False
    
    # 1. Vérifier les matchs dans le cache live
    if 'matches' in live_cache:
        for match_id, match_data in live_cache['matches'].items():
            # Détecter si le match est terminé
            is_finished = False
            
            # Si le match a un vainqueur
            if 'winner' in match_data and match_data['winner'] in ['radiant', 'dire']:
                is_finished = True
            
            # Si le match a radiant_win défini
            if 'radiant_win' in match_data and match_data['radiant_win'] is not None:
                is_finished = True
            
            # Si le match a game_state indiquant une fin
            if 'game_state' in match_data:
                if isinstance(match_data['game_state'], int) and match_data['game_state'] in [2, 3]:
                    is_finished = True
                elif isinstance(match_data['game_state'], str) and match_data['game_state'] in ['radiant_win', 'dire_win']:
                    is_finished = True
            
            # Appliquer le statut fini si détecté
            if is_finished:
                if 'status' not in match_data or match_data['status'] != 'finished':
                    match_data['status'] = 'finished'
                    updated = True
                    logger.info(f"Match {match_id}: status forcé à 'finished'")
                
                if 'status_tag' not in match_data or match_data['status_tag'] != 'FINISHED':
                    match_data['status_tag'] = 'FINISHED'
                    updated = True
                    logger.info(f"Match {match_id}: status_tag forcé à 'FINISHED'")
    
    # 2. Vérifier les matchs dans les données historiques (moins critique)
    if 'matches' in historical_data:
        for match_id, match_data in historical_data['matches'].items():
            # Si le match est dans l'historique, il est probablement terminé
            if 'status' not in match_data or match_data['status'] != 'finished':
                match_data['status'] = 'finished'
                updated = True
                logger.info(f"Historical match {match_id}: status forcé à 'finished'")
            
            if 'status_tag' not in match_data or match_data['status_tag'] != 'FINISHED':
                match_data['status_tag'] = 'FINISHED'
                updated = True
                logger.info(f"Historical match {match_id}: status_tag forcé à 'FINISHED'")
            
            # Mettre à jour également dans le sous-niveau data si présent
            if 'data' in match_data and isinstance(match_data['data'], dict):
                if 'status' not in match_data['data'] or match_data['data']['status'] != 'finished':
                    match_data['data']['status'] = 'finished'
                    updated = True
                    logger.info(f"Historical match {match_id} data: status forcé à 'finished'")
                
                if 'status_tag' not in match_data['data'] or match_data['data']['status_tag'] != 'FINISHED':
                    match_data['data']['status_tag'] = 'FINISHED'
                    updated = True
                    logger.info(f"Historical match {match_id} data: status_tag forcé à 'FINISHED'")
    
    # Sauvegarder les caches mis à jour
    if updated:
        save_cache(LIVE_CACHE_FILE, live_cache)
        save_cache(HISTORICAL_DATA_FILE, historical_data)
        logger.info("Statuts 'finished' ajoutés aux matchs terminés avec succès")
    else:
        logger.info("Aucun ajout de statut 'finished' nécessaire")
    
    return updated

def update_ongoing_match_status() -> bool:
    """
    Met à jour les statuts des matchs en cours pour assurer la cohérence
    """
    # Charger le cache live
    live_cache = load_cache(LIVE_CACHE_FILE)
    updated = False
    
    if 'matches' in live_cache:
        for match_id, match_data in live_cache['matches'].items():
            # Si le match a une durée, mais pas de vainqueur et pas de status terminé
            if ('duration' in match_data and match_data['duration'] and
                ('winner' not in match_data or not match_data['winner']) and
                ('status' not in match_data or match_data['status'] != 'finished')):
                
                match_data['status'] = 'game'
                match_data['status_tag'] = 'GAME'
                updated = True
                logger.info(f"Match {match_id}: status mis à jour à 'game' (match en cours avec durée)")
    
    # Sauvegarder le cache mis à jour
    if updated:
        save_cache(LIVE_CACHE_FILE, live_cache)
        logger.info("Statuts des matchs en cours mis à jour avec succès")
    else:
        logger.info("Aucune mise à jour nécessaire pour les statuts des matchs en cours")
    
    return updated

def main():
    """Fonction principale du script"""
    logger.info("Démarrage du script de correction de la cohérence des statuts")
    
    # 1. Mettre à jour tous les champs de statut
    update_status_fields()
    
    # 2. Ajouter le statut 'finished' aux matchs terminés
    add_finished_status_to_completed_games()
    
    # 3. Mettre à jour les statuts des matchs en cours
    update_ongoing_match_status()
    
    logger.info("Script terminé")

if __name__ == "__main__":
    main()
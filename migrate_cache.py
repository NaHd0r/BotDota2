"""
Script de migration pour convertir l'ancien système de cache vers le nouveau système unifié.

Ce script lit les données des anciens fichiers de cache et les convertit au
nouveau format utilisé par dual_cache_system.py.
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import du nouveau système de cache
import dual_cache_system as cache

# Anciens chemins de fichiers
CACHE_DIR = "cache"
LIVE_SERIES_CACHE = os.path.join(CACHE_DIR, "live_series_cache.json")
SERIES_CACHE = os.path.join(CACHE_DIR, "series_cache.json")
COMPLETED_SERIES_CACHE = os.path.join(CACHE_DIR, "completed_series_cache.json")
SERIES_MATCHES_MAPPING = os.path.join(CACHE_DIR, "series_matches_mapping.json")
MATCH_DATA_CACHE = os.path.join(CACHE_DIR, "match_data_cache.json")

def load_old_cache(file_path: str) -> Any:
    """
    Charge un ancien fichier de cache si existant
    
    Args:
        file_path (str): Chemin du fichier à charger
        
    Returns:
        Any: Données du cache, ou structure vide appropriée si le fichier n'existe pas
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Chargé {file_path}")
                return data
        else:
            logger.warning(f"Fichier non trouvé: {file_path}")
            # Retourner une structure appropriée selon le type de fichier
            if file_path.endswith("match_data_cache.json"):
                return {}
            elif file_path.endswith("series_matches_mapping.json"):
                return {}
            elif file_path.endswith("live_series_cache.json"):
                return {}
            else:
                return []
    except Exception as e:
        logger.error(f"Erreur lors du chargement de {file_path}: {e}")
        return {} if file_path.endswith(".json") else []

def backup_old_files():
    """
    Crée une sauvegarde des anciens fichiers de cache avant la migration
    """
    backup_dir = "cache_backup"
    
    # Créer le répertoire de sauvegarde s'il n'existe pas
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        logger.info(f"Répertoire de sauvegarde créé: {backup_dir}")
    
    # Liste des fichiers à sauvegarder
    files_to_backup = [
        LIVE_SERIES_CACHE,
        SERIES_CACHE,
        COMPLETED_SERIES_CACHE,
        SERIES_MATCHES_MAPPING,
        MATCH_DATA_CACHE
    ]
    
    # Sauvegarder chaque fichier s'il existe
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            timestamp = int(time.time())
            backup_name = os.path.join(backup_dir, f"{os.path.basename(file_path)}.{timestamp}.bak")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as src:
                    with open(backup_name, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                logger.info(f"Sauvegarde créée: {backup_name}")
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde de {file_path}: {e}")

def migrate_live_series():
    """
    Migre les données des séries en direct vers le nouveau système
    """
    # Charger l'ancien cache des séries en direct
    old_live_series = load_old_cache(LIVE_SERIES_CACHE)
    
    # Préparer les nouvelles données
    live_data = cache.load_live_data()
    
    # Parcourir chaque série en direct et la convertir au nouveau format
    for series_id, series_data in old_live_series.items():
        # Normaliser l'ID de série (s'assurer qu'il commence par 's_')
        normalized_series_id = series_id
        if not normalized_series_id.startswith('s_'):
            normalized_series_id = 's_' + normalized_series_id
        
        # Extraire les informations de base de la série
        series_type = series_data.get('series_type', 1)
        radiant_score = series_data.get('radiant_score', 0)
        dire_score = series_data.get('dire_score', 0)
        
        # Créer l'entrée de série dans le nouveau format
        new_series_data = {
            'series_id': normalized_series_id,
            'series_type': series_type,
            'radiant_score': radiant_score,
            'dire_score': dire_score,
            'match_ids': [],
            'last_updated': int(time.time())
        }
        
        # Ajouter les matchs associés à cette série
        # Gestion des deux formats possibles de 'matches': dictionnaire ou liste
        matches_data = series_data.get('matches', {})
        
        # Pour les matchs stockés sous forme de dictionnaire
        if isinstance(matches_data, dict):
            for match_id, match_data in matches_data.items():
                if match_id:
                    match_id = str(match_id)
                    
                    # Ajouter le match à la liste des matchs de la série
                    if match_id not in new_series_data['match_ids']:
                        new_series_data['match_ids'].append(match_id)
                    
                    # Ajouter les données du match au cache
                    if match_data:
                        # Vérifier que les données du match sont complètes
                        match_data['match_id'] = match_id
                        match_data['timestamp'] = match_data.get('timestamp', time.strftime('%H:%M:%S'))
                        
                        # Ajouter le match au cache
                        live_data['matches'][match_id] = match_data
        
        # Pour les matchs stockés sous forme de liste
        elif isinstance(matches_data, list):
            for match_item in matches_data:
                # Si c'est un dictionnaire complet de données de match
                if isinstance(match_item, dict) and 'match_id' in match_item:
                    match_id = str(match_item['match_id'])
                    
                    # Ajouter le match à la liste des matchs de la série
                    if match_id not in new_series_data['match_ids']:
                        new_series_data['match_ids'].append(match_id)
                    
                    # Ajouter le match au cache
                    match_item['timestamp'] = match_item.get('timestamp', time.strftime('%H:%M:%S'))
                    live_data['matches'][match_id] = match_item
                
                # Si c'est juste un ID de match
                elif isinstance(match_item, (str, int)):
                    match_id = str(match_item)
                    
                    # Ajouter le match à la liste des matchs de la série
                    if match_id not in new_series_data['match_ids']:
                        new_series_data['match_ids'].append(match_id)
                        
        # Le match actuel de la série
        current_match = series_data.get('current_match')
        if current_match and isinstance(current_match, dict) and 'match_id' in current_match:
            match_id = str(current_match['match_id'])
            
            # Ajouter le match à la liste des matchs de la série
            if match_id not in new_series_data['match_ids']:
                new_series_data['match_ids'].append(match_id)
            
            # Ajouter le match au cache
            current_match['timestamp'] = current_match.get('timestamp', time.strftime('%H:%M:%S'))
            live_data['matches'][match_id] = current_match
        
        # Ajouter la série au cache
        live_data['series'][normalized_series_id] = new_series_data
    
    # Sauvegarder les données migrées
    cache.save_live_data(live_data)
    logger.info(f"Migration des séries en direct terminée, {len(live_data['series'])} séries migrées")

def migrate_series_matches_mapping():
    """
    Migre les données du mapping séries-matchs vers le nouveau système
    """
    # Charger l'ancien mapping
    old_mapping = load_old_cache(SERIES_MATCHES_MAPPING)
    
    # Charger les données historiques existantes
    historical_data = cache.load_historical_data()
    
    # Parcourir chaque série dans le mapping
    for series_id, matches_info in old_mapping.items():
        # Normaliser l'ID de série
        normalized_series_id = series_id
        if not normalized_series_id.startswith('s_'):
            normalized_series_id = 's_' + normalized_series_id
        
        # Extraire les informations de la série
        if isinstance(matches_info, dict):
            # Format avancé avec informations supplémentaires
            match_ids = matches_info.get('match_ids', [])
            radiant_score = matches_info.get('radiant_score', 0)
            dire_score = matches_info.get('dire_score', 0)
            series_type = matches_info.get('series_type', 1)
        elif isinstance(matches_info, list):
            # Format simple: liste d'IDs de matchs
            match_ids = matches_info
            radiant_score = 0
            dire_score = 0
            series_type = 1  # Default: Bo3
        else:
            logger.warning(f"Format invalide pour la série {series_id}, ignorée")
            continue
        
        # Créer l'entrée de série dans le nouveau format
        new_series_data = {
            'series_id': normalized_series_id,
            'series_type': series_type,
            'radiant_score': radiant_score,
            'dire_score': dire_score,
            'match_ids': [str(mid) for mid in match_ids],
            'last_updated': int(time.time()),
            'historical': True
        }
        
        # Ajouter la série au cache historique
        historical_data['series'][normalized_series_id] = new_series_data
    
    # Sauvegarder les données migrées
    cache.save_historical_data(historical_data)
    logger.info(f"Migration du mapping séries-matchs terminée, {len(historical_data['series'])} séries migrées")

def migrate_match_data():
    """
    Migre les données des matchs vers le nouveau système
    """
    # Charger l'ancien cache de données de matchs
    old_match_data = load_old_cache(MATCH_DATA_CACHE)
    
    # Charger les données historiques existantes
    historical_data = cache.load_historical_data()
    
    # Parcourir chaque match dans l'ancien cache
    for match_id, match_data in old_match_data.items():
        if not match_data:
            continue
        
        # Normaliser l'ID de match
        match_id = str(match_id)
        
        # Marquer le match comme historique
        match_data['match_id'] = match_id
        match_data['historical'] = True
        match_data['status'] = match_data.get('status', 'finished')
        match_data['status_tag'] = match_data.get('status_tag', 'TERMINÉ')
        
        # Ajouter le match au cache historique
        historical_data['matches'][match_id] = match_data
    
    # Sauvegarder les données migrées
    cache.save_historical_data(historical_data)
    logger.info(f"Migration des données de matchs terminée, {len(historical_data['matches'])} matchs migrés")

def main():
    """
    Fonction principale pour exécuter la migration complète
    """
    logger.info("Démarrage de la migration du cache...")
    
    # Créer des sauvegardes des anciens fichiers
    logger.info("Création des sauvegardes...")
    backup_old_files()
    
    # Migrer chaque type de données
    try:
        # Migrer les séries en direct
        logger.info("Migration des séries en direct...")
        migrate_live_series()
        
        # Migrer le mapping séries-matchs
        logger.info("Migration du mapping séries-matchs...")
        migrate_series_matches_mapping()
        
        # Migrer les données des matchs
        logger.info("Migration des données des matchs...")
        migrate_match_data()
        
        logger.info("Migration terminée avec succès!")
    except Exception as e:
        logger.error(f"Erreur lors de la migration: {e}")
        raise

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour insérer directement les données du match 8257802931 dans le cache live.
C'est une solution temporaire pour résoudre un problème d'affichage.
"""

import os
import json
import logging

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fichiers de cache
CACHE_DIR = "cache"
LIVE_CACHE_FILE = os.path.join(CACHE_DIR, "live_series_cache.json")
MATCH_DATA_CACHE_FILE = os.path.join(CACHE_DIR, "match_data_cache.json")

def load_cache(file_path):
    """Charge un fichier de cache JSON"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du cache {file_path}: {str(e)}")
        return {}

def save_cache(file_path, data):
    """Sauvegarde un fichier de cache JSON"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache {file_path}: {str(e)}")
        return False

def fix_match_in_live_cache():
    """Insère directement les données du match 8257802931 dans le cache live"""
    # Charger les caches
    live_cache = load_cache(LIVE_CACHE_FILE)
    match_cache = load_cache(MATCH_DATA_CACHE_FILE)
    
    # Vérifier que les données du match existent
    match_key = "match_8257802931"
    if match_key not in match_cache:
        logger.error(f"Le match {match_key} n'est pas dans le cache match_data_cache.json")
        return False
    
    # Récupérer les données du match
    match_data = match_cache[match_key].get('data', {})
    if not match_data:
        logger.error(f"Données du match {match_key} vides ou invalides")
        return False
    
    # Créer une nouvelle série avec le match
    series_id = "8257802931"  # Utiliser l'ID du match comme ID de série
    league_id = match_data.get('league_id', '17911')
    radiant_score = match_data.get('radiant_score', 0)
    dire_score = match_data.get('dire_score', 0)
    
    # Préparer les données du match pour le cache live
    formatted_match = {
        'match_id': "8257802931",
        'league_id': league_id,
        'radiant_team_id': "",
        'dire_team_id': "",
        'radiant_team_name': match_data.get('radiant_team', {}).get('name', "Équipe Radiant"),
        'dire_team_name': match_data.get('dire_team', {}).get('name', "Équipe Dire"),
        'radiant_score': radiant_score,
        'dire_score': dire_score,
        'total_kills': radiant_score + dire_score,
        'duration': match_data.get('duration', "42:02"),
        'duration_formatted': match_data.get('duration', "42:02"),
        'radiant_networth': 0,
        'dire_networth': 0,
        'networth_difference': 0,
        'draft_phase': False,
        'match_outcome': 1 if match_data.get('winner') == 'radiant' else 2,  # 1=Radiant win, 2=Dire win
        'game_number': 1,
        'timestamp': match_data.get('timestamp', 1744878990),
        'match_state': {
            'phase': 'finished',
            'winner': match_data.get('winner', 'radiant')
        }
    }
    
    # Créer ou mettre à jour la série dans le cache live
    if series_id not in live_cache:
        live_cache[series_id] = {
            'series_id': series_id,
            'radiant_id': "",
            'dire_id': "",
            'league_id': league_id,
            'radiant_score': 1 if match_data.get('winner') == 'radiant' else 0,
            'dire_score': 0 if match_data.get('winner') == 'radiant' else 1,
            'matches': {},
            'last_update_time': 1744878990,
            'created_at': 1744878990
        }
    
    # Ajouter le match à la série
    live_cache[series_id]['matches'][formatted_match['match_id']] = formatted_match
    
    # Sauvegarder le cache mis à jour
    logger.info(f"Insertion du match {formatted_match['match_id']} dans la série {series_id}")
    if save_cache(LIVE_CACHE_FILE, live_cache):
        logger.info(f"Cache live mis à jour avec succès")
        return True
    else:
        logger.error(f"Échec de la mise à jour du cache live")
        return False

if __name__ == "__main__":
    if fix_match_in_live_cache():
        print("Le match 8257802931 a été ajouté au cache live.")
    else:
        print("Erreur lors de l'ajout du match 8257802931 au cache live.")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour enrichir automatiquement un match terminé avec les données d'OpenDota
et l'insérer dans le cache live pour qu'il soit correctement affiché dans le frontend.

Ce script est conçu pour être exécuté après la fin d'un match afin de maintenir
les données affichées dans le frontend même lorsque le match n'est plus en cours.
"""

import os
import sys
import json
import time
import logging
import requests
from browser_simulator import fetch_opendota_match

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

def fetch_match_from_opendota(match_id, max_tries=3, retry_delay=30):
    """
    Récupère les données d'un match depuis l'API OpenDota
    
    Args:
        match_id: ID du match à récupérer
        max_tries: Nombre maximum de tentatives
        retry_delay: Délai entre les tentatives en secondes
        
    Returns:
        Données du match ou None en cas d'échec
    """
    logger.info(f"Récupération des données du match {match_id} depuis OpenDota")
    
    for attempt in range(max_tries):
        try:
            match_data = fetch_opendota_match(match_id)
            if match_data:
                logger.info(f"Données du match {match_id} récupérées avec succès")
                return match_data
            else:
                logger.warning(f"Tentative {attempt+1}/{max_tries}: Aucune donnée récupérée pour le match {match_id}")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du match {match_id}: {str(e)}")
        
        if attempt < max_tries - 1:
            logger.info(f"Nouvelle tentative dans {retry_delay} secondes...")
            time.sleep(retry_delay)
    
    logger.error(f"Impossible de récupérer les données du match {match_id} après {max_tries} tentatives")
    return None

def format_match_for_live_cache(match_id, match_data):
    """
    Formate les données d'un match pour le cache live
    
    Args:
        match_id: ID du match
        match_data: Données du match depuis OpenDota
        
    Returns:
        Dictionnaire formaté pour le cache live
    """
    # Extraire les données essentielles
    radiant_team_name = match_data.get('radiant_team', {}).get('name', "Équipe Radiant")
    dire_team_name = match_data.get('dire_team', {}).get('name', "Équipe Dire")
    league_id = str(match_data.get('league', {}).get('leagueid', match_data.get('leagueid', '17911')))
    radiant_win = match_data.get('radiant_win', False)
    
    # Calculer les scores
    radiant_score = 0
    dire_score = 0
    total_kills = 0
    
    if 'radiant_score' in match_data and 'dire_score' in match_data:
        radiant_score = match_data['radiant_score']
        dire_score = match_data['dire_score']
        total_kills = radiant_score + dire_score
    else:
        # Compter les kills manuellement si les scores ne sont pas disponibles
        for player in match_data.get('players', []):
            if player.get('player_slot', 0) < 128:  # Joueurs Radiant
                radiant_score += player.get('kills', 0)
            else:  # Joueurs Dire
                dire_score += player.get('kills', 0)
        total_kills = radiant_score + dire_score
    
    # Calculer la durée
    duration_seconds = match_data.get('duration', 0)
    minutes = duration_seconds // 60
    seconds = duration_seconds % 60
    duration_formatted = f"{minutes}:{seconds:02d}"
    
    # Créer l'objet formaté pour le cache live
    formatted_match = {
        'match_id': str(match_id),
        'league_id': league_id,
        'radiant_team_id': match_data.get('radiant_team', {}).get('team_id', ""),
        'dire_team_id': match_data.get('dire_team', {}).get('team_id', ""),
        'radiant_team_name': radiant_team_name,
        'dire_team_name': dire_team_name,
        'radiant_score': radiant_score,
        'dire_score': dire_score,
        'total_kills': total_kills,
        'duration': duration_formatted,
        'duration_formatted': duration_formatted,
        'radiant_networth': 0,
        'dire_networth': 0,
        'networth_difference': 0,
        'draft_phase': False,
        'match_outcome': 1 if radiant_win else 2,  # 1=Radiant win, 2=Dire win
        'game_number': 1,
        'timestamp': int(time.time()),
        'match_state': {
            'phase': 'finished',
            'winner': 'radiant' if radiant_win else 'dire'
        }
    }
    
    return formatted_match

def enrich_match_in_live_cache(match_id):
    """
    Récupère les données d'un match depuis OpenDota et les insère dans le cache live
    
    Args:
        match_id: ID du match à enrichir
        
    Returns:
        Boolean indiquant si l'enrichissement a réussi
    """
    # Charger les caches
    live_cache = load_cache(LIVE_CACHE_FILE)
    match_cache = load_cache(MATCH_DATA_CACHE_FILE)
    
    # Vérifier si les données sont déjà en cache
    match_key = f"match_{match_id}"
    match_data = None
    
    if match_key in match_cache:
        logger.info(f"Données du match {match_id} trouvées dans le cache")
        match_data = match_cache[match_key].get('data', {})
    
    # Si les données ne sont pas en cache, les récupérer depuis OpenDota
    if not match_data:
        match_data = fetch_match_from_opendota(match_id)
        if match_data:
            # Sauvegarder les données dans le cache
            match_cache[match_key] = {
                'timestamp': int(time.time()),
                'data': match_data
            }
            save_cache(MATCH_DATA_CACHE_FILE, match_cache)
            logger.info(f"Données du match {match_id} ajoutées au cache")
        else:
            logger.error(f"Impossible de récupérer les données du match {match_id}")
            return False
    
    # Formater les données pour le cache live
    formatted_match = format_match_for_live_cache(match_id, match_data)
    
    # Créer ou mettre à jour la série dans le cache live
    series_id = f"s_{str(match_id)}"  # Utiliser le préfixe s_ avec l'ID du match comme ID de série
    if series_id not in live_cache:
        live_cache[series_id] = {
            'series_id': series_id,
            'radiant_id': formatted_match['radiant_team_id'],
            'dire_id': formatted_match['dire_team_id'],
            'league_id': formatted_match['league_id'],
            'radiant_score': 1 if formatted_match['match_outcome'] == 1 else 0,
            'dire_score': 0 if formatted_match['match_outcome'] == 1 else 1,
            'matches': {},
            'last_update_time': int(time.time()),
            'created_at': int(time.time())
        }
    
    # Ajouter le match à la série
    live_cache[series_id]['matches'][formatted_match['match_id']] = formatted_match
    
    # Sauvegarder le cache mis à jour
    logger.info(f"Insertion du match {match_id} dans la série {series_id}")
    if save_cache(LIVE_CACHE_FILE, live_cache):
        logger.info(f"Cache live mis à jour avec succès")
        return True
    else:
        logger.error(f"Échec de la mise à jour du cache live")
        return False

def enrich_live_match(match_id, check_game_state=False):
    """
    Fonction principale pour enrichir un match avec les données OpenDota
    Cette fonction est appelée par d'autres modules comme auto_enrich_matches.py
    
    Cette fonction gère également la transition d'état "draft" à "game" quand
    check_game_state=True en vérifiant l'état à 10 et 20 secondes après le début du match.
    
    Args:
        match_id (str): ID du match à enrichir
        check_game_state (bool): Si True, vérifie l'état du match pour transition draft -> game
        
    Returns:
        bool: True si l'enrichissement ou le changement d'état a réussi, False sinon
    """
    try:
        # Charger le cache pour vérifier l'état actuel
        live_cache = load_cache(LIVE_CACHE_FILE)
        
        # Si on vérifie le changement d'état (pour les matchs en début de partie)
        if check_game_state:
            # Récupérer le match depuis le cache
            match_data = None
            if match_id in live_cache and isinstance(live_cache[match_id], dict):
                match_data = live_cache[match_id]
            elif any(match_id in series.get('matches', {}) for series in live_cache.values() if isinstance(series, dict)):
                # Recherche dans les séries
                for series in live_cache.values():
                    if isinstance(series, dict) and 'matches' in series and match_id in series['matches']:
                        match_data = series['matches'][match_id]
                        break
            
            if match_data:
                # Vérifier si le match est en phase "draft"
                is_draft = match_data.get('status') == 'draft' or match_data.get('status_tag') == 'DRAFT'
                
                if is_draft:
                    # Récupérer les données à jour depuis OpenDota
                    opendota_data = fetch_opendota_match(match_id)
                    if opendota_data:
                        # Si le match a commencé (durée > 0)
                        if opendota_data.get('duration', 0) > 0:
                            # Mettre à jour l'état du match à "game"
                            match_data['status'] = 'active'
                            match_data['status_tag'] = 'EN JEU'
                            match_data['match_phase'] = 'game'
                            logger.info(f"Transition détectée: Match {match_id} passé de DRAFT à EN JEU via OpenDota")
                            
                            # Sauvegarder le cache
                            save_cache(LIVE_CACHE_FILE, live_cache)
                            return True
            
        # Procéder à l'enrichissement normal
        return enrich_match_in_live_cache(match_id)
    except Exception as e:
        logger.error(f"Erreur lors de l'enrichissement/vérification du match {match_id}: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python enrich_live_match.py <match_id>")
        sys.exit(1)
    
    match_id = sys.argv[1]
    if enrich_live_match(match_id):
        print(f"Le match {match_id} a été enrichi et ajouté au cache live.")
    else:
        print(f"Erreur lors de l'enrichissement du match {match_id}.")
"""
Script pour trouver les matchs précédents d'une série en utilisant l'API OpenDota.

Ce script permet de rechercher automatiquement les matchs précédents d'une série en cours
en se basant sur les identifiants des équipes et des joueurs. Il utilise l'API OpenDota
pour récupérer l'historique récent des matchs et les associe à la série actuelle.
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple

# Importer les modules nécessaires
import opendota_api
from api_field_mapping import format_duration, prepare_match_for_previous_matches

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

def get_match_from_cache(match_id: str) -> Optional[Dict[str, Any]]:
    """
    Récupère les données d'un match depuis les caches (live ou historique)
    
    Args:
        match_id (str): ID du match à récupérer
        
    Returns:
        dict: Données du match ou None si non trouvé
    """
    # Essayer d'abord dans le cache live
    live_cache = load_cache(LIVE_CACHE_FILE)
    if 'matches' in live_cache and match_id in live_cache['matches']:
        return live_cache['matches'][match_id]
    
    # Ensuite dans les données historiques
    historical_data = load_cache(HISTORICAL_DATA_FILE)
    match_key = f"match_{match_id}" if not match_id.startswith("match_") else match_id
    if 'matches' in historical_data and match_key in historical_data['matches']:
        return historical_data['matches'][match_key]
    
    return None

def get_current_series_data(series_id: str) -> Optional[Dict[str, Any]]:
    """
    Récupère les données d'une série depuis le cache
    
    Args:
        series_id (str): ID de la série à récupérer
        
    Returns:
        dict: Données de la série ou None si non trouvée
    """
    live_cache = load_cache(LIVE_CACHE_FILE)
    if 'series' in live_cache and series_id in live_cache['series']:
        return live_cache['series'][series_id]
    
    return None

def get_team_players(match_data: Dict[str, Any]) -> Tuple[Set[str], Set[str], str, str]:
    """
    Extrait les IDs des joueurs et les noms des équipes d'un match
    
    Args:
        match_data (dict): Données du match
        
    Returns:
        tuple: (radiant_player_ids, dire_player_ids, radiant_team_name, dire_team_name)
    """
    radiant_player_ids = set()
    dire_player_ids = set()
    
    radiant_team_name = match_data.get('radiant_team', {}).get('team_name', 'Équipe Radiant')
    dire_team_name = match_data.get('dire_team', {}).get('team_name', 'Équipe Dire')
    
    # Extraire les IDs des joueurs Radiant
    radiant_players = match_data.get('radiant_team', {}).get('players', {})
    for player_id, player_data in radiant_players.items():
        if 'account_id' in player_data and player_data['account_id']:
            radiant_player_ids.add(str(player_data['account_id']))
    
    # Extraire les IDs des joueurs Dire
    dire_players = match_data.get('dire_team', {}).get('players', {})
    for player_id, player_data in dire_players.items():
        if 'account_id' in player_data and player_data['account_id']:
            dire_player_ids.add(str(player_data['account_id']))
    
    return radiant_player_ids, dire_player_ids, radiant_team_name, dire_team_name

def calculate_teams_similarity(players1: Set[str], players2: Set[str]) -> float:
    """
    Calcule le pourcentage de similarité entre deux ensembles de joueurs
    
    Args:
        players1 (set): Premier ensemble d'IDs de joueurs
        players2 (set): Deuxième ensemble d'IDs de joueurs
        
    Returns:
        float: Pourcentage de similarité (0-1)
    """
    if not players1 or not players2:
        return 0.0
    
    common_players = players1.intersection(players2)
    return len(common_players) / max(len(players1), len(players2))

def find_previous_matches_for_series(series_id: str, max_days_back: int = 2) -> List[Dict[str, Any]]:
    """
    Recherche les matchs précédents pour une série
    
    Args:
        series_id (str): ID de la série
        max_days_back (int): Nombre maximum de jours en arrière à chercher
        
    Returns:
        list: Liste des matchs précédents trouvés
    """
    series_data = get_current_series_data(series_id)
    if not series_data:
        logger.error(f"Série {series_id} non trouvée dans le cache")
        return []
    
    # Récupérer le premier match de la série (match actuel)
    match_ids = series_data.get('match_ids', [])
    if not match_ids:
        logger.error(f"Série {series_id} ne contient aucun match")
        return []
    
    current_match_id = match_ids[0]
    current_match_data = get_match_from_cache(current_match_id)
    if not current_match_data:
        logger.error(f"Match {current_match_id} non trouvé dans les caches")
        return []
    
    # Extraire les IDs des joueurs et les noms des équipes
    radiant_players, dire_players, radiant_team_name, dire_team_name = get_team_players(current_match_data)
    
    # Si nous n'avons pas assez de joueurs pour une comparaison fiable
    if len(radiant_players) < 3 or len(dire_players) < 3:
        logger.warning(f"Pas assez de joueurs identifiés dans le match {current_match_id}")
        return []
    
    logger.info(f"Recherche des matchs précédents pour la série {series_id}")
    logger.info(f"Équipe Radiant: {radiant_team_name} ({len(radiant_players)} joueurs)")
    logger.info(f"Équipe Dire: {dire_team_name} ({len(dire_players)} joueurs)")
    
    # Liste des matchs trouvés
    found_matches = []
    
    # Récupérer l'historique des matchs depuis OpenDota
    # Pour chaque joueur d'une équipe, vérifier s'il a joué récemment contre l'autre équipe
    sample_player_id = next(iter(radiant_players)) if radiant_players else None
    if not sample_player_id:
        logger.error("Aucun ID de joueur trouvé pour la recherche")
        return []
    
    try:
        # Récupérer l'historique des matchs récents pour un joueur de l'équipe Radiant
        recent_matches = opendota_api.get_player_recent_matches(sample_player_id)
        if not recent_matches:
            logger.warning(f"Aucun match récent trouvé pour le joueur {sample_player_id}")
            return []
        
        # Date limite pour la recherche (en jours)
        cutoff_date = datetime.now() - timedelta(days=max_days_back)
        cutoff_timestamp = int(cutoff_date.timestamp())
        
        # Filtrer par date et analyser chaque match
        for match in recent_matches:
            match_id_str = str(match.get('match_id', ''))
            start_time = match.get('start_time', 0)
            
            # Ignorer les matchs trop anciens
            if start_time < cutoff_timestamp:
                continue
            
            # Ignorer les matchs déjà dans la série
            if match_id_str in match_ids:
                continue
            
            # Récupérer les détails complets du match
            match_details = opendota_api.get_match_details(match_id_str)
            if not match_details:
                continue
            
            # Analyser les joueurs du match
            match_radiant_players = set()
            match_dire_players = set()
            
            for player in match_details.get('players', []):
                account_id = str(player.get('account_id', ''))
                if not account_id:
                    continue
                
                if player.get('isRadiant', True):
                    match_radiant_players.add(account_id)
                else:
                    match_dire_players.add(account_id)
            
            # Calculer la similarité avec les équipes de la série actuelle
            radiant_similarity1 = calculate_teams_similarity(radiant_players, match_radiant_players)
            dire_similarity1 = calculate_teams_similarity(dire_players, match_dire_players)
            
            # Vérifier si les équipes sont inversées
            radiant_similarity2 = calculate_teams_similarity(radiant_players, match_dire_players)
            dire_similarity2 = calculate_teams_similarity(dire_players, match_radiant_players)
            
            # Si bonne correspondance dans un sens ou l'autre
            if (radiant_similarity1 >= 0.6 and dire_similarity1 >= 0.6) or \
               (radiant_similarity2 >= 0.6 and dire_similarity2 >= 0.6):
                
                # Déterminer si les équipes sont dans le même ordre ou inversées
                teams_flipped = radiant_similarity2 > radiant_similarity1
                
                # Convertir les données au format interne
                match_data = opendota_api.convert_to_internal_format(match_details)
                
                # Adapter les noms des équipes si nécessaire
                if teams_flipped:
                    match_data['radiant_team_name'] = dire_team_name
                    match_data['dire_team_name'] = radiant_team_name
                else:
                    match_data['radiant_team_name'] = radiant_team_name
                    match_data['dire_team_name'] = dire_team_name
                
                # Déterminer le numéro du jeu (approximation basée sur l'heure)
                game_number = len(found_matches) + 1
                
                # Préparer les données pour le cache
                previous_match = prepare_match_for_previous_matches(match_data, game_number)
                
                found_matches.append(previous_match)
                logger.info(f"Match trouvé: {match_id_str} (Game {game_number})")
        
        # Trier par date (start_time) pour assurer l'ordre chronologique
        found_matches.sort(key=lambda m: m.get('timestamp', 0))
        
        # Renuméroter les games pour s'assurer qu'ils sont dans l'ordre
        for i, match in enumerate(found_matches):
            match['game_number'] = i + 1
        
        return found_matches
    
    except Exception as e:
        logger.error(f"Erreur lors de la recherche des matchs précédents: {e}")
        return []

def update_series_with_previous_matches(series_id: str, previous_matches: List[Dict[str, Any]]) -> bool:
    """
    Met à jour une série avec les matchs précédents trouvés
    
    Args:
        series_id (str): ID de la série à mettre à jour
        previous_matches (list): Liste des matchs précédents
        
    Returns:
        bool: True si la mise à jour a réussi, False sinon
    """
    if not previous_matches:
        logger.warning("Aucun match précédent à ajouter")
        return False
    
    try:
        # Charger le cache
        live_cache = load_cache(LIVE_CACHE_FILE)
        
        # Vérifier que la série existe
        if 'series' not in live_cache or series_id not in live_cache['series']:
            logger.error(f"Série {series_id} non trouvée dans le cache")
            return False
        
        # Récupérer la série
        series = live_cache['series'][series_id]
        
        # Mettre à jour la liste des match_ids de la série
        current_match_ids = series.get('match_ids', [])
        
        # Ajouter les nouveaux matchs à la liste des match_ids
        new_match_ids = [match['match_id'] for match in previous_matches if match['match_id'] not in current_match_ids]
        series['match_ids'] = new_match_ids + current_match_ids
        
        # Mettre à jour les scores de la série
        radiant_wins = sum(1 for match in previous_matches if match['winner'] == 'radiant')
        dire_wins = sum(1 for match in previous_matches if match['winner'] == 'dire')
        
        # Si nous avons déjà des scores, les ajouter aux nouveaux
        series['radiant_score'] = radiant_wins + series.get('radiant_score', 0)
        series['dire_score'] = dire_wins + series.get('dire_score', 0)
        
        # Ajouter ou mettre à jour la section previous_matches
        if 'previous_matches' not in series:
            series['previous_matches'] = []
        
        # Ajouter les nouveaux matchs aux matchs précédents
        # Éviter les doublons en vérifiant les match_id
        existing_match_ids = {match['match_id'] for match in series['previous_matches']}
        
        for match in previous_matches:
            if match['match_id'] not in existing_match_ids:
                series['previous_matches'].append(match)
                existing_match_ids.add(match['match_id'])
        
        # Trier les matchs précédents par numéro de jeu
        series['previous_matches'].sort(key=lambda m: m.get('game_number', 0))
        
        # Mettre à jour le timestamp
        series['last_updated'] = int(time.time())
        
        # Sauvegarder le cache
        if save_cache(LIVE_CACHE_FILE, live_cache):
            logger.info(f"Série {series_id} mise à jour avec {len(previous_matches)} matchs précédents")
            return True
        else:
            logger.error("Erreur lors de la sauvegarde du cache")
            return False
    
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la série {series_id}: {e}")
        return False

def update_series_mapping(series_id: str, match_ids: List[str]) -> bool:
    """
    Met à jour le mapping des séries
    
    Args:
        series_id (str): ID de la série
        match_ids (list): Liste des IDs de match à associer
        
    Returns:
        bool: True si la mise à jour a réussi, False sinon
    """
    try:
        # Charger le mapping
        mapping = load_cache(SERIES_MAPPING_FILE)
        
        # Initialiser si nécessaire
        if not mapping:
            mapping = {}
        
        # Mettre à jour le mapping
        if series_id not in mapping:
            mapping[series_id] = []
        
        # Ajouter les nouveaux match_ids
        for match_id in match_ids:
            if match_id not in mapping[series_id]:
                mapping[series_id].append(match_id)
        
        # Sauvegarder le mapping
        if save_cache(SERIES_MAPPING_FILE, mapping):
            logger.info(f"Mapping des séries mis à jour pour {series_id}")
            return True
        else:
            logger.error("Erreur lors de la sauvegarde du mapping des séries")
            return False
    
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du mapping des séries: {e}")
        return False

def main():
    """Fonction principale du script"""
    logger.info("Script de recherche des matchs précédents d'une série")
    
    # Si un ID de série est fourni en argument, l'utiliser
    if len(sys.argv) > 1:
        series_id = sys.argv[1]
    else:
        # Sinon, demander l'ID de la série
        series_id = input("Entrez l'ID de la série (ex: s_8261361161): ")
    
    # Limiter les recherches au premier match trouvé
    max_previous_matches = 1
    if len(sys.argv) > 2:
        try:
            max_previous_matches = int(sys.argv[2])
        except ValueError:
            pass
            
    # Trouver les matchs précédents
    previous_matches = find_previous_matches_for_series(series_id)
    
    # Ne garder que le nombre demandé (par défaut 1)
    if previous_matches and max_previous_matches > 0:
        logger.info(f"Limitant à {max_previous_matches} matchs précédents")
        previous_matches = previous_matches[:max_previous_matches]
    
    if previous_matches:
        logger.info(f"Nombre de matchs précédents trouvés: {len(previous_matches)}")
        
        # Mettre à jour la série
        update_series_with_previous_matches(series_id, previous_matches)
        
        # Mettre à jour le mapping des séries
        match_ids = [match['match_id'] for match in previous_matches]
        update_series_mapping(series_id, match_ids)
        
        logger.info("Opération terminée avec succès")
    else:
        logger.warning("Aucun match précédent trouvé pour cette série")
    
    logger.info("Script terminé")

if __name__ == "__main__":
    main()
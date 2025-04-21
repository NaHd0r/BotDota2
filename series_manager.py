"""
Module de gestion des séries de matchs Dota 2

Ce module implémente les fonctions pour générer les IDs de série, suivre les matchs
dans une série et déterminer la position d'un match dans une série en cours.
"""

import json
import logging
import os

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chemin du fichier de mapping des séries aux matchs
SERIES_MAPPING_FILE = 'cache/series_matches_mapping.json'

def load_series_mapping():
    """
    Charge le fichier de mapping des séries
    
    Returns:
        dict: Mapping des séries aux matchs
    """
    try:
        if os.path.exists(SERIES_MAPPING_FILE):
            with open(SERIES_MAPPING_FILE, 'r') as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du mapping des séries: {e}")
        return {}

def save_series_mapping(mapping):
    """
    Sauvegarde le mapping des séries
    
    Args:
        mapping (dict): Mapping à sauvegarder
    """
    try:
        os.makedirs(os.path.dirname(SERIES_MAPPING_FILE), exist_ok=True)
        with open(SERIES_MAPPING_FILE, 'w') as f:
            json.dump(mapping, f, indent=2)
        logger.info(f"Mapping des séries sauvegardé dans {SERIES_MAPPING_FILE}")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du mapping des séries: {e}")

def get_series_id(match_data):
    """
    Génère ou récupère l'ID de série pour un match
    
    Cette fonction utilise plusieurs heuristiques pour déterminer l'ID de la série:
    1. Si le match est déjà associé à une série dans le mapping, retourne cet ID
    2. Recherche une série existante avec les mêmes équipes en comparant les IDs des joueurs
    3. Si aucune série n'est trouvée, crée une nouvelle série avec le préfixe s_ et l'ID du match actuel
    
    Args:
        match_data (dict): Données du match issues de l'API Steam
        
    Returns:
        str: ID de la série
    """
    match_id = str(match_data.get('match_id'))
    radiant_series_wins = match_data.get('radiant_series_wins', 0)
    dire_series_wins = match_data.get('dire_series_wins', 0)
    
    # 1. Vérifier si le match est déjà associé à une série
    mapping = load_series_mapping()
    for series_id, matches in mapping.items():
        if match_id in matches:
            logger.info(f"Match {match_id} déjà associé à la série {series_id}")
            return series_id
    
    # 2. Rechercher une série existante avec les mêmes équipes
    # Récupérer les IDs des équipes radiant et dire
    radiant_team_id = match_data.get('radiant_team', {}).get('team_id')
    dire_team_id = match_data.get('dire_team', {}).get('team_id')
    
    # Récupérer les IDs des joueurs pour une correspondance plus précise
    radiant_player_ids = []
    dire_player_ids = []
    
    # Extraire les IDs des joueurs
    players = match_data.get('players', [])
    for player in players:
        if player.get('team') == 0:  # Radiant
            player_id = player.get('account_id')
            if player_id:
                radiant_player_ids.append(player_id)
        elif player.get('team') == 1:  # Dire
            player_id = player.get('account_id')
            if player_id:
                dire_player_ids.append(player_id)
    
    # 3. Déterminer le numéro de la map actuelle
    current_game_number = radiant_series_wins + dire_series_wins + 1
    
    # Importer ici pour éviter une dépendance circulaire
    from dual_cache_system import load_live_data, get_match_from_live_cache
    live_data = load_live_data()
    
    # Variable pour suivre si nous avons trouvé une série existante
    found_existing_series = False
    existing_series_id = None
    
    # 4. Rechercher une série existante en priorité
    # Vérifier si d'autres matchs récents existent déjà pour ces équipes
    for series_id, matches_list in mapping.items():
        if not matches_list:
            continue
            
        # Nous nous concentrons sur la dernière série en premier (plus petite distance de match_id)
        for existing_match_id in matches_list:
            # Vérifier si la différence d'ID est inférieure à un certain seuil (pour les séries récentes uniquement)
            if abs(int(existing_match_id) - int(match_id)) > 1000000:  # Un seuil arbitraire pour limiter aux matchs récents
                continue
                
            existing_match = get_match_from_live_cache(existing_match_id)
            if not existing_match:
                continue
            
            # Correspondance par ID d'équipe
            existing_radiant_id = existing_match.get('radiant_team', {}).get('team_id')
            existing_dire_id = existing_match.get('dire_team', {}).get('team_id')
            
            # Si les IDs d'équipe correspondent exactement (même position)
            direct_team_match = (existing_radiant_id == radiant_team_id and existing_dire_id == dire_team_id)
            
            # Si les IDs d'équipe correspondent mais positions inversées
            swapped_team_match = (existing_radiant_id == dire_team_id and existing_dire_id == radiant_team_id)
            
            # Correspondance d'équipe via les IDs des joueurs (plus fiable quand les IDs d'équipe manquent)
            player_match = False
            existing_players = existing_match.get('players', [])
            
            existing_radiant_player_ids = []
            existing_dire_player_ids = []
            
            # Extraire les IDs des joueurs du match existant
            for player in existing_players:
                if player.get('team') == 0:  # Radiant
                    player_id = player.get('account_id')
                    if player_id:
                        existing_radiant_player_ids.append(player_id)
                elif player.get('team') == 1:  # Dire
                    player_id = player.get('account_id')
                    if player_id:
                        existing_dire_player_ids.append(player_id)
            
            # Compter combien de joueurs correspondent entre les deux matchs
            radiant_to_radiant_matches = len(set(radiant_player_ids) & set(existing_radiant_player_ids))
            dire_to_dire_matches = len(set(dire_player_ids) & set(existing_dire_player_ids))
            radiant_to_dire_matches = len(set(radiant_player_ids) & set(existing_dire_player_ids))
            dire_to_radiant_matches = len(set(dire_player_ids) & set(existing_radiant_player_ids))
            
            # Si nous avons au moins 3 joueurs qui correspondent des deux côtés
            direct_player_match = (radiant_to_radiant_matches >= 3 and dire_to_dire_matches >= 3)
            swapped_player_match = (radiant_to_dire_matches >= 3 and dire_to_radiant_matches >= 3)
            
            # Si les équipes correspondent d'une manière ou d'une autre
            if direct_team_match or swapped_team_match or direct_player_match or swapped_player_match:
                logger.info(f"Série existante trouvée ({series_id}) pour le match {match_id} basée sur la correspondance d'équipe")
                found_existing_series = True
                existing_series_id = series_id
                break
        
        if found_existing_series:
            break
    
    # 5. Si une série existante a été trouvée, l'utiliser
    if found_existing_series and existing_series_id:
        series_id = existing_series_id
        logger.info(f"Utilisation de la série existante {series_id} pour le match {match_id} (Game {current_game_number})")
    else:
        # 6. Sinon, créer une nouvelle série avec l'ID du match actuel
        series_id = f"s_{match_id}"
        logger.info(f"Nouvelle série créée avec ID {series_id} pour match {match_id} (Game {current_game_number})")
    
    # 7. Enregistrer l'association dans le mapping
    if series_id not in mapping:
        mapping[series_id] = []
    
    if match_id not in mapping[series_id]:
        mapping[series_id].append(match_id)
        save_series_mapping(mapping)
    
    return series_id

def add_match_to_series(series_id, match_id):
    """
    Ajoute un match à une série existante
    
    Args:
        series_id (str): ID de la série
        match_id (str): ID du match à ajouter
        
    Returns:
        bool: True si l'ajout a réussi, False sinon
    """
    try:
        mapping = load_series_mapping()
        
        if series_id not in mapping:
            mapping[series_id] = []
        
        if match_id not in mapping[series_id]:
            mapping[series_id].append(match_id)
            save_series_mapping(mapping)
            logger.info(f"Match {match_id} ajouté à la série {series_id}")
            return True
        else:
            logger.info(f"Match {match_id} déjà présent dans la série {series_id}")
            return True
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du match {match_id} à la série {series_id}: {e}")
        return False

def get_matches_in_series(series_id):
    """
    Récupère tous les matchs d'une série
    
    Args:
        series_id (str): ID de la série
        
    Returns:
        list: Liste des IDs de match dans la série
    """
    mapping = load_series_mapping()
    return mapping.get(series_id, [])

def get_current_game_number(match_data):
    """
    Détermine le numéro du match actuel dans la série
    
    Args:
        match_data (dict): Données du match issues de l'API Steam
        
    Returns:
        int: Numéro du match dans la série (1, 2 ou 3)
    """
    radiant_series_wins = match_data.get('radiant_series_wins', 0)
    dire_series_wins = match_data.get('dire_series_wins', 0)
    
    # Le numéro du match est la somme des victoires + 1
    return radiant_series_wins + dire_series_wins + 1

def get_series_type(match_data):
    """
    Détermine le type de série (BO1, BO3, BO5)
    
    Args:
        match_data (dict): Données du match issues de l'API Steam
        
    Returns:
        int: Type de série (0=BO1, 1=BO3, 2=BO5)
    """
    # L'API Steam fournit cette information directement
    return match_data.get('series_type', 1)  # Default to BO3 if not provided

def get_max_games(series_type):
    """
    Détermine le nombre maximum de matchs dans une série
    
    Args:
        series_type (int): Type de série (0=BO1, 1=BO3, 2=BO5)
        
    Returns:
        int: Nombre maximum de matchs
    """
    if series_type == 0:
        return 1  # BO1
    elif series_type == 1:
        return 3  # BO3
    elif series_type == 2:
        return 5  # BO5
    else:
        return 3  # Default to BO3
#!/usr/bin/env python3
"""
Script amélioré pour trouver les matchs qui font partie de la même série,
avec des règles plus strictes sur la proximité temporelle et l'ID des matchs.
"""

import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional, Set

import opendota_api
from find_previous_matches import (
    get_current_series_data,
    get_match_from_cache,
    update_series_with_previous_matches,
    update_series_mapping
)

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paramètres de recherche
MAX_HOURS_DIFF = 3  # Différence maximale en heures entre matchs d'une même série
MAX_ID_DIFF = 100000  # Différence maximale entre IDs de matchs d'une même série
SIMILARITY_THRESHOLD = 0.6  # Seuil de similarité pour considérer qu'il s'agit des mêmes équipes

def calculate_teams_similarity(players1: Set[str], players2: Set[str]) -> float:
    """
    Calcule la similarité entre deux ensembles de joueurs
    
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

def is_likely_same_series(
    current_match_id: str, 
    current_match_time: int,
    candidate_match_id: str,
    candidate_match_time: int
) -> bool:
    """
    Détermine si un match candidat fait probablement partie de la même série
    que le match actuel, basé sur la proximité temporelle et des IDs.
    
    Args:
        current_match_id (str): ID du match actuel
        current_match_time (int): Timestamp du match actuel
        candidate_match_id (str): ID du match candidat
        candidate_match_time (int): Timestamp du match candidat
        
    Returns:
        bool: True si le match fait probablement partie de la même série
    """
    # Vérifier la proximité temporelle
    time_diff_seconds = abs(current_match_time - candidate_match_time)
    time_diff_hours = time_diff_seconds / 3600
    
    if time_diff_hours > MAX_HOURS_DIFF:
        logger.info(f"Match {candidate_match_id} écarté : trop éloigné temporellement ({time_diff_hours:.1f}h)")
        return False
    
    # Vérifier la proximité des IDs
    try:
        id_diff = abs(int(current_match_id) - int(candidate_match_id))
        if id_diff > MAX_ID_DIFF:
            logger.info(f"Match {candidate_match_id} écarté : ID trop éloigné (diff={id_diff})")
            return False
    except ValueError:
        # En cas d'erreur de conversion des IDs
        logger.warning(f"Erreur de comparaison des IDs: {current_match_id} vs {candidate_match_id}")
        return False
    
    logger.info(f"Match {candidate_match_id} validé : proximité temporelle ({time_diff_hours:.1f}h), proximité ID (diff={id_diff})")
    return True

def find_matches_same_series(series_id: str, max_hours_diff: int = MAX_HOURS_DIFF) -> List[Dict[str, Any]]:
    """
    Trouve les matchs qui font partie de la même série, avec des règles strictes
    
    Args:
        series_id (str): ID de la série
        max_hours_diff (int): Différence maximale en heures
        
    Returns:
        list: Liste des matchs trouvés qui font partie de la même série
    """
    # Récupérer les données de la série actuelle
    series_data = get_current_series_data(series_id)
    if not series_data:
        logger.error(f"Série {series_id} non trouvée dans le cache")
        return []
    
    # Récupérer la liste des matchs déjà présents dans la série
    match_ids = series_data.get('match_ids', [])
    if not match_ids:
        logger.error(f"Série {series_id} ne contient aucun match")
        return []
    
    # Récupérer le dernier match de la série (match le plus récent)
    current_match_id = match_ids[0]  # Généralement le plus récent
    current_match_data = get_match_from_cache(current_match_id)
    if not current_match_data:
        logger.error(f"Match {current_match_id} non trouvé dans les caches")
        return []
    
    # Extraire les joueurs et les noms d'équipes
    radiant_players = set()
    dire_players = set()
    radiant_team_name = current_match_data.get('radiant_team', {}).get('name', "Équipe Radiant")
    dire_team_name = current_match_data.get('dire_team', {}).get('name', "Équipe Dire")
    
    # Extraire les IDs des joueurs
    for player in current_match_data.get('players', []):
        account_id = str(player.get('account_id', ''))
        if not account_id:
            continue
        
        if player.get('isRadiant', player.get('team_number', 0) == 0):
            radiant_players.add(account_id)
        else:
            dire_players.add(account_id)
    
    if len(radiant_players) < 3 or len(dire_players) < 3:
        logger.warning(f"Pas assez de joueurs identifiés dans le match {current_match_id}")
        return []
    
    logger.info(f"Recherche des matchs de la même série que {series_id}")
    logger.info(f"Équipe Radiant: {radiant_team_name} ({len(radiant_players)} joueurs)")
    logger.info(f"Équipe Dire: {dire_team_name} ({len(dire_players)} joueurs)")
    
    # Récupérer le timestamp du match actuel
    current_match_time = int(current_match_data.get('start_time', int(time.time())))
    
    # Choisir un joueur pour obtenir son historique récent
    sample_player_id = next(iter(radiant_players)) if radiant_players else None
    if not sample_player_id:
        logger.error("Aucun ID de joueur trouvé pour la recherche")
        return []
    
    # Récupérer les matchs récents de ce joueur
    recent_matches = opendota_api.get_player_recent_matches(sample_player_id)
    if not recent_matches:
        logger.warning(f"Aucun match récent trouvé pour le joueur {sample_player_id}")
        return []
    
    # Liste des matchs trouvés qui font partie de la même série
    found_matches = []
    
    # Analyser chaque match récent
    for match in recent_matches:
        candidate_match_id = str(match.get('match_id', ''))
        candidate_match_time = match.get('start_time', 0)
        
        # Ignorer les matchs déjà dans la série
        if candidate_match_id in match_ids:
            continue
        
        # Vérifier si ce match fait probablement partie de la même série
        if not is_likely_same_series(
            current_match_id, 
            current_match_time,
            candidate_match_id, 
            candidate_match_time
        ):
            continue
        
        # Récupérer les détails complets du match
        match_details = opendota_api.get_match_details(candidate_match_id)
        if not match_details or not match_details.get('players'):
            continue
        
        # Extraire les joueurs de ce match
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
        
        # Calculer la similarité des équipes dans les deux sens possibles
        # (car les équipes peuvent changer de côté entre les matchs)
        radiant_similarity1 = calculate_teams_similarity(radiant_players, match_radiant_players)
        dire_similarity1 = calculate_teams_similarity(dire_players, match_dire_players)
        
        radiant_similarity2 = calculate_teams_similarity(radiant_players, match_dire_players)
        dire_similarity2 = calculate_teams_similarity(dire_players, match_radiant_players)
        
        # Vérifier la similarité des équipes
        same_teams = False
        teams_flipped = False
        
        if radiant_similarity1 >= SIMILARITY_THRESHOLD and dire_similarity1 >= SIMILARITY_THRESHOLD:
            same_teams = True
            teams_flipped = False
        elif radiant_similarity2 >= SIMILARITY_THRESHOLD and dire_similarity2 >= SIMILARITY_THRESHOLD:
            same_teams = True
            teams_flipped = True
        
        if not same_teams:
            logger.info(f"Match {candidate_match_id} écarté : équipes différentes")
            logger.info(f"  Radiant: {radiant_similarity1:.2f}, Dire: {dire_similarity1:.2f}")
            logger.info(f"  Radiant(alt): {radiant_similarity2:.2f}, Dire(alt): {dire_similarity2:.2f}")
            continue
        
        # Convertir les données au format interne
        match_data = opendota_api.convert_to_internal_format(match_details)
        
        # Adapter les noms d'équipes si nécessaire
        if teams_flipped:
            match_data['radiant_team_name'] = dire_team_name
            match_data['dire_team_name'] = radiant_team_name
        else:
            match_data['radiant_team_name'] = radiant_team_name
            match_data['dire_team_name'] = dire_team_name
        
        # Ajouter à la liste des matchs trouvés
        found_matches.append(match_data)
        logger.info(f"Match trouvé: {candidate_match_id}")
    
    # Trier par ID de match
    found_matches.sort(key=lambda m: int(m['match_id']))
    
    # Ajouter le numéro de game en fonction de l'ordre
    for i, match in enumerate(found_matches):
        match['game_number'] = i + 1
    
    return found_matches

def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        print("Usage: python find_matches_same_series.py <series_id> [max_hours_diff]")
        return
    
    series_id = sys.argv[1]
    
    # Paramètre optionnel pour la différence horaire maximale
    max_hours_diff = MAX_HOURS_DIFF
    if len(sys.argv) > 2:
        try:
            max_hours_diff = float(sys.argv[2])
        except ValueError:
            logger.warning(f"Valeur invalide pour max_hours_diff, utilisation de la valeur par défaut: {MAX_HOURS_DIFF}")
    
    # Rechercher les matchs de la même série
    matches = find_matches_same_series(series_id, max_hours_diff)
    
    if matches:
        logger.info(f"{len(matches)} matchs trouvés pour la série {series_id}")
        
        # Afficher les matchs trouvés
        for i, match in enumerate(matches):
            match_id = match.get('match_id')
            logger.info(f"[{i+1}] Match {match_id}")
        
        # Proposer de mettre à jour la série
        update_option = input("Mettre à jour la série ? (o/n): ")
        if update_option.lower() == 'o':
            # Mettre à jour la série
            update_series_with_previous_matches(series_id, matches)
            
            # Mettre à jour le mapping des séries
            match_ids = [match['match_id'] for match in matches]
            update_series_mapping(series_id, match_ids)
            
            logger.info("Série mise à jour avec succès")
    else:
        logger.warning(f"Aucun match trouvé pour la série {series_id}")

if __name__ == "__main__":
    main()
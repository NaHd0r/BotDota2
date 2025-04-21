"""
Script pour corriger l'extraction des account_id depuis l'API Steam

Ce script analyse la structure correcte de l'API Steam et met à jour le code
pour extraire les account_id au bon endroit.
"""

import json
import logging
import os
import requests
from typing import Dict, List, Any, Set

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes
STEAM_API_KEY = os.environ.get("STEAM_API_KEY", "")
STEAM_API_URL = "https://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v1/"
ALLOWED_LEAGUE_IDS = ["17911", "17211"]

def get_live_matches() -> List[Dict[str, Any]]:
    """
    Récupère tous les matchs en direct depuis l'API Steam
    
    Returns:
        list: Liste des matchs en direct avec les données brutes de l'API
    """
    params = {"key": STEAM_API_KEY}
    
    try:
        response = requests.get(STEAM_API_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        games = data.get("result", {}).get("games", [])
        
        # Filtrer les matchs par ID de ligue
        filtered_games = [
            game for game in games 
            if str(game.get("league_id", "")) in ALLOWED_LEAGUE_IDS
        ]
        
        logger.info(f"API Steam: {len(filtered_games)} matchs en direct dans les ligues surveillées")
        return filtered_games
    
    except (requests.RequestException, json.JSONDecodeError) as e:
        logger.error(f"Erreur lors de la récupération des matchs en direct: {e}")
        return []

def extract_account_ids_from_match(match_data: Dict[str, Any]) -> Dict[int, str]:
    """
    Extrait les account_id des joueurs d'un match avec leur team (0=radiant, 1=dire)
    
    Args:
        match_data (dict): Données du match depuis l'API Steam
        
    Returns:
        dict: Mapping des account_id vers leur équipe (0=radiant, 1=dire)
    """
    account_ids = {}
    
    if "players" in match_data:
        for player in match_data["players"]:
            account_id = player.get("account_id")
            team = player.get("team")
            
            if account_id is not None:
                # Convertir en string pour uniformité
                account_ids[account_id] = team
                
    logger.info(f"Extraction: {len(account_ids)} account_id extraits du match {match_data.get('match_id')}")
    return account_ids

def show_match_structure():
    """
    Affiche la structure des joueurs dans un match de l'API Steam
    pour analyser où se trouvent les account_id
    """
    matches = get_live_matches()
    
    if not matches:
        logger.error("Aucun match en direct trouvé pour analyser la structure")
        return
    
    sample_match = matches[0]
    match_id = sample_match.get("match_id", "inconnu")
    
    logger.info(f"Analyse du match {match_id}:")
    
    # Vérifier si la liste des joueurs existe au premier niveau
    if "players" in sample_match:
        logger.info("Liste des joueurs trouvée au premier niveau du match")
        logger.info(f"Nombre de joueurs: {len(sample_match['players'])}")
        
        # Afficher un exemple de structure de joueur
        if sample_match["players"]:
            logger.info("Structure d'exemple d'un joueur:")
            player = sample_match["players"][0]
            for key, value in player.items():
                logger.info(f"  - {key}: {value}")
    else:
        logger.info("Aucune liste de joueurs au premier niveau du match")
    
    # Vérifier si les équipes contiennent aussi des listes de joueurs
    for team_key in ["radiant_team", "dire_team"]:
        if team_key in sample_match:
            team_data = sample_match[team_key]
            logger.info(f"Équipe {team_key} trouvée:")
            
            if "players" in team_data:
                logger.info(f"  - Liste des joueurs trouvée dans {team_key}")
                logger.info(f"  - Nombre de joueurs: {len(team_data['players'])}")
            else:
                logger.info(f"  - Aucune liste de joueurs dans {team_key}")
                
            # Afficher la structure de l'équipe
            for key, value in team_data.items():
                if key != "players":  # Pour éviter d'afficher toute la liste des joueurs
                    logger.info(f"  - {key}: {value}")

def main():
    """
    Fonction principale pour analyser et corriger l'extraction des account_id
    """
    logger.info("=== Analyse de la structure de l'API Steam pour les account_id ===")
    
    show_match_structure()
    
    # Tester l'extraction des account_id
    matches = get_live_matches()
    if matches:
        sample_match = matches[0]
        account_ids = extract_account_ids_from_match(sample_match)
        
        # Afficher les account_id extraits
        logger.info("\nAccount IDs extraits du match :")
        for account_id, team in account_ids.items():
            logger.info(f"Account ID: {account_id}, Team: {team}")
        
        logger.info("\nRecommandation: Mettre à jour le code pour extraire les account_id"
                   " directement depuis la liste 'players' au premier niveau du match,"
                   " plutôt que de chercher dans match_data['radiant_team']['players']")

if __name__ == "__main__":
    main()
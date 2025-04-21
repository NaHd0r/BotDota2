#!/usr/bin/env python3
"""
Script pour analyser et tracer l'affiliation des joueurs à leurs équipes
et calculer correctement le networth total par équipe en utilisant le team_id.

Ce script permet de s'assurer que les calculs de networth sont bien attribués
à la bonne équipe, indépendamment de leur position Radiant/Dire qui peut changer
d'un match à l'autre dans une série.
"""

import os
import json
import logging
from typing import Dict, Any, List, Tuple

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes
CACHE_DIR = "cache"
LIVE_DATA_FILE = os.path.join(CACHE_DIR, "live_data.json")

def load_live_data() -> Dict[str, Any]:
    """Charge les données du cache live"""
    if not os.path.exists(LIVE_DATA_FILE):
        logger.error(f"Le fichier de cache {LIVE_DATA_FILE} n'existe pas")
        return {}
    
    try:
        with open(LIVE_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Erreur lors du chargement du cache live: {e}")
        return {}

def track_player_teams(match_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Trace les joueurs et leur affiliation d'équipe
    
    Args:
        match_id (str): ID du match à analyser
        
    Returns:
        Dict: Mapping des account_id vers les informations d'équipe
    """
    data = load_live_data()
    if not data or "matches" not in data or match_id not in data["matches"]:
        logger.error(f"Match {match_id} non trouvé dans le cache")
        return {}
    
    match_data = data["matches"][match_id]
    player_team_mapping = {}
    
    # Traiter les joueurs de l'équipe Radiant
    if "radiant_team" in match_data and "players" in match_data["radiant_team"]:
        radiant_team_id = match_data["radiant_team"].get("team_id", "unknown")
        radiant_team_name = match_data["radiant_team"].get("team_name", "Radiant")
        
        for position, player in match_data["radiant_team"]["players"].items():
            account_id = player.get("account_id", "unknown")
            player_team_mapping[account_id] = {
                "team_id": radiant_team_id,
                "team_name": radiant_team_name,
                "side": "radiant",
                "position": position,
                "hero_id": player.get("hero_id", 0),
                "net_worth": player.get("net_worth", 0)
            }
    
    # Traiter les joueurs de l'équipe Dire
    if "dire_team" in match_data and "players" in match_data["dire_team"]:
        dire_team_id = match_data["dire_team"].get("team_id", "unknown")
        dire_team_name = match_data["dire_team"].get("team_name", "Dire")
        
        for position, player in match_data["dire_team"]["players"].items():
            account_id = player.get("account_id", "unknown")
            player_team_mapping[account_id] = {
                "team_id": dire_team_id,
                "team_name": dire_team_name,
                "side": "dire",
                "position": position,
                "hero_id": player.get("hero_id", 0),
                "net_worth": player.get("net_worth", 0)
            }
    
    return player_team_mapping

def calculate_team_networth(player_mapping: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Calcule le networth total par équipe à partir du mapping des joueurs
    
    Args:
        player_mapping (Dict): Mapping des account_id vers les informations d'équipe
        
    Returns:
        Dict: Networth total par équipe
    """
    team_networth = {}
    
    for account_id, player_info in player_mapping.items():
        team_id = player_info["team_id"]
        team_name = player_info["team_name"]
        net_worth = player_info["net_worth"]
        
        if team_id not in team_networth:
            team_networth[team_id] = {
                "team_name": team_name,
                "total_net_worth": 0,
                "player_count": 0
            }
        
        team_networth[team_id]["total_net_worth"] += net_worth
        team_networth[team_id]["player_count"] += 1
    
    return team_networth

def analyze_team_positions(match_ids: List[str]) -> None:
    """
    Analyse la position des équipes (Radiant/Dire) à travers plusieurs matchs
    
    Args:
        match_ids (List[str]): Liste des IDs de matchs à analyser
    """
    data = load_live_data()
    if not data or "matches" not in data:
        logger.error("Données de cache invalides")
        return
    
    print("\n=== ANALYSE DES POSITIONS D'ÉQUIPES DANS LA SÉRIE ===")
    
    for match_id in match_ids:
        if match_id not in data["matches"]:
            print(f"Match {match_id} non trouvé dans le cache")
            continue
        
        match_data = data["matches"][match_id]
        
        # Extraire les informations d'équipe
        radiant_team_id = match_data.get("radiant_team", {}).get("team_id", "unknown")
        radiant_team_name = match_data.get("radiant_team", {}).get("team_name", "Radiant")
        
        dire_team_id = match_data.get("dire_team", {}).get("team_id", "unknown")
        dire_team_name = match_data.get("dire_team", {}).get("team_name", "Dire")
        
        # Extraire les informations de série
        series_id = match_data.get("match_type", {}).get("series_id", "N/A")
        game_number = match_data.get("match_type", {}).get("series_current_value", "N/A")
        series_max = match_data.get("match_type", {}).get("series_max_value", "N/A")
        
        print(f"\nMatch {match_id} (Game {game_number}/{series_max}, Series {series_id}):")
        print(f"  Radiant: {radiant_team_name} (ID: {radiant_team_id})")
        print(f"  Dire: {dire_team_name} (ID: {dire_team_id})")
        
        # Calculer le networth par équipe basé sur le team_id
        player_mapping = track_player_teams(match_id)
        team_networth = calculate_team_networth(player_mapping)
        
        print("  Networth par équipe (basé sur team_id):")
        for team_id, team_info in team_networth.items():
            print(f"    {team_info['team_name']} (ID: {team_id}): {team_info['total_net_worth']}")

def track_player_consistency(match_ids: List[str]) -> None:
    """
    Vérifie si les mêmes joueurs restent dans la même équipe à travers les matchs
    
    Args:
        match_ids (List[str]): Liste des IDs de matchs à analyser
    """
    player_teams = {}
    data = load_live_data()
    
    if not data or "matches" not in data:
        logger.error("Données de cache invalides")
        return
    
    print("\n=== SUIVI DE LA CONSISTANCE DES JOUEURS DANS LA SÉRIE ===")
    
    for match_id in match_ids:
        if match_id not in data["matches"]:
            continue
        
        player_mapping = track_player_teams(match_id)
        
        for account_id, player_info in player_mapping.items():
            if account_id not in player_teams:
                player_teams[account_id] = []
            
            player_teams[account_id].append({
                "match_id": match_id,
                "team_id": player_info["team_id"],
                "team_name": player_info["team_name"],
                "side": player_info["side"]
            })
    
    # Vérifier la consistance
    for account_id, matches in player_teams.items():
        if len(matches) <= 1:
            continue
        
        first_team = matches[0]["team_id"]
        is_consistent = all(match["team_id"] == first_team for match in matches)
        
        if is_consistent:
            print(f"Joueur {account_id}: Consistant - Toujours avec {matches[0]['team_name']} (ID: {first_team})")
        else:
            print(f"Joueur {account_id}: INCONSISTANT - Change d'équipe entre les matchs:")
            for match in matches:
                print(f"  Match {match['match_id']}: {match['team_name']} (ID: {match['team_id']}) - {match['side'].capitalize()}")

def main() -> None:
    """Fonction principale"""
    print("Script d'analyse des équipes et du networth pour Dota 2")
    print("======================================================")
    
    # Analyser les 3 matchs de la série
    match_ids = ["8259450653", "8259522321", "8259581999"]
    
    # Analyser la position des équipes à travers les matchs
    analyze_team_positions(match_ids)
    
    # Vérifier la consistance des joueurs
    track_player_consistency(match_ids)
    
    print("\nAnalyse terminée.")

if __name__ == "__main__":
    main()
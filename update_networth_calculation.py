#!/usr/bin/env python3
"""
Script pour mettre à jour la méthode de calcul du networth total des équipes
dans le système Dota 2 Dashboard.

Ce script introduit une nouvelle fonction de calcul qui utilise le team_id
comme identifiant stable pour attribuer correctement le networth à chaque équipe,
indépendamment de leur position Radiant/Dire qui peut changer d'un match
à l'autre dans une série.
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

def save_live_data(data: Dict[str, Any]) -> None:
    """Sauvegarde les données dans le cache live"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    
    try:
        with open(LIVE_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Données sauvegardées dans {LIVE_DATA_FILE}")
    except IOError as e:
        logger.error(f"Erreur lors de la sauvegarde du cache live: {e}")

def calculate_team_networth_by_id(match_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Calcule le networth total par team_id en additionnant les networth des joueurs
    
    Args:
        match_data (Dict): Données du match
        
    Returns:
        Dict: Dictionnaire avec les team_id comme clés et les networth totaux comme valeurs
    """
    team_networth = {}
    
    # Initialiser les équipes avec leurs ID
    radiant_team_id = match_data.get("radiant_team", {}).get("team_id", "unknown")
    dire_team_id = match_data.get("dire_team", {}).get("team_id", "unknown")
    
    team_networth[radiant_team_id] = 0
    team_networth[dire_team_id] = 0
    
    # Calculer le networth pour l'équipe Radiant
    if "radiant_team" in match_data and "players" in match_data["radiant_team"]:
        for position, player in match_data["radiant_team"]["players"].items():
            team_networth[radiant_team_id] += player.get("net_worth", 0)
    
    # Calculer le networth pour l'équipe Dire
    if "dire_team" in match_data and "players" in match_data["dire_team"]:
        for position, player in match_data["dire_team"]["players"].items():
            team_networth[dire_team_id] += player.get("net_worth", 0)
    
    return team_networth

def update_networth_in_match(match_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Met à jour les champs de networth total dans les données du match
    
    Args:
        match_data (Dict): Données du match à mettre à jour
        
    Returns:
        Dict: Données du match mises à jour
    """
    team_networth = calculate_team_networth_by_id(match_data)
    
    # Obtenir les IDs des équipes
    radiant_team_id = match_data.get("radiant_team", {}).get("team_id", "unknown")
    dire_team_id = match_data.get("dire_team", {}).get("team_id", "unknown")
    
    # Mettre à jour les valeurs de networth total dans les données des équipes
    if "radiant_team" in match_data:
        match_data["radiant_team"]["total_net_worth"] = team_networth.get(radiant_team_id, 0)
    
    if "dire_team" in match_data:
        match_data["dire_team"]["total_net_worth"] = team_networth.get(dire_team_id, 0)
    
    return match_data

def update_all_matches_networth() -> None:
    """
    Met à jour le calcul du networth pour tous les matchs dans le cache
    """
    data = load_live_data()
    if not data or "matches" not in data:
        logger.error("Données de cache invalides")
        return
    
    updated_count = 0
    matches = data["matches"]
    
    for match_id, match_data in matches.items():
        original_radiant_networth = match_data.get("radiant_team", {}).get("total_net_worth", 0)
        original_dire_networth = match_data.get("dire_team", {}).get("total_net_worth", 0)
        
        # Mettre à jour les données du match
        updated_match_data = update_networth_in_match(match_data)
        matches[match_id] = updated_match_data
        
        new_radiant_networth = updated_match_data.get("radiant_team", {}).get("total_net_worth", 0)
        new_dire_networth = updated_match_data.get("dire_team", {}).get("total_net_worth", 0)
        
        # Vérifier si les valeurs ont été modifiées
        if original_radiant_networth != new_radiant_networth or original_dire_networth != new_dire_networth:
            updated_count += 1
            radiant_team_name = match_data.get("radiant_team", {}).get("team_name", "Radiant")
            dire_team_name = match_data.get("dire_team", {}).get("team_name", "Dire")
            
            print(f"Match {match_id} mis à jour:")
            print(f"  {radiant_team_name}: {original_radiant_networth} -> {new_radiant_networth}")
            print(f"  {dire_team_name}: {original_dire_networth} -> {new_dire_networth}")
    
    # Sauvegarder les données mises à jour
    if updated_count > 0:
        data["matches"] = matches
        save_live_data(data)
        print(f"{updated_count} matchs ont été mis à jour avec le nouveau calcul de networth.")
    else:
        print("Aucune mise à jour nécessaire, les valeurs de networth sont déjà correctes.")

def main() -> None:
    """Fonction principale"""
    print("Script de mise à jour du calcul du networth par équipe")
    print("====================================================")
    
    update_all_matches_networth()
    
    print("\nMise à jour terminée.")

if __name__ == "__main__":
    main()
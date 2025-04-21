#!/usr/bin/env python3
"""
Script pour corriger l'affichage des noms de joueurs dans l'application
en fusionnant les données du niveau racine (players) avec les données du scoreboard
"""

import os
import logging
import re

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_dota_service():
    """
    Met à jour le fichier dota_service.py pour fusionner les données des joueurs
    du niveau racine avec les données du scoreboard
    """
    try:
        with open('dota_service.py', 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du fichier: {e}")
        return False
    
    # Ajouter la nouvelle fonction extract_players_with_names après extract_players
    extract_players_regex = r'def extract_players\(players_data: List\[Dict\[str, Any\]\]\) -> Dict\[str, Dict\[str, Any\]\]:.*?return processed_players\n'
    extract_players_match = re.search(extract_players_regex, content, re.DOTALL)
    
    if not extract_players_match:
        logger.error("Fonction extract_players non trouvée")
        return False
    
    original_extract_players = extract_players_match.group(0)
    
    # Nouvelle fonction à ajouter
    new_function = """
def extract_players_with_names(scoreboard_players: List[Dict[str, Any]], root_players: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    \"\"\"
    Extrait les données des joueurs en combinant les données du scoreboard avec les noms des joueurs
    provenant du niveau racine des données de l'API
    
    Args:
        scoreboard_players (list): Liste des données des joueurs du scoreboard
        root_players (list): Liste des données des joueurs au niveau racine
        
    Returns:
        dict: Dictionnaire des joueurs indexé par position avec leurs noms complets
    \"\"\"
    processed_players = {}
    
    # Créer un mapping des account_id vers les noms des joueurs
    player_names = {}
    for player in root_players:
        account_id = str(player.get("account_id", ""))
        if account_id and "name" in player:
            player_names[account_id] = player.get("name", "")
    
    for i, player in enumerate(scoreboard_players):
        position = str(i)
        account_id = str(player.get("account_id", ""))
        
        # Récupérer le nom du joueur depuis le mapping
        player_name = player_names.get(account_id, "")
        
        processed_players[position] = {
            "account_id": account_id,
            "name": player_name,
            "hero_id": player.get("hero_id", 0),
            "net_worth": player.get("net_worth", 0),
            "gold": player.get("gold", 0),
            "kills": player.get("kills", 0),
            "deaths": player.get("death", 0),  # Notez que le champ API est "death" (singulier)
            "assists": player.get("assists", 0)
        }
    
    return processed_players
"""
    
    # Insérer la nouvelle fonction après la fonction extract_players originale
    updated_content = content.replace(original_extract_players, 
                                     original_extract_players + new_function)
    
    # Maintenant, mettre à jour la fonction process_live_match pour utiliser extract_players_with_names
    process_match_regex = r'# Traiter les données des joueurs\n\s+radiant_players = extract_players\(scoreboard\.get\("radiant", \{\}\)\.get\("players", \[\]\)\)\n\s+dire_players = extract_players\(scoreboard\.get\("dire", \{\}\)\.get\("players", \[\]\)\)'
    process_match_replacement = """# Traiter les données des joueurs
        # Utiliser la nouvelle fonction qui combine les noms et les stats
        radiant_players = extract_players_with_names(
            scoreboard.get("radiant", {}).get("players", []),
            match_data.get("players", [])
        )
        dire_players = extract_players_with_names(
            scoreboard.get("dire", {}).get("players", []),
            match_data.get("players", [])
        )"""
    
    updated_content = re.sub(process_match_regex, process_match_replacement, updated_content)
    
    # Sauvegarder le fichier mis à jour
    try:
        with open('dota_service.py', 'w', encoding='utf-8') as file:
            file.write(updated_content)
        logger.info("Fichier dota_service.py mis à jour avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'écriture du fichier: {e}")
        return False

if __name__ == "__main__":
    update_dota_service()
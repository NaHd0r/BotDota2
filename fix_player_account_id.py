"""
Script pour corriger l'extraction des account_id des joueurs depuis l'API Steam

Ce script met à jour la fonction log_players_details dans dota_service.py pour
extraire correctement les account_id depuis la liste players au niveau racine
du match, plutôt que de chercher dans radiant_team.players qui n'existe pas.
"""

import re
import logging
import os

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fichier à mettre à jour
DOTA_SERVICE_FILE = "./dota_service.py"

# Code actuel qui doit être remplacé
OLD_CODE = """def log_players_details(match_data: Dict[str, Any]) -> None:
    \"\"\"
    Journalise les détails des joueurs d'un match pour le débogage
    
    Args:
        match_data (dict): Données du match contenant les informations des joueurs
    \"\"\"
    match_id = match_data.get("match_id", "inconnu")
    
    # Journaliser les informations des joueurs par équipe
    if "radiant_team" in match_data and "players" in match_data["radiant_team"]:
        logger.info(f"RADIANT PROCESSED PLAYERS dans le match {match_id}:")
        for position, player in match_data["radiant_team"]["players"].items():
            logger.info(f"  - Player ID: {player.get('account_id', 'inconnu')}")
            logger.info(f"    Name: {player.get('name', 'inconnu')}")
            logger.info(f"    Hero ID: {player.get('hero_id', 0)}")
            logger.info(f"    NetWorth: {player.get('net_worth', 0)}")
    
    if "dire_team" in match_data and "players" in match_data["dire_team"]:
        logger.info(f"DIRE PROCESSED PLAYERS dans le match {match_id}:")
        for position, player in match_data["dire_team"]["players"].items():
            logger.info(f"  - Player ID: {player.get('account_id', 'inconnu')}")
            logger.info(f"    Name: {player.get('name', 'inconnu')}")
            logger.info(f"    Hero ID: {player.get('hero_id', 0)}")
            logger.info(f"    NetWorth: {player.get('net_worth', 0)}")"""

# Nouveau code qui utilise la bonne structure
NEW_CODE = """def log_players_details(match_data: Dict[str, Any]) -> None:
    \"\"\"
    Journalise les détails des joueurs d'un match pour le débogage
    
    Args:
        match_data (dict): Données du match contenant les informations des joueurs
    \"\"\"
    match_id = match_data.get("match_id", "inconnu")
    
    # Vérifier si nous avons des joueurs dans le match
    if "players" not in match_data:
        logger.warning(f"Aucun joueur trouvé dans le match {match_id}")
        return
    
    # Créer des dictionnaires pour les joueurs de chaque équipe
    radiant_players = {}
    dire_players = {}
    
    # Répartir les joueurs dans leurs équipes respectives
    for player in match_data["players"]:
        account_id = player.get("account_id", "inconnu")
        team = player.get("team", -1)
        
        # Team 0 = Radiant, Team 1 = Dire, Team 2 = Spectateur ou autre
        if team == 0:
            radiant_players[account_id] = player
        elif team == 1:
            dire_players[account_id] = player
    
    # Journaliser les joueurs Radiant
    logger.info(f"RADIANT PROCESSED PLAYERS dans le match {match_id}:")
    for account_id, player in radiant_players.items():
        logger.info(f"  - Player ID: {account_id}")
        logger.info(f"    Name: {player.get('name', 'inconnu')}")
        logger.info(f"    Hero ID: {player.get('hero_id', 0)}")
        logger.info(f"    NetWorth: {player.get('net_worth', 0)}")
    
    # Journaliser les joueurs Dire
    logger.info(f"DIRE PROCESSED PLAYERS dans le match {match_id}:")
    for account_id, player in dire_players.items():
        logger.info(f"  - Player ID: {account_id}")
        logger.info(f"    Name: {player.get('name', 'inconnu')}")
        logger.info(f"    Hero ID: {player.get('hero_id', 0)}")
        logger.info(f"    NetWorth: {player.get('net_worth', 0)}")"""

def update_dota_service():
    """
    Lit le fichier dota_service.py, remplace le code de la fonction
    log_players_details et écrit les modifications
    """
    try:
        # Lire le fichier
        with open(DOTA_SERVICE_FILE, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Vérifier que le code à remplacer existe bien
        if OLD_CODE not in content:
            logger.error("Impossible de trouver le code à remplacer dans dota_service.py")
            logger.info("Vérifiez que la fonction log_players_details n'a pas déjà été modifiée")
            return False
        
        # Remplacer le code
        new_content = content.replace(OLD_CODE, NEW_CODE)
        
        # Écrire les modifications
        with open(DOTA_SERVICE_FILE, 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        logger.info("La fonction log_players_details a été mise à jour avec succès")
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de dota_service.py: {e}")
        return False

def main():
    """
    Fonction principale pour mettre à jour le code d'extraction des account_id
    """
    logger.info("=== Correction de l'extraction des account_id dans dota_service.py ===")
    
    if update_dota_service():
        logger.info("Redémarrez le serveur pour appliquer les modifications")
    else:
        logger.error("La correction n'a pas pu être appliquée")

if __name__ == "__main__":
    main()
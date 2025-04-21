#!/usr/bin/env python3
"""
Script pour mettre à jour la fonction extract_players dans dota_service.py
afin de mieux récupérer et afficher les noms des joueurs
"""

import dual_cache_system as cache
import logging
import os
import re
from typing import Dict, Any

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_extract_players_function():
    """
    Met à jour la fonction extract_players dans dota_service.py
    pour mieux gérer les noms des joueurs
    """
    # Lire le fichier source
    try:
        with open('dota_service.py', 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du fichier: {e}")
        return False
    
    # Motif pour trouver la fonction extract_players
    pattern = r'def extract_players\(players_data:.*?\):.*?return processed_players'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        logger.error("Fonction extract_players non trouvée dans dota_service.py")
        return False
    
    # Récupérer l'ancienne implémentation
    old_function = match.group(0)
    
    # Créer la nouvelle implémentation
    new_function = """def extract_players(players_data: list) -> Dict[str, Dict[str, Any]]:
    """
    Extrait les données des joueurs à partir du tableau des scores
    
    Args:
        players_data (list): Liste des données brutes des joueurs
        
    Returns:
        dict: Dictionnaire des joueurs indexé par position
    """
    processed_players = {}
    
    # Créer un mapping temporaire des account_id vers les noms (pour le débogage)
    account_to_name = {
        # Exemple de mapping - à compléter avec les données réelles
        # Format: 'account_id': 'nom_du_joueur',
        '1419061264': 'All_After_me',
        # Ajoutez d'autres mappings ici
    }
    
    for i, player in enumerate(players_data):
        position = str(i)
        account_id = str(player.get("account_id", ""))
        name = account_to_name.get(account_id, "")  # Obtenir le nom depuis le mapping
        
        processed_players[position] = {
            "account_id": account_id,
            "name": name,
            "hero_id": player.get("hero_id", 0),
            "net_worth": player.get("net_worth", 0),
            "gold": player.get("gold", 0),
            "kills": player.get("kills", 0),
            "deaths": player.get("death", 0),  # Notez que le champ API est "death" (singulier)
            "assists": player.get("assists", 0)
        }
    
    return processed_players"""
    
    # Remplacer l'ancienne fonction par la nouvelle
    new_content = content.replace(old_function, new_function)
    
    # Sauvegarder le fichier mis à jour
    try:
        with open('dota_service.py', 'w', encoding='utf-8') as file:
            file.write(new_content)
        logger.info("Fonction extract_players mise à jour avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'écriture du fichier: {e}")
        return False

if __name__ == "__main__":
    update_extract_players_function()
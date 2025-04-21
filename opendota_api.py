"""
Module pour interagir avec l'API OpenDota.

Ce module fournit des fonctions pour récupérer des informations sur les matchs Dota 2
depuis l'API OpenDota, en particulier pour enrichir les matchs terminés avec des données
plus complètes que celles disponibles via l'API Steam.
"""

import time
import logging
import requests
from typing import Dict, Any, Optional, List

# Configuration du logger
logger = logging.getLogger(__name__)

# URL de base de l'API OpenDota
OPENDOTA_API_BASE_URL = "https://api.opendota.com/api"

# Délai entre les appels API pour éviter de dépasser les limites de rate
API_CALL_DELAY = 1.0  # secondes

# Dictionnaire pour stocker le timestamp du dernier appel API
last_api_call = {"timestamp": 0.0}

def respect_rate_limit() -> None:
    """
    Assure le respect des limites de débit de l'API OpenDota
    en attendant si nécessaire entre les appels
    """
    current_time = time.time()
    time_since_last_call = current_time - last_api_call["timestamp"]
    
    if time_since_last_call < API_CALL_DELAY:
        # Attendre pour respecter le délai minimal entre appels
        wait_time = API_CALL_DELAY - time_since_last_call
        logger.debug(f"Attente de {wait_time:.2f}s pour respecter les limites de l'API")
        time.sleep(wait_time)
    
    # Mettre à jour le timestamp du dernier appel
    last_api_call["timestamp"] = time.time()

def get_match_details(match_id: str) -> Optional[Dict[str, Any]]:
    """
    Récupère les détails complets d'un match depuis l'API OpenDota
    
    Args:
        match_id (str): ID du match à récupérer
        
    Returns:
        dict: Données du match ou None en cas d'erreur
    """
    # Respecter les limites de débit de l'API
    respect_rate_limit()
    
    try:
        # Utiliser une requête standard
        url = f"{OPENDOTA_API_BASE_URL}/matches/{match_id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            match_data = response.json()
            logger.info(f"Match {match_id} récupéré avec succès depuis OpenDota")
            return match_data
        else:
            logger.warning(f"Échec de récupération du match {match_id} (code {response.status_code})")
            return None
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du match {match_id} depuis OpenDota: {e}")
        return None

def get_player_details(account_id: str) -> Optional[Dict[str, Any]]:
    """
    Récupère les détails d'un joueur depuis l'API OpenDota
    
    Args:
        account_id (str): ID du compte du joueur
        
    Returns:
        dict: Données du joueur ou None en cas d'erreur
    """
    # Respecter les limites de débit de l'API
    respect_rate_limit()
    
    try:
        url = f"{OPENDOTA_API_BASE_URL}/players/{account_id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            player_data = response.json()
            logger.info(f"Joueur {account_id} récupéré avec succès depuis OpenDota")
            return player_data
        else:
            logger.warning(f"Échec de récupération du joueur {account_id} (code {response.status_code})")
            return None
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du joueur {account_id} depuis OpenDota: {e}")
        return None

def get_player_recent_matches(account_id: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
    """
    Récupère les matchs récents d'un joueur depuis l'API OpenDota
    
    Args:
        account_id (str): ID du compte du joueur
        limit (int): Nombre maximum de matchs à récupérer
        
    Returns:
        list: Liste des matchs récents ou None en cas d'erreur
    """
    # Respecter les limites de débit de l'API
    respect_rate_limit()
    
    try:
        url = f"{OPENDOTA_API_BASE_URL}/players/{account_id}/matches?limit={limit}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            matches = response.json()
            logger.info(f"Matchs récents du joueur {account_id} récupérés avec succès ({len(matches)} matchs)")
            return matches
        else:
            logger.warning(f"Échec de récupération des matchs du joueur {account_id} (code {response.status_code})")
            return None
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des matchs du joueur {account_id}: {e}")
        return None

def get_team_matches(team_id: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
    """
    Récupère les matchs récents d'une équipe depuis l'API OpenDota
    
    Args:
        team_id (str): ID de l'équipe
        limit (int): Nombre maximum de matchs à récupérer
        
    Returns:
        list: Liste des matchs récents ou None en cas d'erreur
    """
    # Respecter les limites de débit de l'API
    respect_rate_limit()
    
    try:
        url = f"{OPENDOTA_API_BASE_URL}/teams/{team_id}/matches?limit={limit}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            matches = response.json()
            logger.info(f"Matchs récents de l'équipe {team_id} récupérés avec succès ({len(matches)} matchs)")
            return matches
        else:
            logger.warning(f"Échec de récupération des matchs de l'équipe {team_id} (code {response.status_code})")
            return None
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des matchs de l'équipe {team_id}: {e}")
        return None

def convert_to_internal_format(opendota_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convertit les données de l'API OpenDota au format interne de l'application
    
    Args:
        opendota_data (dict): Données brutes de l'API OpenDota
        
    Returns:
        dict: Données converties au format interne
    """
    try:
        match_id = str(opendota_data.get("match_id", ""))
        radiant_win = opendota_data.get("radiant_win", False)
        duration = opendota_data.get("duration", 0)
        
        # Scores des équipes
        radiant_score = opendota_data.get("radiant_score", 0)
        dire_score = opendota_data.get("dire_score", 0)
        
        # Noms des équipes (peuvent être None dans l'API OpenDota)
        radiant_team_name = "Équipe Radiant"
        dire_team_name = "Équipe Dire"
        
        if "radiant_team" in opendota_data and opendota_data["radiant_team"]:
            radiant_team_name = opendota_data["radiant_team"].get("name", radiant_team_name)
        
        if "dire_team" in opendota_data and opendota_data["dire_team"]:
            dire_team_name = opendota_data["dire_team"].get("name", dire_team_name)
        
        # Extraire les joueurs pour un traitement ultérieur si nécessaire
        players = opendota_data.get("players", [])
        radiant_players = [p for p in players if p.get("isRadiant", True)]
        dire_players = [p for p in players if not p.get("isRadiant", True)]
        
        # Format interne
        internal_data = {
            "match_id": match_id,
            "duration": format_duration(duration),
            "radiant_team_name": radiant_team_name,
            "dire_team_name": dire_team_name,
            "radiant_score": radiant_score,
            "dire_score": dire_score,
            "total_kills": radiant_score + dire_score,
            "status": "finished",
            "status_tag": "FINISHED",
            "winner": "radiant" if radiant_win else "dire",
            "timestamp": opendota_data.get("start_time", int(time.time())),
            # Données supplémentaires pour l'enrichissement
            "radiant_win": radiant_win,
            "raw_duration": duration,
            "tower_status_radiant": opendota_data.get("tower_status_radiant", 0),
            "tower_status_dire": opendota_data.get("tower_status_dire", 0)
        }
        
        return internal_data
    
    except Exception as e:
        logger.error(f"Erreur lors de la conversion des données OpenDota: {e}")
        # Retourner des données minimales pour éviter les erreurs
        match_id_safe = opendota_data.get("match_id", "unknown")
        return {
            "match_id": str(match_id_safe),
            "duration": "0:00",
            "status": "error",
            "status_tag": "error",
            "radiant_score": 0,
            "dire_score": 0,
            "error": str(e)
        }

def format_duration(seconds: int) -> str:
    """
    Convertit une durée en secondes en format MM:SS
    
    Args:
        seconds (int): Nombre de secondes
        
    Returns:
        str: Durée formatée (ex: "47:07")
    """
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:02d}"

# Point d'entrée pour test manuel
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Exemple d'utilisation
    test_match_id = "8260574364"  # Remplacer par un ID de match valide
    
    logger.info(f"Test de récupération du match {test_match_id}")
    match_data = get_match_details(test_match_id)
    
    if match_data:
        logger.info(f"Match récupéré: {match_data.get('match_id')} ({match_data.get('duration')}s)")
        
        # Convertir au format interne
        internal_data = convert_to_internal_format(match_data)
        logger.info(f"Format interne: {internal_data['match_id']} - Score: {internal_data['radiant_score']}-{internal_data['dire_score']}")
    else:
        logger.error(f"Impossible de récupérer le match {test_match_id}")
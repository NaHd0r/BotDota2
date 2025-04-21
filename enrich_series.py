#!/usr/bin/env python3
"""
Script pour enrichir les données historiques d'une série avec l'API OpenDota.

Ce script récupère les matchs terminés d'une série, enrichit leurs données avec 
l'API OpenDota, et les intègre dans la structure du cache pour permettre leur
affichage dans l'interface.
"""

import os
import json
import time
import logging
import requests
from typing import Dict, Any, List, Optional

# Configuration du logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes
CACHE_DIR = "cache"
LIVE_DATA_FILE = os.path.join(CACHE_DIR, "live_data.json")
OPENDOTA_API_BASE = "https://api.opendota.com/api"

# Séries à enrichir
SERIES_ID = "s_8259450653"
MATCH_IDS = ["8259450653", "8259522321", "8259581999"]

def load_cache(file_path: str) -> Dict[str, Any]:
    """Charge le cache JSON depuis un fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        logger.error(f"Erreur lors du chargement du cache {file_path}: {e}")
        return {}

def save_cache(file_path: str, data: Dict[str, Any]) -> bool:
    """Sauvegarde le cache JSON dans un fichier"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Cache sauvegardé dans {file_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache {file_path}: {e}")
        return False

def fetch_opendota_match(match_id: str) -> Optional[Dict[str, Any]]:
    """
    Récupère les données d'un match depuis l'API OpenDota
    
    Args:
        match_id (str): ID du match à récupérer
        
    Returns:
        dict: Données du match ou None en cas d'erreur
    """
    url = f"{OPENDOTA_API_BASE}/matches/{match_id}"
    
    try:
        logger.info(f"Récupération des données du match {match_id} depuis OpenDota")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Données du match {match_id} récupérées avec succès")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur lors de la récupération des données du match {match_id}: {e}")
        return None
    except ValueError as e:
        logger.error(f"Erreur lors du parsing des données JSON pour le match {match_id}: {e}")
        return None

def format_duration(seconds: int) -> str:
    """
    Convertit une durée en secondes en format MM:SS
    
    Args:
        seconds (int): Nombre de secondes
        
    Returns:
        str: Durée formatée (ex: "47:07")
    """
    if seconds is None:
        return "0:00"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:02d}"

def convert_opendota_to_internal(opendota_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convertit les données de l'API OpenDota en format interne standardisé
    
    Args:
        opendota_data (dict): Données brutes de l'API OpenDota
        
    Returns:
        dict: Données converties au format interne
    """
    radiant_win = opendota_data.get("radiant_win", False)
    winner = "radiant" if radiant_win else "dire"
    
    return {
        "match_id": str(opendota_data.get("match_id")),
        "radiant_score": opendota_data.get("radiant_score", 0),
        "dire_score": opendota_data.get("dire_score", 0),
        "duration": format_duration(opendota_data.get("duration")),
        "start_time": opendota_data.get("start_time", int(time.time())),
        "end_time": opendota_data.get("start_time", int(time.time())) + opendota_data.get("duration", 0),
        "winner": winner,
        "status": "finished",  # Marquer les matchs récupérés via OpenDota comme terminés
        "status_tag": "TERMINÉ",  # Tag d'affichage pour l'interface
        "total_kills": opendota_data.get("radiant_score", 0) + opendota_data.get("dire_score", 0),
        "radiant_team": {
            "team_id": opendota_data.get("radiant_team_id", ""),
            "team_name": opendota_data.get("radiant_name", "Radiant")
        },
        "dire_team": {
            "team_id": opendota_data.get("dire_team_id", ""),
            "team_name": opendota_data.get("dire_name", "Dire")
        }
    }

def prepare_match_for_previous_matches(match_data: Dict[str, Any], game_number: int = 1) -> Dict[str, Any]:
    """
    Prépare les données d'un match pour la liste des matchs précédents d'une série
    
    Args:
        match_data (dict): Données du match au format interne
        game_number (int): Numéro du match dans la série
        
    Returns:
        dict: Données formatées pour les matchs précédents
    """
    return {
        "match_id": match_data.get("match_id"),
        "radiant_team_name": match_data.get("radiant_team", {}).get("team_name"),
        "dire_team_name": match_data.get("dire_team", {}).get("team_name"),
        "radiant_score": match_data.get("radiant_score", 0),
        "dire_score": match_data.get("dire_score", 0),
        "duration": match_data.get("duration", "0:00"),
        "total_kills": match_data.get("radiant_score", 0) + match_data.get("dire_score", 0),
        "game_number": game_number,
        "winner": match_data.get("winner"),
        "timestamp": match_data.get("start_time", int(time.time()))
    }

def enrich_series():
    """
    Enrichit les données d'une série en récupérant les informations
    via l'API OpenDota pour chaque match terminé.
    """
    # Charger le cache live
    cache_data = load_cache(LIVE_DATA_FILE)
    if not cache_data:
        logger.error("Le cache est vide")
        return False
    
    # Vérifier si la série existe
    if "series" not in cache_data or SERIES_ID not in cache_data["series"]:
        logger.error(f"La série {SERIES_ID} n'existe pas dans le cache")
        return False
    
    # Récupérer les données de la série
    series_data = cache_data["series"][SERIES_ID]
    
    # S'assurer que les match_ids sont à jour et dans le bon ordre
    series_data["match_ids"] = MATCH_IDS.copy()
    
    # Créer une liste pour les matchs précédents avec les bons numéros de jeu
    previous_matches = []
    
    # Pour chaque match de la série
    for i, match_id in enumerate(MATCH_IDS, 1):
        logger.info(f"Traitement du match {match_id} (game {i})")
        
        # Récupérer les données du match via OpenDota
        opendota_data = fetch_opendota_match(match_id)
        
        if not opendota_data:
            logger.warning(f"Impossible de récupérer les données OpenDota pour le match {match_id}")
            continue
        
        # Convertir les données OpenDota en format interne
        match_data = convert_opendota_to_internal(opendota_data)
        
        if not match_data:
            logger.warning(f"Erreur lors de la conversion des données pour le match {match_id}")
            continue
        
        # Mettre à jour le match dans le cache
        if "matches" not in cache_data:
            cache_data["matches"] = {}
        
        # Sauvegarder les données du match dans le cache
        cache_data["matches"][match_id] = match_data
        logger.info(f"Match {match_id} mis à jour dans le cache")
        
        # Créer une entrée pour previous_matches avec le bon numéro de jeu
        previous_match = prepare_match_for_previous_matches(match_data, i)
        previous_matches.append(previous_match)
        
        logger.info(f"Match {match_id} (game {i}) ajouté à previous_matches")
    
    if not previous_matches:
        logger.error("Aucun match précédent n'a été trouvé")
        return False
    
    # Mettre à jour la liste des matchs précédents
    series_data["previous_matches"] = previous_matches
    cache_data["series"][SERIES_ID] = series_data
    
    logger.info(f"La série {SERIES_ID} a maintenant {len(previous_matches)} matchs enrichis")
    
    # Sauvegarder le cache
    return save_cache(LIVE_DATA_FILE, cache_data)

def main():
    """Fonction principale"""
    print("===== Enrichissement d'une série avec l'API OpenDota =====")
    print(f"Série: {SERIES_ID}")
    print(f"Matchs: {', '.join(MATCH_IDS)}")
    
    if enrich_series():
        print("Enrichissement terminé avec succès!")
    else:
        print("Échec de l'enrichissement!")
    
    print("\nVérifiez l'API /match-history pour voir les matchs enrichis.")

if __name__ == "__main__":
    main()
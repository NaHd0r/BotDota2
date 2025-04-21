#!/usr/bin/env python3
"""
Script générique pour lier un match à une série existante dans le cache.
Cette version plus générique accepte des paramètres pour associer n'importe quel match
à n'importe quelle série.
"""

import os
import json
import logging
import sys
from typing import Dict, Any, List

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes
CACHE_DIR = "cache"
LIVE_DATA_FILE = os.path.join(CACHE_DIR, "live_data.json")
SERIES_PREFIX = "s_"

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

def save_live_data(data: Dict[str, Any]) -> bool:
    """Sauvegarde les données du cache live"""
    try:
        with open(LIVE_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Cache live sauvegardé avec succès")
        return True
    except IOError as e:
        logger.error(f"Erreur lors de la sauvegarde du cache live: {e}")
        return False

def link_match_to_series(match_id: str, series_id: str, game_number: int = None):
    """
    Lie un match à une série existante ou crée une nouvelle série
    
    Args:
        match_id (str): ID du match à lier
        series_id (str): ID de la série cible (sans le préfixe 's_')
        game_number (int, optional): Numéro du match dans la série
    
    Returns:
        bool: True si l'opération a réussi, False sinon
    """
    # Ajouter le préfixe 's_' si nécessaire
    if not series_id.startswith(SERIES_PREFIX):
        series_id = f"{SERIES_PREFIX}{series_id}"
    
    # Charger les données
    data = load_live_data()
    if not data:
        logger.error("Impossible de charger les données du cache")
        return False
    
    # Vérifier si le match existe dans le cache
    matches = data.get("matches", {})
    if match_id not in matches:
        logger.error(f"Match {match_id} non trouvé dans le cache")
        return False
    
    # Vérifier si la série existe déjà dans le cache
    series = data.get("series", {})
    series_exists = series_id in series
    
    # Si la série n'existe pas, la créer
    if not series_exists:
        # Récupérer les informations du match pour initialiser la série
        match_data = matches[match_id]
        series_type = match_data.get("match_type", {}).get("series_type", 1)
        max_games = 3 if series_type == 1 else (5 if series_type == 2 else 1)
        
        # Créer la série
        series[series_id] = {
            "series_type": series_type,
            "max_games": max_games,
            "radiant_score": match_data.get("radiant_series_wins", 0),
            "dire_score": match_data.get("dire_series_wins", 0),
            "match_ids": [match_id],
            "teams": {
                "radiant": {
                    "team_id": match_data.get("radiant_team", {}).get("team_id", "unknown"),
                    "team_name": match_data.get("radiant_team", {}).get("team_name", "Radiant")
                },
                "dire": {
                    "team_id": match_data.get("dire_team", {}).get("team_id", "unknown"),
                    "team_name": match_data.get("dire_team", {}).get("team_name", "Dire")
                }
            },
            "last_updated": match_data.get("timestamp", 0)
        }
        logger.info(f"Nouvelle série créée: {series_id}")
    else:
        # Mise à jour de la série existante
        if match_id not in series[series_id].get("match_ids", []):
            if "match_ids" not in series[series_id]:
                series[series_id]["match_ids"] = []
            series[series_id]["match_ids"].append(match_id)
            logger.info(f"Match {match_id} ajouté à la série {series_id}")
    
    # Mettre à jour les références de série dans les données du match
    match_type = matches[match_id].get("match_type", {})
    series_max = match_type.get("series_max_value", 3)
    
    if game_number is not None:
        match_type["series_current_value"] = game_number
    
    match_type["series_id"] = series_id
    match_type["series_max_value"] = series_max
    
    matches[match_id]["match_type"] = match_type
    
    # Sauvegarder les données mises à jour
    data["matches"] = matches
    data["series"] = series
    
    if save_live_data(data):
        logger.info(f"Le match {match_id} a été lié avec succès à la série {series_id}")
        if game_number is not None:
            logger.info(f"Numéro de match dans la série défini à {game_number}")
        return True
    else:
        logger.error("Erreur lors de la sauvegarde des données")
        return False

def print_usage():
    """Affiche les instructions d'utilisation"""
    print(f"Usage: python {sys.argv[0]} <match_id> <series_id> [game_number]")
    print("Arguments:")
    print("  match_id    : ID du match à lier à la série")
    print("  series_id   : ID de la série (avec ou sans le préfixe 's_')")
    print("  game_number : (Optionnel) Numéro du match dans la série (1, 2, 3, etc.)")
    print("\nExemple:")
    print(f"  python {sys.argv[0]} 8259450653 8259450653 1")
    print(f"  python {sys.argv[0]} 8259522321 8259450653 2")

if __name__ == "__main__":
    logger.info("Démarrage de la liaison de match à série...")
    
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)
    
    match_id = sys.argv[1]
    series_id = sys.argv[2]
    game_number = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    if link_match_to_series(match_id, series_id, game_number):
        logger.info("Liaison terminée avec succès")
    else:
        logger.error("Échec de la liaison")
        sys.exit(1)
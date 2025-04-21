#!/usr/bin/env python3
"""
Script pour lier les matchs Game1 et Game2 de la série entre Immortal Squad et Azure Dragons
Match ID Game 1: 8259450653
Match ID Game 2: 8259522321

Ce script modifie le cache pour s'assurer que ces deux matchs utilisent le même ID de série.
"""

import os
import json
import logging
from typing import Dict, Any

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes
CACHE_DIR = "cache"
LIVE_DATA_FILE = os.path.join(CACHE_DIR, "live_data.json")
SERIES_PREFIX = "s_"

# Match IDs à lier
GAME1_ID = "8259450653"  # Premier match de la série
GAME2_ID = "8259522321"  # Deuxième match de la série

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

def link_series_matches():
    """Lie les matchs de la même série sous un ID commun"""
    # Charger les données
    data = load_live_data()
    if not data:
        logger.error("Impossible de charger les données du cache")
        return False
    
    # Vérifier si les matchs existent dans le cache
    matches = data.get("matches", {})
    if GAME1_ID not in matches:
        logger.error(f"Match {GAME1_ID} non trouvé dans le cache")
        return False
    
    if GAME2_ID not in matches:
        logger.error(f"Match {GAME2_ID} non trouvé dans le cache")
        return False
    
    # Déterminer l'ID de série à utiliser (celui du premier match)
    series_id = f"{SERIES_PREFIX}{GAME1_ID}"
    logger.info(f"Utilisation de l'ID de série: {series_id}")
    
    # Vérifier si la série existe déjà dans le cache
    series = data.get("series", {})
    
    # Créer ou mettre à jour la série dans le cache
    if series_id not in series:
        series[series_id] = {
            "series_type": 1,  # Bo3
            "max_games": 3,
            "radiant_score": 1,  # Premier match remporté par Radiant (Immortal Squad)
            "dire_score": 0,
            "match_ids": [GAME1_ID, GAME2_ID],
            "teams": {
                "radiant": {
                    "team_id": "9339714",
                    "team_name": "Immortal Squad"
                },
                "dire": {
                    "team_id": "9086888",
                    "team_name": "Azure Dragons"
                }
            },
            "last_updated": matches[GAME2_ID].get("timestamp", 0)
        }
    else:
        # Mise à jour des matchs dans la série existante
        if GAME1_ID not in series[series_id].get("match_ids", []):
            series[series_id]["match_ids"].append(GAME1_ID)
        if GAME2_ID not in series[series_id].get("match_ids", []):
            series[series_id]["match_ids"].append(GAME2_ID)
    
    # Mettre à jour les références de série dans les données des matchs
    matches[GAME1_ID]["match_type"]["series_id"] = series_id
    matches[GAME1_ID]["match_type"]["series_current_value"] = 1
    matches[GAME1_ID]["match_type"]["series_max_value"] = 3
    
    matches[GAME2_ID]["match_type"]["series_id"] = series_id
    matches[GAME2_ID]["match_type"]["series_current_value"] = 2
    matches[GAME2_ID]["match_type"]["series_max_value"] = 3
    
    # Sauvegarder les données mises à jour
    data["matches"] = matches
    data["series"] = series
    
    if save_live_data(data):
        logger.info(f"Les matchs {GAME1_ID} et {GAME2_ID} ont été liés avec succès sous l'ID de série {series_id}")
        return True
    else:
        logger.error("Erreur lors de la sauvegarde des données")
        return False

if __name__ == "__main__":
    logger.info("Démarrage de la correction des liens de série...")
    if link_series_matches():
        logger.info("Correction terminée avec succès")
    else:
        logger.error("Échec de la correction")
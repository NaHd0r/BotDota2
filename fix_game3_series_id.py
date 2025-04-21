#!/usr/bin/env python3
"""
Script pour lier le match Game 3 (match ID 8259581999) avec la même série que les deux
précédents matchs de la série (Game 1: 8259450653, Game 2: 8259522321).
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

# Match IDs de la série
GAME1_ID = "8259450653"  # Premier match de la série
GAME2_ID = "8259522321"  # Deuxième match de la série
GAME3_ID = "8259581999"  # Troisième match de la série (à lier)

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

def link_game3_to_series():
    """Lie le match Game 3 à la même série que les matches Game 1 et Game 2"""
    # Charger les données
    data = load_live_data()
    if not data:
        logger.error("Impossible de charger les données du cache")
        return False
    
    # Vérifier si les matchs existent dans le cache
    matches = data.get("matches", {})
    if GAME3_ID not in matches:
        logger.error(f"Match {GAME3_ID} non trouvé dans le cache")
        return False
    
    # Déterminer l'ID de série à utiliser (celui du premier match)
    series_id = f"{SERIES_PREFIX}{GAME1_ID}"
    logger.info(f"Utilisation de l'ID de série: {series_id}")
    
    # Vérifier si la série existe dans le cache
    series = data.get("series", {})
    if series_id not in series:
        logger.error(f"Série {series_id} non trouvée dans le cache")
        return False
    
    # Ajouter le match Game 3 à la série
    if GAME3_ID not in series[series_id].get("match_ids", []):
        if "match_ids" not in series[series_id]:
            series[series_id]["match_ids"] = []
        series[series_id]["match_ids"].append(GAME3_ID)
    
    # Mettre à jour les références de série dans les données du match
    matches[GAME3_ID]["match_type"]["series_id"] = series_id
    matches[GAME3_ID]["match_type"]["series_current_value"] = 3
    matches[GAME3_ID]["match_type"]["series_max_value"] = 3
    
    # Sauvegarder les données mises à jour
    data["matches"] = matches
    data["series"] = series
    
    if save_live_data(data):
        logger.info(f"Le match {GAME3_ID} a été lié avec succès à la série {series_id}")
        return True
    else:
        logger.error("Erreur lors de la sauvegarde des données")
        return False

if __name__ == "__main__":
    logger.info("Démarrage de la correction des liens de série pour le Game 3...")
    if link_game3_to_series():
        logger.info("Correction terminée avec succès")
    else:
        logger.error("Échec de la correction")
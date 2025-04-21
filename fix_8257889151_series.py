#!/usr/bin/env python
"""
Script spécifique pour corriger la série 8257889151 en ajoutant les champs
manquants et en assurant la cohérence des champs entre les matchs de la série.

Ce script se concentre uniquement sur cette série spécifique pour éviter
de modifier accidentellement d'autres séries.
"""

import json
import os
import logging
import time

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
CACHE_DIR = 'cache'
LIVE_SERIES_CACHE = os.path.join(CACHE_DIR, 'live_series_cache.json')
SERIES_CACHE = os.path.join(CACHE_DIR, 'series_cache.json')
COMPLETED_SERIES_CACHE = os.path.join(CACHE_DIR, 'completed_series_cache.json')

# ID de la série et des matchs à corriger
SERIES_ID = "8257889151"
FIRST_MATCH_ID = "8257889151"
CURRENT_MATCH_ID = "8257938792"

def load_json_file(filepath):
    """Charge un fichier JSON"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du fichier {filepath}: {e}")
        return {}

def save_json_file(filepath, data):
    """Sauvegarde des données dans un fichier JSON"""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Fichier {filepath} sauvegardé avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du fichier {filepath}: {e}")
        return False

def format_duration(seconds):
    """
    Convertit une durée en secondes en format MM:SS
    
    Args:
        seconds: Nombre de secondes
        
    Returns:
        Durée formatée (ex: "47:07")
    """
    if not seconds:
        return "00:00"
    
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def get_match_data_from_completed_cache():
    """
    Récupère les données du match 8257889151 depuis le cache des séries complétées
    
    Returns:
        Données du match si trouvées, None sinon
    """
    completed_cache = load_json_file(COMPLETED_SERIES_CACHE)
    
    if SERIES_ID in completed_cache:
        for match in completed_cache[SERIES_ID].get("matches", []):
            if match.get("match_id") == FIRST_MATCH_ID:
                return match
    
    return None

def fix_series_cache():
    """
    Met à jour le cache principal des séries pour la série 8257889151
    en assurant la cohérence des champs entre les matchs
    """
    series_cache = load_json_file(SERIES_CACHE)
    
    # Obtenir les données du premier match
    completed_match_data = get_match_data_from_completed_cache()
    if not completed_match_data:
        logger.error(f"Match {FIRST_MATCH_ID} non trouvé dans le cache des séries complétées")
        return False
    
    # S'assurer que la série existe dans le cache
    if SERIES_ID not in series_cache:
        logger.warning(f"Série {SERIES_ID} non trouvée dans le cache, création d'une nouvelle entrée")
        series_cache[SERIES_ID] = {
            "series_id": SERIES_ID,
            "radiant_team_id": completed_match_data.get("radiant_team", {}).get("team_id"),
            "dire_team_id": completed_match_data.get("dire_team", {}).get("team_id"),
            "radiant_team_name": completed_match_data.get("radiant_team", {}).get("name"),
            "dire_team_name": completed_match_data.get("dire_team", {}).get("name"),
            "radiant_score": 1 if completed_match_data.get("winner") == "radiant" else 0,
            "dire_score": 1 if completed_match_data.get("winner") == "dire" else 0,
            "previous_matches": [],
            "series_type": 1  # Bo3
        }
    
    # Mettre à jour ou ajouter le match précédent à la liste
    previous_matches = series_cache[SERIES_ID].get("previous_matches", [])
    match_found = False
    
    for i, match in enumerate(previous_matches):
        if match.get("match_id") == FIRST_MATCH_ID:
            match_found = True
            # Mettre à jour le match existant
            previous_matches[i] = {
                "match_id": FIRST_MATCH_ID,
                "radiant_team_name": completed_match_data.get("radiant_team", {}).get("name"),
                "dire_team_name": completed_match_data.get("dire_team", {}).get("name"),
                "radiant_score": completed_match_data.get("radiant_score", 0),
                "dire_score": completed_match_data.get("dire_score", 0),
                "duration": completed_match_data.get("duration", "00:00"),
                "total_kills": completed_match_data.get("radiant_score", 0) + completed_match_data.get("dire_score", 0),
                "game_number": 1,
                "winner": completed_match_data.get("winner"),
                "timestamp": completed_match_data.get("start_time", int(time.time()))
            }
            break
    
    if not match_found:
        # Ajouter le nouveau match à la liste
        previous_matches.append({
            "match_id": FIRST_MATCH_ID,
            "radiant_team_name": completed_match_data.get("radiant_team", {}).get("name"),
            "dire_team_name": completed_match_data.get("dire_team", {}).get("name"),
            "radiant_score": completed_match_data.get("radiant_score", 0),
            "dire_score": completed_match_data.get("dire_score", 0),
            "duration": completed_match_data.get("duration", "00:00"),
            "total_kills": completed_match_data.get("radiant_score", 0) + completed_match_data.get("dire_score", 0),
            "game_number": 1,
            "winner": completed_match_data.get("winner"),
            "timestamp": completed_match_data.get("start_time", int(time.time()))
        })
    
    # Mettre à jour les previous_matches dans la série
    series_cache[SERIES_ID]["previous_matches"] = previous_matches
    
    # Sauvegarder le cache mis à jour
    return save_json_file(SERIES_CACHE, series_cache)

def fix_live_series_cache():
    """
    Met à jour le cache des séries en direct pour la série 8257889151
    en assurant la cohérence des champs entre les matchs
    """
    live_cache = load_json_file(LIVE_SERIES_CACHE)
    
    # Obtenir les données du premier match
    completed_match_data = get_match_data_from_completed_cache()
    if not completed_match_data:
        logger.error(f"Match {FIRST_MATCH_ID} non trouvé dans le cache des séries complétées")
        return False
    
    # Vérifier si la série existe déjà
    if SERIES_ID not in live_cache:
        logger.warning(f"Série {SERIES_ID} non trouvée dans le cache live, création d'une nouvelle entrée")
        live_cache[SERIES_ID] = {
            "series_id": SERIES_ID,
            "radiant_team_id": completed_match_data.get("radiant_team", {}).get("team_id"),
            "dire_team_id": completed_match_data.get("dire_team", {}).get("team_id"),
            "radiant_team_name": completed_match_data.get("radiant_team", {}).get("name"),
            "dire_team_name": completed_match_data.get("dire_team", {}).get("name"),
            "radiant_score": 1 if completed_match_data.get("winner") == "radiant" else 0,
            "dire_score": 1 if completed_match_data.get("winner") == "dire" else 0,
            "matches": [],
            "series_type": 1,  # Bo3
            "completed": False
        }
    
    # Préparer les données du match complété pour le cache live
    match_entry_1 = {
        "match_id": FIRST_MATCH_ID,
        "league_id": completed_match_data.get("league_id", 17911),
        "radiant_team_id": completed_match_data.get("radiant_team", {}).get("team_id"),
        "dire_team_id": completed_match_data.get("dire_team", {}).get("team_id"),
        "radiant_team_name": completed_match_data.get("radiant_team", {}).get("name"),
        "dire_team_name": completed_match_data.get("dire_team", {}).get("name"),
        "radiant_score": completed_match_data.get("radiant_score", 0),
        "dire_score": completed_match_data.get("dire_score", 0),
        "total_kills": completed_match_data.get("radiant_score", 0) + completed_match_data.get("dire_score", 0),
        "duration": completed_match_data.get("duration", "00:00"),
        "radiant_team": completed_match_data.get("radiant_team", {}),
        "dire_team": completed_match_data.get("dire_team", {}),
        "match_phase": "finished",
        "winner": completed_match_data.get("winner"),
        "game_number": 1,
        "timestamp": completed_match_data.get("start_time", int(time.time())),
        "start_time": completed_match_data.get("start_time", int(time.time()))
    }
    
    # Mettre à jour la liste des matchs dans la série
    matches = live_cache[SERIES_ID].get("matches", [])
    match_1_found = False
    match_2_found = False
    
    # Vérifier et mettre à jour le premier match
    for i, match in enumerate(matches):
        if isinstance(match, dict) and match.get("match_id") == FIRST_MATCH_ID:
            match_1_found = True
            matches[i] = match_entry_1
        elif isinstance(match, dict) and match.get("match_id") == CURRENT_MATCH_ID:
            match_2_found = True
            # S'assurer que le match en cours a les mêmes champs que le match complété
            if "total_kills" not in match:
                match["total_kills"] = match.get("radiant_score", 0) + match.get("dire_score", 0)
            if "match_phase" not in match:
                match["match_phase"] = "game"
    
    # Ajouter le premier match s'il n'existe pas
    if not match_1_found:
        matches.append(match_entry_1)
    
    # Mettre à jour les matches dans la série
    live_cache[SERIES_ID]["matches"] = matches
    
    # Sauvegarder le cache mis à jour
    return save_json_file(LIVE_SERIES_CACHE, live_cache)

def dump_debug_info():
    """Affiche les informations de debug sur la série"""
    live_cache = load_json_file(LIVE_SERIES_CACHE)
    series_cache = load_json_file(SERIES_CACHE)
    completed_cache = load_json_file(COMPLETED_SERIES_CACHE)
    
    logger.info("=== DONNÉES DU MATCH DANS LE CACHE DES SÉRIES COMPLÉTÉES ===")
    if SERIES_ID in completed_cache:
        for match in completed_cache[SERIES_ID].get("matches", []):
            if match.get("match_id") == FIRST_MATCH_ID:
                logger.info(f"Champs du match {FIRST_MATCH_ID}:")
                for key, value in match.items():
                    if not isinstance(value, dict) and not isinstance(value, list):
                        logger.info(f"  {key}: {value}")
    else:
        logger.warning(f"Série {SERIES_ID} non trouvée dans le cache des séries complétées")
    
    logger.info("=== DONNÉES DE LA SÉRIE DANS LE CACHE PRINCIPAL ===")
    if SERIES_ID in series_cache:
        for key, value in series_cache[SERIES_ID].items():
            if not isinstance(value, dict) and not isinstance(value, list):
                logger.info(f"  {key}: {value}")
        
        logger.info("  Previous matches:")
        for match in series_cache[SERIES_ID].get("previous_matches", []):
            logger.info(f"    Match {match.get('match_id')}:")
            for key, value in match.items():
                if not isinstance(value, dict) and not isinstance(value, list):
                    logger.info(f"      {key}: {value}")
    else:
        logger.warning(f"Série {SERIES_ID} non trouvée dans le cache principal")
    
    logger.info("=== DONNÉES DE LA SÉRIE DANS LE CACHE LIVE ===")
    if SERIES_ID in live_cache:
        for key, value in live_cache[SERIES_ID].items():
            if not isinstance(value, dict) and not isinstance(value, list):
                logger.info(f"  {key}: {value}")
        
        logger.info("  Matches:")
        for match in live_cache[SERIES_ID].get("matches", []):
            if isinstance(match, dict):
                logger.info(f"    Match {match.get('match_id')}:")
                for key, value in match.items():
                    if not isinstance(value, dict) and not isinstance(value, list):
                        logger.info(f"      {key}: {value}")
            else:
                logger.warning(f"    Match de type non-dictionnaire trouvé: {type(match)}")
    else:
        logger.warning(f"Série {SERIES_ID} non trouvée dans le cache live")

def main():
    """Fonction principale pour la correction de la série 8257889151"""
    logger.info(f"Démarrage de la correction de la série {SERIES_ID}")
    
    # Afficher les informations de debug avant la correction
    logger.info("=== ÉTAT AVANT CORRECTION ===")
    dump_debug_info()
    
    # Corriger le cache principal des séries
    if fix_series_cache():
        logger.info(f"Cache principal des séries mis à jour pour la série {SERIES_ID}")
    else:
        logger.error(f"Échec de la mise à jour du cache principal pour la série {SERIES_ID}")
    
    # Corriger le cache des séries en direct
    if fix_live_series_cache():
        logger.info(f"Cache des séries en direct mis à jour pour la série {SERIES_ID}")
    else:
        logger.error(f"Échec de la mise à jour du cache live pour la série {SERIES_ID}")
    
    # Afficher les informations de debug après la correction
    logger.info("=== ÉTAT APRÈS CORRECTION ===")
    dump_debug_info()
    
    logger.info(f"Correction de la série {SERIES_ID} terminée")

if __name__ == "__main__":
    main()
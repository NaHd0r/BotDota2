#!/usr/bin/env python
"""
Script pour mettre à jour le cache de la série 8257889151 avec les données complètes
du match précédent. Ce script corrige le problème d'affichage dans le frontend
en s'assurant que les données du match sont correctement intégrées au cache des séries.
"""

import json
import os
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
CACHE_DIR = 'cache'
COMPLETED_SERIES_CACHE = os.path.join(CACHE_DIR, 'completed_series_cache.json')
LIVE_SERIES_CACHE = os.path.join(CACHE_DIR, 'live_series_cache.json')
SERIES_CACHE = os.path.join(CACHE_DIR, 'series_cache.json')
SERIES_MAPPING = os.path.join(CACHE_DIR, 'series_matches_mapping.json')

# ID de la série et du match à mettre à jour
SERIES_ID = "8257889151"
MATCH_ID = "8257889151"
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

def update_series_mapping():
    """Met à jour le mapping des séries avec les matchs"""
    mappings = load_json_file(SERIES_MAPPING)
    
    # Vérifier si la série existe déjà dans le mapping
    if SERIES_ID not in mappings:
        # Ajouter la nouvelle série au mapping
        mappings[SERIES_ID] = {
            "series_id": SERIES_ID,
            "series_name": "Hellspawn vs Azure Dragons",
            "team1_name": "Hellspawn",
            "team2_name": "Azure Dragons",
            "matches": [
                {
                    "game_number": 1,
                    "match_id": MATCH_ID
                },
                {
                    "game_number": 2,
                    "match_id": CURRENT_MATCH_ID
                }
            ],
            "league_id": "17911",
            "scrape_time": 1744888888  # Horodatage actuel
        }
        
        # Sauvegarder le mapping mis à jour
        save_json_file(SERIES_MAPPING, mappings)
        logger.info(f"Série {SERIES_ID} ajoutée au mapping avec les matchs {MATCH_ID} et {CURRENT_MATCH_ID}")
    else:
        # Vérifier si les deux matchs sont déjà dans le mapping
        matches = mappings[SERIES_ID].get("matches", [])
        match_ids = [m.get("match_id") for m in matches]
        
        if MATCH_ID not in match_ids:
            matches.append({
                "game_number": len(matches) + 1,
                "match_id": MATCH_ID
            })
            
        if CURRENT_MATCH_ID not in match_ids:
            matches.append({
                "game_number": len(matches) + 1,
                "match_id": CURRENT_MATCH_ID
            })
            
        # Mise à jour des matchs
        mappings[SERIES_ID]["matches"] = matches
        
        # Sauvegarder le mapping mis à jour
        save_json_file(SERIES_MAPPING, mappings)
        logger.info(f"Mapping de la série {SERIES_ID} mis à jour avec les matchs")

def update_live_series_cache():
    """Met à jour le cache des séries en direct avec les données correctes"""
    completed_cache = load_json_file(COMPLETED_SERIES_CACHE)
    live_cache = load_json_file(LIVE_SERIES_CACHE)
    
    # Vérifier si les données du match terminé sont disponibles
    if SERIES_ID in completed_cache:
        completed_match_data = None
        
        # Chercher les données du match complété
        for match in completed_cache[SERIES_ID].get("matches", []):
            if match.get("match_id") == MATCH_ID:
                completed_match_data = match
                break
        
        if completed_match_data:
            # Mettre à jour ou ajouter la série dans le cache live
            if SERIES_ID not in live_cache:
                # Créer une nouvelle entrée dans le cache live
                live_cache[SERIES_ID] = {
                    "series_id": SERIES_ID,
                    "radiant_team_id": completed_cache[SERIES_ID].get("radiant_team_id"),
                    "dire_team_id": completed_cache[SERIES_ID].get("dire_team_id"),
                    "radiant_team_name": completed_cache[SERIES_ID].get("radiant_team_name"),
                    "dire_team_name": completed_cache[SERIES_ID].get("dire_team_name"),
                    "radiant_score": 1 if completed_match_data.get("winner") == "radiant" else 0,
                    "dire_score": 1 if completed_match_data.get("winner") == "dire" else 0,
                    "matches": [completed_match_data],
                    "series_type": 1,  # BO3
                    "completed": False
                }
            else:
                # Ajouter le match complété à la série existante
                existing_matches = live_cache[SERIES_ID].get("matches", [])
                match_ids = [m.get("match_id") for m in existing_matches]
                
                if MATCH_ID not in match_ids:
                    existing_matches.append(completed_match_data)
                    live_cache[SERIES_ID]["matches"] = existing_matches
                    
                # Mettre à jour le score de la série
                radiant_score = 0
                dire_score = 0
                for match in existing_matches:
                    if match.get("winner") == "radiant":
                        radiant_score += 1
                    elif match.get("winner") == "dire":
                        dire_score += 1
                        
                live_cache[SERIES_ID]["radiant_score"] = radiant_score
                live_cache[SERIES_ID]["dire_score"] = dire_score
            
            # Sauvegarder le cache mis à jour
            save_json_file(LIVE_SERIES_CACHE, live_cache)
            logger.info(f"Cache des séries en direct mis à jour pour la série {SERIES_ID}")
        else:
            logger.error(f"Données du match {MATCH_ID} non trouvées dans le cache des séries complétées")
    else:
        logger.error(f"Série {SERIES_ID} non trouvée dans le cache des séries complétées")

def update_series_cache():
    """Met à jour le cache de série principal avec les données complètes"""
    series_cache = load_json_file(SERIES_CACHE)
    completed_cache = load_json_file(COMPLETED_SERIES_CACHE)
    
    # Vérifier si les données du match terminé sont disponibles
    if SERIES_ID in completed_cache:
        completed_match_data = None
        
        # Chercher les données du match complété
        for match in completed_cache[SERIES_ID].get("matches", []):
            if match.get("match_id") == MATCH_ID:
                completed_match_data = match
                break
        
        if completed_match_data:
            # Créer ou mettre à jour l'entrée dans le cache principal des séries
            if SERIES_ID not in series_cache:
                series_cache[SERIES_ID] = {
                    "series_id": SERIES_ID,
                    "radiant_team_id": completed_cache[SERIES_ID].get("radiant_team_id"),
                    "dire_team_id": completed_cache[SERIES_ID].get("dire_team_id"),
                    "radiant_team_name": completed_cache[SERIES_ID].get("radiant_team_name"),
                    "dire_team_name": completed_cache[SERIES_ID].get("dire_team_name"),
                    "radiant_score": 1 if completed_match_data.get("winner") == "radiant" else 0,
                    "dire_score": 1 if completed_match_data.get("winner") == "dire" else 0,
                    "previous_matches": [
                        {
                            "match_id": MATCH_ID,
                            "radiant_team_name": completed_cache[SERIES_ID].get("radiant_team_name"),
                            "dire_team_name": completed_cache[SERIES_ID].get("dire_team_name"),
                            "radiant_score": completed_match_data.get("radiant_score", 0),
                            "dire_score": completed_match_data.get("dire_score", 0),
                            "duration": completed_match_data.get("duration", "00:00"),
                            "total_kills": completed_match_data.get("radiant_score", 0) + completed_match_data.get("dire_score", 0),
                            "game_number": 1,
                            "winner": completed_match_data.get("winner"),
                            "timestamp": completed_match_data.get("start_time", 0)
                        }
                    ],
                    "series_type": 1  # BO3
                }
            else:
                # Mettre à jour les données du match précédent dans la série
                previous_matches = series_cache[SERIES_ID].get("previous_matches", [])
                match_ids = [m.get("match_id") for m in previous_matches]
                
                if MATCH_ID not in match_ids:
                    previous_matches.append({
                        "match_id": MATCH_ID,
                        "radiant_team_name": completed_cache[SERIES_ID].get("radiant_team_name"),
                        "dire_team_name": completed_cache[SERIES_ID].get("dire_team_name"),
                        "radiant_score": completed_match_data.get("radiant_score", 0),
                        "dire_score": completed_match_data.get("dire_score", 0),
                        "duration": completed_match_data.get("duration", "00:00"),
                        "total_kills": completed_match_data.get("radiant_score", 0) + completed_match_data.get("dire_score", 0),
                        "game_number": len(previous_matches) + 1,
                        "winner": completed_match_data.get("winner"),
                        "timestamp": completed_match_data.get("start_time", 0)
                    })
                    
                    series_cache[SERIES_ID]["previous_matches"] = previous_matches
                
                # Mettre à jour le score de la série
                radiant_score = 0
                dire_score = 0
                for match in previous_matches:
                    if match.get("winner") == "radiant":
                        radiant_score += 1
                    elif match.get("winner") == "dire":
                        dire_score += 1
                        
                series_cache[SERIES_ID]["radiant_score"] = radiant_score
                series_cache[SERIES_ID]["dire_score"] = dire_score
            
            # Sauvegarder le cache mis à jour
            save_json_file(SERIES_CACHE, series_cache)
            logger.info(f"Cache principal des séries mis à jour pour la série {SERIES_ID}")
        else:
            logger.error(f"Données du match {MATCH_ID} non trouvées dans le cache des séries complétées")
    else:
        logger.error(f"Série {SERIES_ID} non trouvée dans le cache des séries complétées")

def dump_completed_match_data():
    """Affiche les données du match complété pour debug"""
    completed_cache = load_json_file(COMPLETED_SERIES_CACHE)
    
    if SERIES_ID in completed_cache:
        logger.info("Données de la série complétée:")
        print(json.dumps(completed_cache[SERIES_ID], indent=2))
        
        for match in completed_cache[SERIES_ID].get("matches", []):
            if match.get("match_id") == MATCH_ID:
                logger.info(f"Données du match {MATCH_ID}:")
                print(json.dumps(match, indent=2))
                return
                
        logger.error(f"Match {MATCH_ID} non trouvé dans la série {SERIES_ID}")
    else:
        logger.error(f"Série {SERIES_ID} non trouvée dans le cache")

if __name__ == "__main__":
    logger.info("Démarrage de la mise à jour des caches de série")
    
    # Afficher les données du match pour debug
    dump_completed_match_data()
    
    # Mettre à jour le mapping des séries
    update_series_mapping()
    
    # Mettre à jour le cache des séries en direct
    update_live_series_cache()
    
    # Mettre à jour le cache principal des séries
    update_series_cache()
    
    logger.info("Mise à jour des caches terminée")
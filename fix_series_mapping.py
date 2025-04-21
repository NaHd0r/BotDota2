#!/usr/bin/env python3
"""
Script pour corriger le mappage des séries et regrouper les matchs qui appartiennent
à la même série sous un ID de série commun.

Ce script permet de définir manuellement quels matchs font partie de la même série,
puis met à jour le cache en conséquence.
"""

import json
import os
import time
import logging
from typing import Dict, List, Any, Optional

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
CACHE_DIR = "cache"
LIVE_DATA_FILE = os.path.join(CACHE_DIR, "live_data.json")
HISTORICAL_DATA_FILE = os.path.join(CACHE_DIR, "historical_data.json")

def load_cache(file_path: str) -> Dict[str, Any]:
    """Charge le cache depuis le fichier"""
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"Cache chargé depuis {file_path}")
                return data
        else:
            logger.warning(f"Fichier de cache {file_path} non trouvé")
            return {"last_updated": 0, "matches": {}, "series": {}}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du cache {file_path}: {e}")
        return {"last_updated": 0, "matches": {}, "series": {}}

def save_cache(file_path: str, data: Dict[str, Any]) -> bool:
    """Sauvegarde le cache dans le fichier"""
    try:
        # Mise à jour du timestamp
        data["last_updated"] = int(time.time())
        
        # Créer le répertoire de cache s'il n'existe pas
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Cache sauvegardé dans {file_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache {file_path}: {e}")
        return False

def fix_series_mapping():
    """
    Corrige le mappage des séries dans le cache.
    
    Cette fonction regroupe les matchs qui font partie de la même série sous
    un ID de série commun, et met à jour les informations de la série.
    """
    # Définition des mappages: match_id -> series_id et game_number
    series_mappings = {
        # Série 1 - s_8259450653
        "8259450653": {"series_id": "s_8259450653", "game_number": 1},
        "8259522321": {"series_id": "s_8259450653", "game_number": 2},
        "8259581999": {"series_id": "s_8259450653", "game_number": 3},
    }
    
    # Charger les caches
    live_data = load_cache(LIVE_DATA_FILE)
    historical_data = load_cache(HISTORICAL_DATA_FILE)
    
    # Pour chaque mapping, appliquer les corrections
    for match_id, mapping in series_mappings.items():
        series_id = mapping["series_id"]
        game_number = mapping["game_number"]
        
        # Rechercher le match dans les caches
        match_data = None
        cache_data = None
        cache_file = None
        
        if match_id in live_data.get("matches", {}):
            match_data = live_data["matches"][match_id]
            cache_data = live_data
            cache_file = LIVE_DATA_FILE
        elif match_id in historical_data.get("matches", {}):
            match_data = historical_data["matches"][match_id]
            cache_data = historical_data
            cache_file = HISTORICAL_DATA_FILE
        
        if not match_data or not cache_data:
            logger.warning(f"Match {match_id} non trouvé dans les caches")
            continue
        
        # Mettre à jour l'ID de série du match
        if "match_type" not in match_data:
            match_data["match_type"] = {}
        match_data["match_type"]["series_id"] = series_id
        match_data["match_type"]["series_type"] = 1  # Bo3
        match_data["match_type"]["series_current_value"] = game_number
        
        # Mettre à jour la série dans le cache
        if series_id not in cache_data["series"]:
            cache_data["series"][series_id] = {
                "series_id": series_id,
                "match_ids": [],
                "previous_matches": [],
                "series_type": 1,  # Bo3
                "radiant_score": 0,
                "dire_score": 0,
                "last_updated": int(time.time())
            }
        
        # Ajouter ce match à la liste des matchs de la série s'il n'y est pas déjà
        if match_id not in cache_data["series"][series_id]["match_ids"]:
            cache_data["series"][series_id]["match_ids"].append(match_id)
        
        # Créer ou mettre à jour l'entrée dans previous_matches
        previous_match_entry = {
            "match_id": match_id,
            "radiant_team_name": match_data.get("radiant_team", {}).get("team_name", "Équipe Radiant"),
            "dire_team_name": match_data.get("dire_team", {}).get("team_name", "Équipe Dire"),
            "radiant_score": match_data.get("radiant_score", 0),
            "dire_score": match_data.get("dire_score", 0),
            "duration": match_data.get("duration", "0:00"),
            "total_kills": match_data.get("radiant_score", 0) + match_data.get("dire_score", 0),
            "game_number": game_number,
            "winner": match_data.get("winner"),
            "timestamp": match_data.get("start_time", int(time.time())),
            "status": match_data.get("status", "finished"),
            "status_tag": match_data.get("status_tag", "TERMINÉ")
        }
        
        # Vérifier si ce match existe déjà dans previous_matches
        exists = False
        for i, pm in enumerate(cache_data["series"][series_id]["previous_matches"]):
            if pm.get("match_id") == match_id:
                # Mettre à jour l'entrée existante
                cache_data["series"][series_id]["previous_matches"][i] = previous_match_entry
                exists = True
                break
        
        # Ajouter l'entrée si elle n'existe pas
        if not exists:
            cache_data["series"][series_id]["previous_matches"].append(previous_match_entry)
        
        # Trier les previous_matches par game_number
        cache_data["series"][series_id]["previous_matches"].sort(key=lambda m: m.get("game_number", 0))
        
        # Mettre à jour les scores de la série - compter les gagnants
        radiant_wins = sum(1 for pm in cache_data["series"][series_id]["previous_matches"] 
                          if pm.get("winner") == "radiant")
        dire_wins = sum(1 for pm in cache_data["series"][series_id]["previous_matches"] 
                       if pm.get("winner") == "dire")
        
        cache_data["series"][series_id]["radiant_score"] = radiant_wins
        cache_data["series"][series_id]["dire_score"] = dire_wins
        cache_data["series"][series_id]["last_updated"] = int(time.time())
        
        # Mettre à jour aussi les scores dans les matchs
        match_data["radiant_series_wins"] = radiant_wins
        match_data["dire_series_wins"] = dire_wins
        
        logger.info(f"Match {match_id} (Game {game_number}) associé à la série {series_id}")
    
    # Supprimer les séries orphelines (qui ont le même ID que le match)
    for series_id in list(live_data["series"].keys()):
        if series_id.startswith("s_") and series_id[2:] in live_data["matches"]:
            # Cette série a le même ID qu'un match, vérifier si elle a été migrée
            has_been_migrated = False
            for mapping in series_mappings.values():
                if mapping["series_id"] != series_id and series_id[2:] in series_mappings:
                    has_been_migrated = True
                    break
            
            if has_been_migrated:
                logger.info(f"Suppression de la série orpheline {series_id} (migrée)")
                del live_data["series"][series_id]
    
    # Sauvegarder les caches mis à jour
    save_cache(LIVE_DATA_FILE, live_data)
    save_cache(HISTORICAL_DATA_FILE, historical_data)
    
    logger.info("Correction du mappage des séries terminée")

def main():
    """Fonction principale"""
    print("===== Correction du mappage des séries =====")
    
    fix_series_mapping()
    
    print("\nCorrection terminée. Redémarrez le serveur pour appliquer les modifications.")

if __name__ == "__main__":
    main()
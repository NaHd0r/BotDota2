"""
Script pour corriger le statut d'un match en fonction de sa durée.
Ce script vérifie la durée d'un match et met à jour son statut en conséquence.
"""

import json
import os
import logging
import time
import re

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
CACHE_DIR = "cache"
LIVE_CACHE_FILE = os.path.join(CACHE_DIR, "live_series_cache.json")

def load_cache(file_path):
    """Charge un fichier de cache JSON"""
    try:
        if not os.path.exists(file_path):
            logger.warning(f"Le fichier {file_path} n'existe pas")
            return {}
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Cache chargé depuis {file_path}")
            return data
    except Exception as e:
        logger.error(f"Erreur lors du chargement du cache {file_path}: {e}")
        return {}

def save_cache(file_path, data):
    """Sauvegarde un fichier de cache JSON"""
    try:
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Cache sauvegardé dans {file_path}")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache {file_path}: {e}")

def parse_duration(duration_str):
    """
    Convertit une durée au format MM:SS en secondes
    
    Args:
        duration_str (str): Durée au format MM:SS
        
    Returns:
        int: Durée en secondes
    """
    if not duration_str:
        return 0
        
    # Format MM:SS
    match = re.match(r'(\d+):(\d+)', duration_str)
    if match:
        minutes, seconds = map(int, match.groups())
        return minutes * 60 + seconds
    
    return 0

def fix_match_status():
    """
    Corrige le statut des matchs en fonction de leur durée
    """
    # Charger le cache
    cache_data = load_cache(LIVE_CACHE_FILE)
    if not cache_data:
        logger.error("Impossible de charger le cache")
        return
    
    # Parcourir tous les matchs dans le cache
    matches = cache_data.get("matches", {})
    updated = False
    
    for match_id, match_data in matches.items():
        # Vérifier si le match est en cours
        if "duration" in match_data:
            duration_str = match_data["duration"]
            duration_seconds = parse_duration(duration_str)
            
            logger.info(f"Match {match_id} - Durée: {duration_str} ({duration_seconds} secondes)")
            
            # Si la durée est supérieure à 10 secondes, le match est en cours
            if duration_seconds >= 10:
                # Vérifier si le statut est incorrect
                current_status = match_data.get("status")
                current_status_tag = match_data.get("status_tag")
                
                if current_status != "active" or current_status_tag != "EN JEU":
                    logger.info(f"⚠️ Statut incorrect pour le match {match_id}: {current_status}/{current_status_tag}")
                    logger.info(f"⚠️ Durée: {duration_str} - Mise à jour du statut vers 'active/EN JEU'")
                    
                    # Mettre à jour le statut
                    match_data["status"] = "active"
                    match_data["status_tag"] = "EN JEU"
                    match_data["draft_phase"] = False
                    match_data["match_state"]["phase"] = "game"
                    
                    updated = True
                    logger.info(f"✅ Statut du match {match_id} mis à jour")
                else:
                    logger.info(f"✅ Le statut du match {match_id} est correct: {current_status}/{current_status_tag}")
    
    # Sauvegarder le cache si des modifications ont été effectuées
    if updated:
        cache_data["matches"] = matches
        save_cache(LIVE_CACHE_FILE, cache_data)
        logger.info("Cache mis à jour et sauvegardé")
    else:
        logger.info("Aucune modification nécessaire")

if __name__ == "__main__":
    fix_match_status()
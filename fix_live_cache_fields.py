#!/usr/bin/env python
"""
Script pour ajouter les champs manquants dans le cache live:
- duration (durée formatée)
- winner (vainqueur du match)
- total_kills (nombre total de kills)

Ce script complète les données du cache live en utilisant les informations 
disponibles dans les logs ou en les calculant à partir des données existantes.
"""

import json
import os
import logging
import time
from typing import Dict, Any, List, Optional

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

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Charge un fichier JSON"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du fichier {filepath}: {e}")
        return {}

def save_json_file(filepath: str, data: Dict[str, Any]) -> bool:
    """Sauvegarde des données dans un fichier JSON"""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Fichier {filepath} sauvegardé avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du fichier {filepath}: {e}")
        return False

def format_duration(seconds: float) -> str:
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

def get_match_completed_data(match_id: str) -> Optional[Dict[str, Any]]:
    """
    Recherche les données d'un match complété dans le cache des séries complétées
    
    Args:
        match_id: ID du match à rechercher
        
    Returns:
        Données du match si trouvées, None sinon
    """
    completed_cache = load_json_file(COMPLETED_SERIES_CACHE)
    
    for series_id, series_data in completed_cache.items():
        for match in series_data.get("matches", []):
            if match.get("match_id") == match_id:
                return match
                
    return None

def fix_live_cache_fields():
    """Ajoute les champs manquants dans le cache live"""
    live_cache = load_json_file(LIVE_SERIES_CACHE)
    updated = False
    
    for series_id, series_data in live_cache.items():
        matches = series_data.get("matches", [])
        updated_matches = []
        
        for match in matches:
            match_id = match.get("match_id")
            updated_match = match.copy()
            
            # Vérifier si c'est un match terminé
            match_outcome = match.get("match_outcome", 0)
            match_phase = match.get("match_phase")
            draft_phase = match.get("draft_phase", False)
            
            # Ajouter le champ total_kills s'il manque
            if "total_kills" not in updated_match and "radiant_score" in updated_match and "dire_score" in updated_match:
                radiant_score = updated_match.get("radiant_score", 0)
                dire_score = updated_match.get("dire_score", 0)
                updated_match["total_kills"] = radiant_score + dire_score
                logger.info(f"Ajout du champ total_kills={radiant_score + dire_score} pour le match {match_id}")
                updated = True
            
            # Ajouter le champ duration s'il manque
            if "duration" not in updated_match and "duration_formatted" in updated_match:
                updated_match["duration"] = updated_match["duration_formatted"]
                logger.info(f"Copie du champ duration depuis duration_formatted pour le match {match_id}")
                updated = True
            elif "duration" not in updated_match and "game_time" in updated_match:
                game_time = updated_match.get("game_time", 0)
                updated_match["duration"] = format_duration(game_time)
                logger.info(f"Ajout du champ duration={format_duration(game_time)} pour le match {match_id}")
                updated = True
            
            # Ajouter le champ winner s'il manque pour un match terminé
            if "winner" not in updated_match:
                if match_outcome == 2:  # Radiant win
                    updated_match["winner"] = "radiant"
                    logger.info(f"Ajout du champ winner=radiant pour le match {match_id}")
                    updated = True
                elif match_outcome == 3:  # Dire win
                    updated_match["winner"] = "dire"
                    logger.info(f"Ajout du champ winner=dire pour le match {match_id}")
                    updated = True
                else:
                    # Vérifier dans le cache des matches terminés
                    completed_match = get_match_completed_data(match_id)
                    if completed_match and "winner" in completed_match:
                        updated_match["winner"] = completed_match["winner"]
                        logger.info(f"Ajout du champ winner={completed_match['winner']} depuis le cache des matchs terminés pour le match {match_id}")
                        updated = True
            
            # Ajouter le champ match_phase s'il manque
            if "match_phase" not in updated_match:
                if draft_phase:
                    updated_match["match_phase"] = "draft"
                    logger.info(f"Ajout du champ match_phase=draft pour le match {match_id}")
                elif match_outcome in [2, 3]:
                    updated_match["match_phase"] = "finished"
                    logger.info(f"Ajout du champ match_phase=finished pour le match {match_id}")
                else:
                    updated_match["match_phase"] = "game"
                    logger.info(f"Ajout du champ match_phase=game pour le match {match_id}")
                updated = True
            
            updated_matches.append(updated_match)
        
        # Mettre à jour les matches dans la série
        if matches != updated_matches:
            series_data["matches"] = updated_matches
    
    # Sauvegarder le cache mis à jour si des modifications ont été effectuées
    if updated:
        save_json_file(LIVE_SERIES_CACHE, live_cache)
        logger.info("Cache des séries en direct mis à jour avec les champs manquants")
    else:
        logger.info("Aucune modification nécessaire dans le cache des séries en direct")

def fix_series_cache_previous_matches():
    """Ajoute les champs manquants dans les previous_matches du cache principal des séries"""
    series_cache = load_json_file(SERIES_CACHE)
    updated = False
    
    for series_id, series_data in series_cache.items():
        previous_matches = series_data.get("previous_matches", [])
        updated_previous_matches = []
        
        for match in previous_matches:
            match_id = match.get("match_id")
            updated_match = match.copy()
            
            # Ajouter le champ total_kills s'il manque
            if "total_kills" not in updated_match and "radiant_score" in updated_match and "dire_score" in updated_match:
                radiant_score = updated_match.get("radiant_score", 0)
                dire_score = updated_match.get("dire_score", 0)
                updated_match["total_kills"] = radiant_score + dire_score
                logger.info(f"Ajout du champ total_kills={radiant_score + dire_score} pour le match précédent {match_id}")
                updated = True
            
            # Rechercher des informations complémentaires dans le cache des séries complétées
            if "winner" not in updated_match or "duration" not in updated_match:
                completed_match = get_match_completed_data(match_id)
                if completed_match:
                    # Ajouter le champ winner s'il manque
                    if "winner" not in updated_match and "winner" in completed_match:
                        updated_match["winner"] = completed_match["winner"]
                        logger.info(f"Ajout du champ winner={completed_match['winner']} depuis le cache des matchs terminés")
                        updated = True
                    
                    # Ajouter le champ duration s'il manque
                    if "duration" not in updated_match and "duration" in completed_match:
                        updated_match["duration"] = completed_match["duration"]
                        logger.info(f"Ajout du champ duration={completed_match['duration']} depuis le cache des matchs terminés")
                        updated = True
            
            updated_previous_matches.append(updated_match)
        
        # Mettre à jour les previous_matches dans la série
        if previous_matches != updated_previous_matches:
            series_data["previous_matches"] = updated_previous_matches
            updated = True
    
    # Sauvegarder le cache mis à jour si des modifications ont été effectuées
    if updated:
        save_json_file(SERIES_CACHE, series_cache)
        logger.info("Cache principal des séries mis à jour avec les champs manquants")
    else:
        logger.info("Aucune modification nécessaire dans le cache principal des séries")

def main():
    """Fonction principale"""
    logger.info("Démarrage de la correction des champs manquants dans les caches")
    
    # Ajouter les champs manquants dans le cache live
    fix_live_cache_fields()
    
    # Ajouter les champs manquants dans les previous_matches du cache principal
    fix_series_cache_previous_matches()
    
    logger.info("Correction des champs manquants terminée")

if __name__ == "__main__":
    main()
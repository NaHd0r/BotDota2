#!/usr/bin/env python3
"""
Script pour corriger les previous_matches dans les séries du cache.

Ce script s'assure que tous les matchs d'une série sont inclus dans le champ
previous_matches de cette série dans le cache.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_cache(file_path: str) -> Dict[str, Any]:
    """Charge le cache JSON depuis un fichier"""
    if not os.path.exists(file_path):
        logger.error(f"Le fichier {file_path} n'existe pas")
        return {}
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erreur lors du chargement du cache {file_path}: {e}")
        return {}

def save_cache(file_path: str, data: Dict[str, Any]) -> bool:
    """Sauvegarde le cache JSON dans un fichier"""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Cache sauvegardé dans {file_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache {file_path}: {e}")
        return False

def fix_series_previous_matches(series_id: str = None):
    """
    Corrige les matchs précédents dans les séries du cache.
    
    Si series_id est fourni, ne corrige que cette série spécifique.
    Sinon, corrige toutes les séries.
    """
    # Charger les données
    live_cache_path = 'cache/live_data.json'
    historical_cache_path = 'cache/historical_data.json'
    
    live_cache = load_cache(live_cache_path)
    historical_cache = load_cache(historical_cache_path)
    
    # Valider les données chargées
    if not live_cache or 'matches' not in live_cache or 'series' not in live_cache:
        logger.error("Format de cache live invalide ou vide")
        return False
    
    if not historical_cache or 'matches' not in historical_cache or 'series' not in historical_cache:
        logger.error("Format de cache historique invalide ou vide")
        return False
    
    # Fonction pour corriger une série spécifique
    def fix_single_series(cache_data, series_id):
        if series_id not in cache_data['series']:
            logger.warning(f"Série {series_id} non trouvée dans le cache")
            return False
        
        series_data = cache_data['series'][series_id]
        match_ids = series_data.get('match_ids', [])
        
        if not match_ids:
            logger.warning(f"Série {series_id} n'a pas de match_ids définis")
            return False
        
        # Initialiser ou réinitialiser les previous_matches
        series_data['previous_matches'] = []
        
        for match_id in match_ids:
            if match_id not in cache_data['matches']:
                logger.warning(f"Match {match_id} non trouvé dans le cache")
                continue
            
            match_data = cache_data['matches'][match_id]
            
            # Extraire le numéro de jeu dans la série
            game_number = 1
            if 'match_type' in match_data and 'series_current_value' in match_data['match_type']:
                game_number = match_data['match_type']['series_current_value']
            
            # Créer une entrée formatée pour le match
            match_entry = {
                "match_id": match_id,
                "radiant_team_name": match_data.get("radiant_team", {}).get("team_name", "Équipe Radiant"),
                "dire_team_name": match_data.get("dire_team", {}).get("team_name", "Équipe Dire"),
                "radiant_score": match_data.get("radiant_score", 0),
                "dire_score": match_data.get("dire_score", 0),
                "duration": match_data.get("duration", "0:00"),
                "total_kills": match_data.get("radiant_score", 0) + match_data.get("dire_score", 0),
                "game_number": game_number,
                "winner": match_data.get("winner", "tie"),
                "status": match_data.get("status", ""),
                "status_tag": match_data.get("status_tag", ""),
                "timestamp": match_data.get("start_time", int(time.time()))
            }
            
            series_data['previous_matches'].append(match_entry)
        
        # Trier les matchs par numéro de jeu
        series_data['previous_matches'].sort(key=lambda m: m.get('game_number', 0))
        
        logger.info(f"Série {series_id} mise à jour avec {len(series_data['previous_matches'])} matchs précédents")
        for i, match in enumerate(series_data['previous_matches']):
            logger.info(f"  - Match #{i+1}: {match['match_id']} (Game {match['game_number']})")
        
        return True
    
    # Corriger les séries
    if series_id:
        # Corriger une série spécifique
        live_updated = fix_single_series(live_cache, series_id)
        historical_updated = fix_single_series(historical_cache, series_id)
    else:
        # Corriger toutes les séries
        live_updated = False
        historical_updated = False
        
        for s_id in live_cache['series'].keys():
            if fix_single_series(live_cache, s_id):
                live_updated = True
        
        for s_id in historical_cache['series'].keys():
            if fix_single_series(historical_cache, s_id):
                historical_updated = True
    
    # Sauvegarder les caches si modifiés
    if live_updated:
        save_cache(live_cache_path, live_cache)
    
    if historical_updated:
        save_cache(historical_cache_path, historical_cache)
    
    return live_updated or historical_updated

if __name__ == "__main__":
    # Vérifier si un ID de série est fourni en argument
    series_id = None
    if len(sys.argv) > 1:
        series_id = sys.argv[1]
        logger.info(f"Correction de la série spécifique: {series_id}")
    else:
        logger.info("Correction de toutes les séries")
    
    import time  # Importé ici pour éviter l'erreur dans la fonction
    
    # Correction des séries
    if fix_series_previous_matches(series_id):
        print("\nCorrection terminée. Redémarrez le serveur pour appliquer les modifications.")
    else:
        print("\nAucune modification n'a été effectuée.")
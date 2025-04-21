import json
import os
import time
from datetime import datetime

# Chemin du fichier de cache
CACHE_DIR = "cache"
LIVE_SERIES_CACHE_FILE = os.path.join(CACHE_DIR, "live_series_cache.json")
SERIES_MATCHES_MAPPING_FILE = os.path.join(CACHE_DIR, "series_matches_mapping.json")

def load_cache(file_path):
    """Charge un fichier de cache JSON"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Erreur lors du chargement du cache {file_path}: {e}")
        return {}

def save_cache(file_path, cache_data):
    """Sauvegarde un fichier de cache JSON"""
    try:
        # Créer le répertoire de cache s'il n'existe pas
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
        print(f"Cache sauvegardé avec succès: {file_path}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du cache {file_path}: {e}")

def simulate_live_match():
    """Simule un match en direct à la game 2 avec un score de série 1-0"""
    # Générer un match_id fictif
    match_id = "9999999999"
    series_id = f"s_{match_id}"
    
    # Charger le mapping des séries
    series_mapping = load_cache(SERIES_MATCHES_MAPPING_FILE)
    
    # Ajouter l'entrée de mapping pour notre série simulée
    if series_id not in series_mapping:
        series_mapping[series_id] = [match_id]
    
    # Sauvegarder le mapping mis à jour
    save_cache(SERIES_MATCHES_MAPPING_FILE, series_mapping)
    
    # Charger le cache des séries en direct
    live_cache = load_cache(LIVE_SERIES_CACHE_FILE)
    
    # Créer une série simulée (game 2 avec score 1-0)
    simulated_series = {
        "match_id": match_id,
        "series_id": series_id,
        "league_id": 17911,  # Mad Dogs League
        "radiant_team_name": "Team Simulation",
        "dire_team_name": "Test Opponents",
        "radiant_team_id": 12345,
        "dire_team_id": 67890,
        "radiant_series_wins": 1,
        "dire_series_wins": 0,
        "game_number": 2,
        "series_type": 1,  # BO3
        "series_max_games": 3,
        "match_type": {
            "series_type": 1,
            "series_max_value": 3,
            "series_current_value": 2,
            "series_id": series_id,
            "radiant_score": 1,
            "dire_score": 0
        },
        "radiant_score": 12,
        "dire_score": 8,
        "duration": 1260,  # 21 minutes
        "duration_formatted": "21:00",
        "state": {
            "phase": "game",
            "winner": None
        },
        "last_updated": datetime.now().timestamp(),
        "previous_games": [
            {
                "match_id": "9999999998",
                "game_number": 1,
                "radiant_score": 42,
                "dire_score": 20,
                "duration": 2400,
                "duration_formatted": "40:00",
                "winner": "radiant",
                "radiant_team_name": "Team Simulation",
                "dire_team_name": "Test Opponents"
            }
        ]
    }
    
    # Ajouter notre série simulée au cache
    live_cache[series_id] = simulated_series
    
    # Sauvegarder le cache mis à jour
    save_cache(LIVE_SERIES_CACHE_FILE, live_cache)
    
    print("Match en direct simulé créé avec succès!")
    print(f"- ID de match: {match_id}")
    print(f"- ID de série: {series_id}")
    print(f"- Score de série: 1-0 (Game 2 sur 3)")
    print(f"- Équipes: Team Simulation vs Test Opponents")
    print(f"- Ligue: 17911 (Mad Dogs League)")
    print("Rafraîchissez l'interface web pour voir le match.")

# Exécuter la simulation lorsque le script est lancé directement
if __name__ == "__main__":
    simulate_live_match()
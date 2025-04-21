"""
Script pour extraire les données d'une série Dotabuff spécifique
et les ajouter au cache series_matches_mapping.json
"""

import os
import json
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from browser_simulator import BrowserSession

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chemin du fichier de cache
CACHE_DIR = "cache"
SERIES_MAPPING_FILE = os.path.join(CACHE_DIR, "series_matches_mapping.json")

def load_cache():
    """Charge le cache existant ou crée un nouveau dictionnaire"""
    try:
        if os.path.exists(SERIES_MAPPING_FILE):
            with open(SERIES_MAPPING_FILE, 'r') as f:
                data = json.load(f)
                logger.info(f"Cache chargé, {len(data)} séries trouvées")
                return data
        else:
            logger.warning(f"Fichier {SERIES_MAPPING_FILE} non trouvé, création d'un nouveau cache")
            return {}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du cache: {e}")
        return {}

def save_cache(data):
    """Sauvegarde le cache mis à jour"""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(SERIES_MAPPING_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Cache sauvegardé, {len(data)} séries au total")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache: {e}")
        return False

def extract_series_data(series_id: str) -> Optional[Dict]:
    """
    Extrait les données d'une série Dotabuff
    
    Args:
        series_id: ID de la série Dotabuff
        
    Returns:
        Dictionnaire contenant les informations de la série, ou None en cas d'erreur
    """
    try:
        url = f"https://www.dotabuff.com/esports/series/{series_id}"
        
        logger.info(f"Récupération des données pour la série {series_id} depuis {url}")
        
        # Utiliser notre simulateur de navigateur pour contourner les restrictions
        browser = BrowserSession()
        response = browser.get(url)
        
        if not response or response.status_code != 200:
            status_code = response.status_code if response else "Aucune réponse"
            logger.error(f"Erreur HTTP {status_code} lors de la récupération de la série")
            return None
        
        # Parser le HTML avec BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraction du titre (équipes)
        logger.info("Extraction du titre et des équipes")
        title_element = soup.select_one("h1.esports-title")
        series_name = title_element.text.strip() if title_element else "Unknown Series"
        print(f"Titre de la série: {series_name}")
        
        # Extraire les noms des équipes depuis le titre
        team_names = series_name.split(' vs ') if ' vs ' in series_name else []
        team1_name = team_names[0].strip() if len(team_names) > 0 else "Team 1"
        team2_name = team_names[1].strip() if len(team_names) > 1 else "Team 2"
        print(f"Équipe 1: {team1_name}")
        print(f"Équipe 2: {team2_name}")
        
        # Récupération des matchs de la série
        logger.info("Extraction des matchs")
        matches = []
        match_links = soup.select("table.series-matches a[href^='/matches/']")
        
        for i, link in enumerate(match_links):
            match_url = link.get('href', '')
            match_id = match_url.split('/')[-1] if match_url and isinstance(match_url, str) else None
            
            if match_id and match_id.isdigit():
                game_title = link.text.strip()
                game_number = i + 1  # Par défaut, utiliser l'ordre dans la liste
                
                # Si le titre du lien contient "Game X", extraire le numéro
                if "Game " in game_title:
                    try:
                        game_number = int(game_title.split("Game ")[1].split(":")[0].strip())
                    except (ValueError, IndexError):
                        pass  # Garder la valeur par défaut si l'extraction échoue
                
                match_data = {
                    "game_number": game_number,
                    "match_id": match_id
                }
                matches.append(match_data)
                print(f"Match {game_number}: {match_id}")
        
        if not matches:
            logger.warning("Aucun match trouvé pour cette série")
            print("ATTENTION: Aucun match trouvé!")
        
        # Construction du résultat
        series_data = {
            "series_id": series_id,
            "series_name": series_name,
            "team1_name": team1_name, 
            "team2_name": team2_name,
            "matches": matches
        }
        
        return series_data
    
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des données de la série: {e}")
        print(f"ERREUR: {e}")
        return None

def update_cache_with_series(series_id):
    """
    Met à jour le cache avec les données d'une série Dotabuff
    
    Args:
        series_id: ID de la série Dotabuff
        
    Returns:
        True si la mise à jour a réussi, False sinon
    """
    # Extraire les données de la série
    series_data = extract_series_data(series_id)
    
    if not series_data:
        print(f"Impossible d'extraire les données pour la série {series_id}")
        return False
    
    # Charger le cache actuel
    cache = load_cache()
    
    # Ajouter ou mettre à jour l'entrée pour cette série
    cache[series_id] = series_data
    
    # Sauvegarder le cache mis à jour
    success = save_cache(cache)
    
    if success:
        print(f"Série {series_id} ajoutée au cache avec succès!")
        return True
    else:
        print(f"Erreur lors de la sauvegarde du cache pour la série {series_id}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        series_id = sys.argv[1]
    else:
        series_id = "2666289"  # ID de série par défaut
    
    print(f"Extraction des données pour la série Dotabuff {series_id}...")
    result = update_cache_with_series(series_id)
    
    if result:
        print(f"Données de la série {series_id} extraites et ajoutées au cache avec succès.")
    else:
        print(f"Échec de l'extraction des données pour la série {series_id}.")
"""
Module pour récupérer les informations de séries depuis Dotabuff.
Ce module utilise trafilatura et BeautifulSoup pour extraire les données d'une série Dotabuff.
"""

import os
import json
import time
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

# Import du module de simulation de navigateur
from browser_simulator import BrowserSession

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
CACHE_DIR = "cache"
SERIES_MAPPING_FILE = os.path.join(CACHE_DIR, "series_matches_mapping.json")


def load_series_mapping() -> Dict:
    """
    Charge le mapping des séries depuis le fichier de cache
    
    Returns:
        Dictionnaire contenant le mapping des séries
    """
    try:
        if os.path.exists(SERIES_MAPPING_FILE):
            with open(SERIES_MAPPING_FILE, 'r') as f:
                mapping = json.load(f)
                logger.info(f"Mapping des séries chargé, {len(mapping)} séries trouvées")
                return mapping
        else:
            logger.warning(f"Fichier de mapping {SERIES_MAPPING_FILE} non trouvé, création d'un nouveau mapping")
            return {}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du mapping des séries: {e}")
        return {}


def save_series_mapping(mapping: Dict) -> bool:
    """
    Sauvegarde le mapping des séries dans le fichier de cache
    
    Args:
        mapping: Dictionnaire contenant le mapping des séries
        
    Returns:
        Bool indiquant si la sauvegarde a réussi
    """
    try:
        # Créer le répertoire de cache s'il n'existe pas
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        with open(SERIES_MAPPING_FILE, 'w') as f:
            json.dump(mapping, f, indent=2)
            logger.info(f"Mapping des séries sauvegardé, {len(mapping)} séries")
            return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du mapping des séries: {e}")
        return False


def extract_related_series(soup, current_series_id: str) -> List[str]:
    """
    Extrait les IDs des séries liées (OTHER SERIES) depuis la page d'une série Dotabuff
    
    Args:
        soup: L'objet BeautifulSoup de la page
        current_series_id: L'ID de la série actuelle (pour l'exclure des résultats)
        
    Returns:
        Liste des IDs des séries liées
    """
    related_series_ids = []
    
    try:
        # Chercher la section "OTHER SERIES"
        other_series_section = soup.find("h2", text=lambda text: text and "OTHER SERIES" in text)
        
        if not other_series_section:
            logger.info("Pas de section 'OTHER SERIES' trouvée")
            return []
            
        # Trouver la table qui contient les liens vers d'autres séries
        series_table = other_series_section.find_next("table")
        
        if not series_table:
            logger.info("Table des autres séries non trouvée")
            return []
            
        # Extraire tous les liens vers des séries
        series_links = series_table.select("a[href^='/esports/series/']")
        
        for link in series_links:
            href = link.get("href", "")
            if href and "/esports/series/" in href:
                series_id = href.split("/")[-1]
                
                # Vérifier que c'est bien un ID numérique et pas la série actuelle
                if series_id.isdigit() and series_id != current_series_id and series_id not in related_series_ids:
                    related_series_ids.append(series_id)
                    
        logger.info(f"Trouvé {len(related_series_ids)} séries liées")
        return related_series_ids
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des séries liées: {str(e)}")
        return []

def scrape_dotabuff_series(series_id: str) -> Optional[Dict]:
    """
    Récupère les informations d'une série depuis Dotabuff
    
    Args:
        series_id: ID de la série Dotabuff
        
    Returns:
        Dictionnaire contenant les informations de la série ou None en cas d'erreur
    """
    url = f"https://www.dotabuff.com/esports/series/{series_id}"
    session = BrowserSession()
    
    try:
        logger.info(f"Récupération des données de la série {series_id} depuis Dotabuff...")
        response = session.get(url)
        
        if not response or response.status_code != 200:
            logger.error(f"Erreur lors de la récupération de la série {series_id}: {response.status_code if response else 'No response'}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraction du titre de la série (équipes)
        title_element = soup.select_one("h1.esports-title")
        series_name = title_element.text.strip() if title_element else "Unknown Series"
        
        # Tentative d'extraction des noms d'équipes depuis le titre
        team_names = series_name.split(' vs ') if ' vs ' in series_name else []
        team1_name = team_names[0].strip() if len(team_names) > 0 else "Team 1"
        team2_name = team_names[1].strip() if len(team_names) > 1 else "Team 2"
        
        # Récupération des matchs de la série
        matches = []
        match_links = soup.select("table.series-matches a[href^='/matches/']")
        
        for i, link in enumerate(match_links):
            match_url = link.get('href', '')
            match_id = match_url.split('/')[-1] if match_url and isinstance(match_url, str) else None
            
            if match_id and match_id.isdigit():
                matches.append({
                    "game_number": i + 1,
                    "match_id": match_id,
                    "match_url": f"https://www.dotabuff.com{match_url}"
                })
        
        # Extraction des séries liées
        related_series = extract_related_series(soup, series_id)
        
        # Construction du résultat
        result = {
            "series_id": series_id,
            "series_name": series_name,
            "team1_name": team1_name,
            "team2_name": team2_name,
            "dotabuff_url": url,
            "matches": matches,
            "related_series": related_series,  # Ajout des séries liées
            "league_id": "",  # À déterminer ultérieurement ou à mettre à jour manuellement
            "scrape_time": int(time.time())
        }
        
        logger.info(f"Série {series_id} récupérée avec succès, {len(matches)} matchs trouvés et {len(related_series)} séries liées")
        return result
    
    except Exception as e:
        logger.error(f"Erreur lors du scraping de la série {series_id}: {str(e)}")
        return None


def add_or_update_series(series_id: str, process_related: bool = True) -> Dict:
    """
    Récupère les informations d'une série depuis Dotabuff et les ajoute au mapping.
    Peut également traiter les séries liées si process_related est True.
    
    Args:
        series_id: ID de la série Dotabuff
        process_related: Si True, les séries liées seront également récupérées et ajoutées au mapping
        
    Returns:
        Dict contenant des informations sur le résultat de l'opération:
            - success: True si l'opération principale a réussi
            - series_processed: Liste des séries traitées avec succès
            - series_failed: Liste des séries qui ont échoué
            - total_matches: Nombre total de matchs récupérés
    """
    # Initialisation du résultat
    result = {
        "success": False,
        "series_processed": [],
        "series_failed": [],
        "total_matches": 0
    }
    
    # Récupération des données de la série principale
    series_data = scrape_dotabuff_series(series_id)
    
    if not series_data:
        result["series_failed"].append(series_id)
        return result
    
    # Ajout de la série au mapping
    mapping = load_series_mapping()
    mapping[series_id] = series_data
    
    # Mise à jour du résultat
    result["success"] = True
    result["series_processed"].append(series_id)
    result["total_matches"] += len(series_data.get("matches", []))
    
    # Traitement des séries liées si demandé
    if process_related and "related_series" in series_data:
        related_series = series_data["related_series"]
        
        logger.info(f"Traitement de {len(related_series)} séries liées...")
        
        for related_id in related_series:
            # Vérifier si la série liée existe déjà dans le mapping
            if related_id in mapping:
                logger.info(f"Série liée {related_id} déjà dans le mapping, ignorée")
                continue
                
            # Récupération des données de la série liée
            related_data = scrape_dotabuff_series(related_id)
            
            if related_data:
                mapping[related_id] = related_data
                result["series_processed"].append(related_id)
                result["total_matches"] += len(related_data.get("matches", []))
                # Ajout d'un délai pour éviter d'être bloqué par Dotabuff
                time.sleep(2)
            else:
                result["series_failed"].append(related_id)
    
    # Sauvegarde du mapping mis à jour
    save_success = save_series_mapping(mapping)
    
    # Si la sauvegarde a échoué, on considère l'opération comme échouée
    if not save_success:
        result["success"] = False
    
    logger.info(f"Récupération terminée: {len(result['series_processed'])} séries traitées, "
                f"{len(result['series_failed'])} séries échouées, "
                f"{result['total_matches']} matchs au total")
    
    return result


if __name__ == "__main__":
    # Test du module
    import sys
    
    if len(sys.argv) < 2:
        series_id = "2666210"  # Série par défaut pour les tests
        print(f"Aucun ID de série fourni, utilisation de l'ID par défaut: {series_id}")
    else:
        series_id = sys.argv[1]
    
    print(f"Récupération des informations pour la série {series_id}...")
    result = add_or_update_series(series_id)
    
    if result:
        print(f"Série {series_id} ajoutée avec succès au mapping!")
    else:
        print(f"Erreur lors de l'ajout de la série {series_id}.")
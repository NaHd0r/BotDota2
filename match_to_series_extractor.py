"""
Module pour extraire les informations de série Dotabuff à partir d'un match ID.
Ce module permet de faire le lien entre un match ID et sa série Dotabuff associée.
"""

import os
import json
import time
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple, Any

# Import du module de simulation de navigateur
from browser_simulator import BrowserSession

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
CACHE_DIR = "cache"
SERIES_MAPPING_FILE = os.path.join(CACHE_DIR, "series_matches_mapping.json")
MATCH_SERIES_FILE = os.path.join(CACHE_DIR, "match_to_series_mapping.json")

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

def load_match_to_series_mapping() -> Dict:
    """
    Charge le mapping des matchs vers les séries depuis le fichier de cache
    
    Returns:
        Dictionnaire contenant le mapping des matchs vers les séries
    """
    try:
        if os.path.exists(MATCH_SERIES_FILE):
            with open(MATCH_SERIES_FILE, 'r') as f:
                mapping = json.load(f)
                logger.info(f"Mapping match→series chargé, {len(mapping)} matchs trouvés")
                return mapping
        else:
            logger.warning(f"Fichier de mapping {MATCH_SERIES_FILE} non trouvé, création d'un nouveau mapping")
            return {}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du mapping match→series: {e}")
        return {}

def save_match_to_series_mapping(mapping: Dict) -> bool:
    """
    Sauvegarde le mapping des matchs vers les séries dans le fichier de cache
    
    Args:
        mapping: Dictionnaire contenant le mapping des matchs vers les séries
        
    Returns:
        Bool indiquant si la sauvegarde a réussi
    """
    try:
        # Créer le répertoire de cache s'il n'existe pas
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        with open(MATCH_SERIES_FILE, 'w') as f:
            json.dump(mapping, f, indent=2)
            logger.info(f"Mapping match→series sauvegardé, {len(mapping)} matchs")
            return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du mapping match→series: {e}")
        return False

def get_dotabuff_series_from_match(match_id: str) -> Optional[str]:
    """
    Récupère l'ID de série Dotabuff pour un match donné
    
    Args:
        match_id: ID du match Dota 2
        
    Returns:
        ID de la série Dotabuff ou None si non trouvé
    """
    try:
        # Vérifier si le match est déjà dans notre mapping
        match_mapping = load_match_to_series_mapping()
        if match_id in match_mapping:
            logger.info(f"Match {match_id} trouvé dans le mapping, série: {match_mapping[match_id]}")
            return match_mapping[match_id]
        
        # Créer une session de navigateur simulé
        session = BrowserSession()
        
        # URL de la page du match sur Dotabuff
        url = f"https://www.dotabuff.com/matches/{match_id}"
        
        logger.info(f"Récupération de la page du match {match_id} depuis Dotabuff...")
        response = session.get(url)
        
        if not response or response.status_code != 200:
            logger.error(f"Erreur lors de la récupération du match {match_id}: {response.status_code if response else 'No response'}")
            return None
        
        # Analyser la page pour trouver le lien vers la série
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher le lien vers la série dans la page
        series_link = soup.select_one("a[href^='/esports/series/']")
        
        if not series_link:
            logger.warning(f"Aucun lien vers une série trouvé pour le match {match_id}")
            return None
        
        # Extraire l'ID de série du lien
        href = series_link.get('href', '')
        if not href or '/esports/series/' not in href:
            logger.warning(f"Format de lien de série invalide: {href}")
            return None
        
        series_id = href.split('/')[-1]
        
        # Vérifier que l'ID est numérique
        if not series_id or not series_id.isdigit():
            logger.warning(f"ID de série non numérique: {series_id}")
            return None
        
        # Ajouter au mapping
        match_mapping[match_id] = series_id
        save_match_to_series_mapping(match_mapping)
        
        logger.info(f"Série Dotabuff trouvée pour le match {match_id}: {series_id}")
        return series_id
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la série pour le match {match_id}: {e}")
        return None

def create_manual_series_mapping(series_data: Dict) -> Dict:
    """
    Crée un mapping manuel entre des matchs et leurs séries
    
    Args:
        series_data: Dictionnaire contenant les séries et leurs matchs
        Exemple:
        {
            "8257889151": {
                "series_id": "2666289",
                "matches": ["8257889151", "8257938792"]
            },
            "2666289": {
                "matches": [
                    {"match_id": "8257889151", "game_number": 1},
                    {"match_id": "8257938792", "game_number": 2}
                ]
            }
        }
        
    Returns:
        Dictionnaire indiquant le succès de l'opération et les détails
    """
    try:
        # Charger les mappings existants
        series_mapping = load_series_mapping()
        match_to_series = load_match_to_series_mapping()
        
        # Compteurs pour le rapport
        matches_ajoutés = 0
        series_ajoutées = 0
        
        # Traiter chaque clé dans les données fournies
        for key, data in series_data.items():
            if "series_id" in data:
                # Cas 1: Entrée de type match-to-series
                match_id = key
                series_id = data["series_id"]
                match_to_series[match_id] = series_id
                
                # Si la série a une liste de matchs, les ajouter aussi
                if "matches" in data and isinstance(data["matches"], list):
                    for other_match in data["matches"]:
                        if isinstance(other_match, str) and other_match != match_id:
                            match_to_series[other_match] = series_id
                            matches_ajoutés += 1
                
                matches_ajoutés += 1
                
            elif "matches" in data and isinstance(data["matches"], list):
                # Cas 2: Entrée de type série avec matchs
                series_id = key
                
                # Créer ou mettre à jour l'entrée de série
                if series_id not in series_mapping:
                    series_mapping[series_id] = {
                        "series_id": series_id,
                        "series_name": data.get("series_name", f"Série {series_id}"),
                        "matches": [],
                        "scrape_time": int(time.time())
                    }
                    series_ajoutées += 1
                
                # Ajouter les matchs à la série
                matches = []
                for match_entry in data["matches"]:
                    if isinstance(match_entry, dict) and "match_id" in match_entry:
                        match_id = match_entry["match_id"]
                        game_number = match_entry.get("game_number", 1)
                        
                        # Ajouter au mapping match→series
                        match_to_series[match_id] = series_id
                        
                        # Ajouter à la liste des matchs de la série
                        matches.append({
                            "match_id": match_id,
                            "game_number": game_number,
                            "match_url": f"https://www.dotabuff.com/matches/{match_id}"
                        })
                        
                        matches_ajoutés += 1
                
                # Mettre à jour la liste des matchs dans la série
                if matches:
                    series_mapping[series_id]["matches"] = matches
        
        # Sauvegarder les mappings
        save_series_mapping(series_mapping)
        save_match_to_series_mapping(match_to_series)
        
        return {
            "success": True,
            "matches_ajoutés": matches_ajoutés,
            "series_ajoutées": series_ajoutées,
            "series_mapping_size": len(series_mapping),
            "match_to_series_size": len(match_to_series)
        }
    
    except Exception as e:
        logger.error(f"Erreur lors de la création du mapping manuel: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def list_all_series_mappings() -> Dict[str, Dict[str, Any]]:
    """
    Liste tous les mappings de séries disponibles dans le cache
    
    Returns:
        Dictionnaire contenant tous les mappings de séries
    """
    try:
        # Charger les mappings
        series_mapping = load_series_mapping()
        match_to_series = load_match_to_series_mapping()
        
        # Créer un rapport
        result = {
            "success": True,
            "series_count": len(series_mapping),
            "match_mapping_count": len(match_to_series),
            "series": {},
            "match_to_series": {}
        }
        
        # Limite à 5 entrées de chaque pour ne pas surcharger la sortie
        sample_series = list(series_mapping.keys())[:5]
        sample_matches = list(match_to_series.keys())[:5]
        
        # Ajouter des échantillons
        for sid in sample_series:
            result["series"][sid] = series_mapping[sid]
        
        for mid in sample_matches:
            result["match_to_series"][mid] = match_to_series[mid]
        
        return result
    
    except Exception as e:
        logger.error(f"Erreur lors de la liste des mappings: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def process_match_id_list(match_id_str: str, series_id: str) -> Dict:
    """
    Traite une liste de match IDs et les associe à un ID de série
    
    Args:
        match_id_str: Chaîne contenant les IDs de match séparés par des virgules
        series_id: ID de série auquel associer ces matchs
        
    Returns:
        Dictionnaire avec le résultat de l'opération
    """
    try:
        # Extraire les IDs de match
        match_ids = [m.strip() for m in match_id_str.split(',') if m.strip().isdigit()]
        
        if not match_ids:
            return {
                "success": False,
                "error": "Aucun ID de match valide trouvé dans la chaîne"
            }
        
        logger.info(f"Association de {len(match_ids)} matchs à la série {series_id}")
        
        # Construire les données de mapping
        series_data = {
            series_id: {
                "matches": []
            }
        }
        
        # Pour chaque match, créer une entrée
        for i, match_id in enumerate(match_ids):
            # Ajouter à la structure de série
            series_data[series_id]["matches"].append({
                "match_id": match_id,
                "game_number": i + 1
            })
            
            # Ajouter aussi une entrée match→serie
            series_data[match_id] = {
                "series_id": series_id,
                "matches": match_ids
            }
        
        # Créer le mapping
        result = create_manual_series_mapping(series_data)
        
        if result["success"]:
            result["message"] = f"{len(match_ids)} matchs associés à la série {series_id}"
            
        return result
    
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la liste de matchs: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# Test function
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python match_to_series_extractor.py <match_id>")
        sys.exit(1)
        
    match_id = sys.argv[1]
    print(f"Recherche de série pour le match {match_id}...")
    
    series_id = get_dotabuff_series_from_match(match_id)
    if series_id:
        print(f"Série trouvée: {series_id}")
    else:
        print(f"Aucune série trouvée pour le match {match_id}")
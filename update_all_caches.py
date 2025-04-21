"""
Script pour mettre à jour tous les fichiers de cache pour utiliser le format
d'ID de série standardisé avec le préfixe "s_" pour les séries générées par notre système.

Ce script traite tous les fichiers de cache utilisés par l'application :
- series_cache.json (cache principal)
- live_series_cache.json (cache secondaire)
- completed_series_cache.json (cache des séries terminées)
- series_matches_mapping.json (mapping séries → matches)
"""

import json
import os
import logging
import re

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
SERIES_CACHE_FILE = 'cache/series_cache.json'
LIVE_SERIES_CACHE_FILE = 'cache/live_series_cache.json'
COMPLETED_SERIES_CACHE_FILE = 'cache/completed_series_cache.json'
SERIES_MAPPING_FILE = 'cache/series_matches_mapping.json'

def is_generated_series_id(series_id):
    """
    Détermine si un ID de série a été généré par notre système.
    
    Args:
        series_id (str): ID de série à vérifier
        
    Returns:
        bool: True si l'ID est généré par notre système, False sinon
    """
    # Si l'ID commence déjà par "s_", c'est déjà au nouveau format
    if str(series_id).startswith("s_"):
        return False
    
    # Si l'ID est numérique et correspond à un format de matchID, c'est généré par notre système
    return re.match(r'^\d{10}$', str(series_id)) is not None

def update_series_in_data(data, old_series_id, new_series_id):
    """
    Met à jour l'ID de série dans les données
    
    Args:
        data (dict): Données à mettre à jour
        old_series_id (str): Ancien ID de série
        new_series_id (str): Nouvel ID de série
        
    Returns:
        dict: Données mises à jour
    """
    # Si les données ont un champ series_id, le mettre à jour
    if "series_id" in data:
        data["series_id"] = new_series_id
    
    # Mettre à jour les références dans les matches
    if "matches" in data:
        for match in data["matches"]:
            if "series_info" in match and match["series_info"].get("series_id") == old_series_id:
                match["series_info"]["series_id"] = new_series_id
    
    # Mettre à jour les références dans previous_matches
    if "previous_matches" in data:
        for match in data["previous_matches"]:
            if "series_info" in match and match["series_info"].get("series_id") == old_series_id:
                match["series_info"]["series_id"] = new_series_id
    
    return data

def update_cache_file(file_path):
    """
    Met à jour un fichier de cache pour utiliser le nouveau format d'ID de série
    
    Args:
        file_path (str): Chemin du fichier à mettre à jour
        
    Returns:
        bool: True si le fichier a été mis à jour, False sinon
    """
    try:
        # Vérifier si le fichier existe
        if not os.path.exists(file_path):
            logger.warning(f"Fichier {file_path} non trouvé, ignoré")
            return False
        
        # Charger les données du fichier
        with open(file_path, 'r') as f:
            cache_data = json.load(f)
        
        # Garder une trace des séries à mettre à jour
        series_to_update = {}
        
        # Identifier les séries qui ont besoin d'être mises à jour
        for series_id in list(cache_data.keys()):
            if is_generated_series_id(series_id):
                # Générer le nouvel ID
                new_series_id = f"s_{series_id}"
                series_to_update[series_id] = new_series_id
                logger.info(f"Série {series_id} à mettre à jour vers {new_series_id} dans {file_path}")
        
        # Mettre à jour les IDs de série
        for old_series_id, new_series_id in series_to_update.items():
            # Récupérer les données de la série
            series_data = cache_data[old_series_id]
            
            # Supprimer l'ancienne entrée
            del cache_data[old_series_id]
            
            # Mettre à jour les données de la série
            series_data = update_series_in_data(series_data, old_series_id, new_series_id)
            
            # Ajouter la nouvelle entrée
            cache_data[new_series_id] = series_data
        
        # Sauvegarder le fichier mis à jour si des modifications ont été effectuées
        if series_to_update:
            with open(file_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"Fichier {file_path} mis à jour ({len(series_to_update)} séries modifiées)")
            return True
        else:
            logger.info(f"Aucune série à mettre à jour dans {file_path}")
            return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du fichier {file_path}: {e}")
        return False

def update_mapping_file():
    """
    Met à jour le fichier de mapping series_matches_mapping.json
    
    Returns:
        bool: True si le fichier a été mis à jour, False sinon
    """
    try:
        # Vérifier si le fichier existe
        if not os.path.exists(SERIES_MAPPING_FILE):
            logger.warning(f"Fichier {SERIES_MAPPING_FILE} non trouvé, ignoré")
            return False
        
        # Charger les données du fichier
        with open(SERIES_MAPPING_FILE, 'r') as f:
            mapping_data = json.load(f)
        
        # Garder une trace des séries à mettre à jour
        series_to_update = {}
        
        # Identifier les séries qui ont besoin d'être mises à jour
        for series_id in list(mapping_data.keys()):
            if is_generated_series_id(series_id):
                # Générer le nouvel ID
                new_series_id = f"s_{series_id}"
                series_to_update[series_id] = new_series_id
                logger.info(f"Mapping pour série {series_id} à mettre à jour vers {new_series_id}")
        
        # Mettre à jour les IDs de série
        for old_series_id, new_series_id in series_to_update.items():
            # Récupérer les matches de la série
            matches = mapping_data[old_series_id]
            
            # Supprimer l'ancienne entrée
            del mapping_data[old_series_id]
            
            # Ajouter la nouvelle entrée
            mapping_data[new_series_id] = matches
        
        # Sauvegarder le fichier mis à jour si des modifications ont été effectuées
        if series_to_update:
            with open(SERIES_MAPPING_FILE, 'w') as f:
                json.dump(mapping_data, f, indent=2)
            logger.info(f"Fichier {SERIES_MAPPING_FILE} mis à jour ({len(series_to_update)} séries modifiées)")
            return True
        else:
            logger.info(f"Aucune série à mettre à jour dans {SERIES_MAPPING_FILE}")
            return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du fichier {SERIES_MAPPING_FILE}: {e}")
        return False

def main():
    """Fonction principale du script"""
    logger.info("Démarrage de la mise à jour des fichiers de cache")
    
    # Mettre à jour le cache principal
    logger.info("=== Mise à jour du cache principal (series_cache.json) ===")
    update_cache_file(SERIES_CACHE_FILE)
    
    # Mettre à jour le cache des séries en direct
    logger.info("=== Mise à jour du cache des séries en direct (live_series_cache.json) ===")
    update_cache_file(LIVE_SERIES_CACHE_FILE)
    
    # Mettre à jour le cache des séries terminées
    logger.info("=== Mise à jour du cache des séries terminées (completed_series_cache.json) ===")
    update_cache_file(COMPLETED_SERIES_CACHE_FILE)
    
    # Mettre à jour le mapping des séries
    logger.info("=== Mise à jour du mapping des séries (series_matches_mapping.json) ===")
    update_mapping_file()
    
    logger.info("Mise à jour des fichiers de cache terminée")

if __name__ == "__main__":
    main()
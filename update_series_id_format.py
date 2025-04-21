#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour mettre à jour le format des IDs de séries dans tous les fichiers de cache.
Tous les IDs de séries doivent commencer par "s_" pour être cohérents.
"""

import os
import json
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
CACHE_DIRECTORY = "cache"
SERIES_CACHE_FILE = os.path.join(CACHE_DIRECTORY, "series_cache.json")
LIVE_SERIES_CACHE_FILE = os.path.join(CACHE_DIRECTORY, "live_series_cache.json")
SERIES_MAPPING_FILE = os.path.join(CACHE_DIRECTORY, "series_matches_mapping.json")

def load_json_file(file_path):
    """Charge un fichier JSON et retourne son contenu"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du fichier {file_path}: {e}")
        return {}

def save_json_file(file_path, data):
    """Sauvegarde des données au format JSON dans un fichier"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        logger.info(f"Fichier {file_path} sauvegardé avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du fichier {file_path}: {e}")
        return False

def update_series_ids(cache_data):
    """
    Met à jour tous les IDs de séries pour s'assurer qu'ils commencent par "s_"
    
    Args:
        cache_data (dict): Données du cache à mettre à jour
        
    Returns:
        tuple: (données mises à jour, dict de correspondance des anciens/nouveaux IDs)
    """
    updated_data = {}
    id_mapping = {}  # Pour suivre les changements d'ID
    
    for series_id, series_data in cache_data.items():
        # Si l'ID ne commence pas par "s_", le mettre à jour
        if not series_id.startswith("s_"):
            new_series_id = f"s_{series_id}"
            logger.info(f"Mise à jour de l'ID de série: {series_id} -> {new_series_id}")
            id_mapping[series_id] = new_series_id
            
            # Mettre à jour l'ID dans les données de la série
            if "series_id" in series_data:
                series_data["series_id"] = new_series_id
                
            updated_data[new_series_id] = series_data
        else:
            # Déjà au bon format
            updated_data[series_id] = series_data
    
    return updated_data, id_mapping

def update_related_ids(cache_data, id_mapping):
    """
    Met à jour les références aux IDs de séries dans les données
    
    Args:
        cache_data (dict): Données du cache à mettre à jour
        id_mapping (dict): Correspondance entre anciens et nouveaux IDs
        
    Returns:
        dict: Données mises à jour
    """
    # Parcourir toutes les séries et mettre à jour les références
    for series_id, series_data in cache_data.items():
        # Mettre à jour les références dans les matchs
        if "matches" in series_data:
            # Si matches est une liste
            if isinstance(series_data["matches"], list):
                for match in series_data["matches"]:
                    if "series_info" in match and "series_id" in match["series_info"]:
                        old_id = match["series_info"]["series_id"]
                        if old_id in id_mapping:
                            match["series_info"]["series_id"] = id_mapping[old_id]
            # Si matches est un dictionnaire
            elif isinstance(series_data["matches"], dict):
                for match_id, match in series_data["matches"].items():
                    if "series_info" in match and "series_id" in match["series_info"]:
                        old_id = match["series_info"]["series_id"]
                        if old_id in id_mapping:
                            match["series_info"]["series_id"] = id_mapping[old_id]
    
    return cache_data

def update_series_mapping(mapping_data, id_mapping):
    """
    Met à jour le fichier de mapping des séries/matchs
    
    Args:
        mapping_data (dict): Données de mapping à mettre à jour
        id_mapping (dict): Correspondance entre anciens et nouveaux IDs
        
    Returns:
        dict: Données de mapping mises à jour
    """
    updated_mapping = {}
    
    # Mettre à jour les clés du mapping
    for series_id, match_ids in mapping_data.items():
        if series_id in id_mapping:
            new_series_id = id_mapping[series_id]
            updated_mapping[new_series_id] = match_ids
        else:
            updated_mapping[series_id] = match_ids
    
    return updated_mapping

def main():
    """Fonction principale"""
    logger.info("=== DÉBUT DE LA MISE À JOUR DES IDS DE SÉRIES ===")
    
    # Charger tous les fichiers de cache
    series_cache = load_json_file(SERIES_CACHE_FILE)
    live_series_cache = load_json_file(LIVE_SERIES_CACHE_FILE)
    series_mapping = load_json_file(SERIES_MAPPING_FILE)
    
    # Vérifier et mettre à jour les fichiers de cache
    if series_cache:
        logger.info(f"Mise à jour du fichier {SERIES_CACHE_FILE}")
        updated_series_cache, id_mapping_series = update_series_ids(series_cache)
        
        # Mettre à jour les références
        updated_series_cache = update_related_ids(updated_series_cache, id_mapping_series)
        
        # Sauvegarder le fichier mis à jour
        save_json_file(SERIES_CACHE_FILE, updated_series_cache)
    
    if live_series_cache:
        logger.info(f"Mise à jour du fichier {LIVE_SERIES_CACHE_FILE}")
        updated_live_cache, id_mapping_live = update_series_ids(live_series_cache)
        
        # Mettre à jour les références
        updated_live_cache = update_related_ids(updated_live_cache, id_mapping_live)
        
        # Sauvegarder le fichier mis à jour
        save_json_file(LIVE_SERIES_CACHE_FILE, updated_live_cache)
    
    # Combiner les mappings d'ID
    all_id_mappings = {}
    if 'id_mapping_series' in locals():
        all_id_mappings.update(id_mapping_series)
    if 'id_mapping_live' in locals():
        all_id_mappings.update(id_mapping_live)
    
    if series_mapping and all_id_mappings:
        logger.info(f"Mise à jour du fichier {SERIES_MAPPING_FILE}")
        updated_mapping = update_series_mapping(series_mapping, all_id_mappings)
        
        # Sauvegarder le fichier mis à jour
        save_json_file(SERIES_MAPPING_FILE, updated_mapping)
    
    logger.info("=== FIN DE LA MISE À JOUR DES IDS DE SÉRIES ===")
    logger.info("Redémarrez le serveur pour appliquer les modifications.")

if __name__ == "__main__":
    main()
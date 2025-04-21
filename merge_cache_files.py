#!/usr/bin/env python3
"""
Script pour fusionner les données de live_data.json vers live_series_cache.json 
et empêcher l'utilisation du fichier live_data.json à l'avenir
"""

import json
import logging
import os
import shutil
from typing import Dict, Any

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
CACHE_DIR = "./cache"
LIVE_SERIES_CACHE = os.path.join(CACHE_DIR, "live_series_cache.json")
LIVE_DATA_CACHE = os.path.join(CACHE_DIR, "live_data.json")
LIVE_DATA_BACKUP = os.path.join(CACHE_DIR, "live_data.json.bak")

def load_cache(file_path: str) -> Dict[str, Any]:
    """Charge un fichier de cache JSON"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Erreur lors du chargement du cache {file_path}: {e}")
        return {}

def save_cache(file_path: str, cache_data: Dict[str, Any]) -> bool:
    """Sauvegarde un fichier de cache JSON"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Cache sauvegardé: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache {file_path}: {e}")
        return False

def merge_cache_files():
    """
    Fusionne les données de live_data.json vers live_series_cache.json
    et crée un fichier vide pour live_data.json
    """
    # 1. Charger les fichiers de cache
    series_cache = load_cache(LIVE_SERIES_CACHE)
    live_data = load_cache(LIVE_DATA_CACHE)
    
    # 2. Faire une sauvegarde du fichier live_data.json au cas où
    if os.path.exists(LIVE_DATA_CACHE):
        shutil.copy2(LIVE_DATA_CACHE, LIVE_DATA_BACKUP)
        logger.info(f"Backup créé: {LIVE_DATA_BACKUP}")
    
    # 3. Transférer les données de matches de live_data.json vers live_series_cache.json
    if "matches" in live_data:
        for match_id, match_data in live_data["matches"].items():
            # Si le match n'est pas dans le cache des séries individuelles, l'ajouter
            if match_id not in series_cache:
                series_cache[match_id] = match_data
                logger.info(f"Match {match_id} transféré de live_data vers live_series_cache")
            
            # S'assurer que le match est associé à sa série
            series_id = match_data.get("series_id")
            if series_id and "series" in series_cache and series_id in series_cache["series"]:
                if "match_ids" in series_cache["series"][series_id]:
                    if match_id not in series_cache["series"][series_id]["match_ids"]:
                        series_cache["series"][series_id]["match_ids"].append(match_id)
                        logger.info(f"Match {match_id} ajouté à la liste match_ids de la série {series_id}")
                else:
                    series_cache["series"][series_id]["match_ids"] = [match_id]
                    logger.info(f"Liste match_ids créée pour la série {series_id} avec le match {match_id}")
    
    # 4. Sauvegarder les changements dans le fichier live_series_cache.json
    if save_cache(LIVE_SERIES_CACHE, series_cache):
        logger.info("Cache live_series_cache.json mis à jour avec succès")
    else:
        logger.error("Échec de la mise à jour du cache live_series_cache.json")
    
    # 5. Créer un fichier live_data.json vide pour désactiver son utilisation
    empty_cache = {
        "message": "Ce fichier est désactivé. Toutes les données sont maintenant dans live_series_cache.json.",
        "last_updated": "2025-04-19",
        "matches": {},
        "series": {},
        "disabled": True
    }
    
    if save_cache(LIVE_DATA_CACHE, empty_cache):
        logger.info("Fichier live_data.json vidé et désactivé")
    else:
        logger.error("Échec de la désactivation du fichier live_data.json")
    
    # 6. Créer un fichier .htaccess pour rediriger les requêtes
    htaccess_path = os.path.join(CACHE_DIR, ".htaccess")
    try:
        with open(htaccess_path, "w") as f:
            f.write("# Redirection des requêtes de live_data.json vers live_series_cache.json\n")
            f.write("Redirect /cache/live_data.json /cache/live_series_cache.json\n")
        logger.info("Fichier .htaccess créé pour la redirection")
    except Exception as e:
        logger.error(f"Échec de la création du fichier .htaccess: {e}")
    
    return True

def patch_dual_cache_system():
    """
    Crée un fichier de patch pour désactiver l'utilisation de live_data.json
    dans le système de cache
    """
    patch_content = """
# Patch pour rediriger les lectures/écritures de live_data.json vers live_series_cache.json

def redirect_cache_operations():
    """
    Cette fonction modifie le comportement du système de cache pour
    rediriger toutes les opérations de live_data.json vers live_series_cache.json
    """
    import dual_cache_system as dcs
    
    # Sauvegarder les fonctions originales
    original_add_match_to_live_cache = dcs.add_match_to_live_cache
    original_get_match_from_live_cache = dcs.get_match_from_live_cache
    
    def new_add_match_to_live_cache(match_data):
        """
        Version patchée qui redirige vers le cache des séries
        """
        match_id = match_data.get("match_id")
        series_cache = dcs.load_live_series_cache()
        
        # Ajouter le match au cache des séries
        series_cache[match_id] = match_data
        
        # S'assurer que le match est associé à sa série
        series_id = match_data.get("series_id")
        if series_id and "series" in series_cache and series_id in series_cache["series"]:
            if "match_ids" in series_cache["series"][series_id]:
                if match_id not in series_cache["series"][series_id]["match_ids"]:
                    series_cache["series"][series_id]["match_ids"].append(match_id)
            else:
                series_cache["series"][series_id]["match_ids"] = [match_id]
        
        # Sauvegarder le cache mis à jour
        dcs.save_live_series_cache(series_cache)
        return True
    
    def new_get_match_from_live_cache(match_id):
        """
        Version patchée qui récupère depuis le cache des séries
        """
        series_cache = dcs.load_live_series_cache()
        return series_cache.get(match_id)
    
    # Remplacer les fonctions
    dcs.add_match_to_live_cache = new_add_match_to_live_cache
    dcs.get_match_from_live_cache = new_get_match_from_live_cache
    
    print("Système de cache patché avec succès!")

# Exécuter le patch au démarrage
redirect_cache_operations()
"""
    
    patch_path = os.path.join(".", "cache_redirect_patch.py")
    try:
        with open(patch_path, "w") as f:
            f.write(patch_content)
        logger.info(f"Fichier de patch créé: {patch_path}")
        
        # Instructions pour modifier dual_cache_system.py
        logger.info("\nModification à faire dans dual_cache_system.py:")
        logger.info("Ajouter au début du fichier: import cache_redirect_patch")
    except Exception as e:
        logger.error(f"Échec de la création du fichier de patch: {e}")
    
    return True

if __name__ == "__main__":
    print("Fusion des fichiers de cache en cours...")
    if merge_cache_files():
        print("Fusion des fichiers de cache terminée avec succès!")
    else:
        print("Erreur lors de la fusion des fichiers de cache.")
    
    print("\nCréation du patch pour le système de cache...")
    if patch_dual_cache_system():
        print("Patch créé avec succès!")
        print("\nÉtape suivante: Modifier dual_cache_system.py pour inclure le patch")
        print("Ajouter cette ligne au début du fichier:")
        print("import cache_redirect_patch")
    else:
        print("Erreur lors de la création du patch.")
"""
Script pour mettre à jour spécifiquement l'ID de la série 8258012658 vers s_8258012658
"""

import json
import os
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paramètres du script
CURRENT_MATCH_ID = "8258012658"
NEW_SERIES_ID = f"s_{CURRENT_MATCH_ID}"

# Chemins des fichiers de cache
LIVE_SERIES_CACHE_FILE = 'cache/live_series_cache.json'
SERIES_CACHE_FILE = 'cache/series_cache.json'
SERIES_MAPPING_FILE = 'cache/series_matches_mapping.json'

def update_active_series():
    """
    Met à jour spécifiquement la série active 8258012658 vers s_8258012658
    dans les différents fichiers de cache
    """
    success = False
    
    # Mise à jour du cache live_series_cache.json
    success_live = update_live_series_cache()
    
    # Mise à jour du cache series_cache.json
    success_series = update_main_series_cache()
    
    # Mise à jour du mapping series_id → match_ids
    success_mapping = update_series_mapping()
    
    return success_live or success_series or success_mapping

def update_live_series_cache():
    """
    Met à jour le cache live_series_cache.json
    """
    try:
        # Charger le cache des séries en direct
        if os.path.exists(LIVE_SERIES_CACHE_FILE):
            with open(LIVE_SERIES_CACHE_FILE, 'r') as f:
                live_series = json.load(f)
        else:
            logger.error(f"Fichier {LIVE_SERIES_CACHE_FILE} non trouvé")
            return False
        
        # Vérifier si la série est présente
        if CURRENT_MATCH_ID in live_series:
            # Récupérer les données de la série
            series_data = live_series[CURRENT_MATCH_ID]
            logger.info(f"Série active trouvée dans live_series_cache: {CURRENT_MATCH_ID}")
            
            # Supprimer l'ancienne entrée
            del live_series[CURRENT_MATCH_ID]
            
            # Mettre à jour l'ID de série
            series_data["series_id"] = NEW_SERIES_ID
            
            # Ajouter l'entrée avec le nouvel ID
            live_series[NEW_SERIES_ID] = series_data
            logger.info(f"Série renommée dans live_series_cache: {CURRENT_MATCH_ID} → {NEW_SERIES_ID}")
            
            # Pour chaque match dans la série, mettre à jour l'ID de série
            for match in series_data.get("matches", []):
                if "series_info" not in match:
                    match["series_info"] = {}
                match["series_info"]["series_id"] = NEW_SERIES_ID
            
            # Sauvegarder le cache mis à jour
            with open(LIVE_SERIES_CACHE_FILE, 'w') as f:
                json.dump(live_series, f, indent=2)
            logger.info(f"Cache des séries en direct mis à jour avec succès")
            
            return True
        else:
            logger.warning(f"Série active {CURRENT_MATCH_ID} non trouvée dans le cache live_series_cache")
            return False
            
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du cache live_series_cache: {e}")
        return False

def update_main_series_cache():
    """
    Met à jour le cache series_cache.json
    """
    try:
        # Charger le cache des séries principal
        if os.path.exists(SERIES_CACHE_FILE):
            with open(SERIES_CACHE_FILE, 'r') as f:
                series_cache = json.load(f)
        else:
            logger.error(f"Fichier {SERIES_CACHE_FILE} non trouvé")
            return False
        
        # Vérifier si la série est présente
        if CURRENT_MATCH_ID in series_cache:
            # Récupérer les données de la série
            series_data = series_cache[CURRENT_MATCH_ID]
            logger.info(f"Série active trouvée dans series_cache: {CURRENT_MATCH_ID}")
            
            # Supprimer l'ancienne entrée
            del series_cache[CURRENT_MATCH_ID]
            
            # Mettre à jour l'ID de série
            series_data["series_id"] = NEW_SERIES_ID
            
            # Ajouter l'entrée avec le nouvel ID
            series_cache[NEW_SERIES_ID] = series_data
            logger.info(f"Série renommée dans series_cache: {CURRENT_MATCH_ID} → {NEW_SERIES_ID}")
            
            # Sauvegarder le cache mis à jour
            with open(SERIES_CACHE_FILE, 'w') as f:
                json.dump(series_cache, f, indent=2)
            logger.info(f"Cache series_cache.json mis à jour avec succès")
            
            return True
        else:
            logger.warning(f"Série active {CURRENT_MATCH_ID} non trouvée dans le cache series_cache")
            return False
            
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du cache series_cache: {e}")
        return False

def update_series_mapping():
    """
    Met à jour le mapping des séries pour la série active
    """
    try:
        # Charger le mapping des séries
        if os.path.exists(SERIES_MAPPING_FILE):
            with open(SERIES_MAPPING_FILE, 'r') as f:
                mapping = json.load(f)
        else:
            logger.warning(f"Fichier {SERIES_MAPPING_FILE} non trouvé, création d'un nouveau fichier")
            mapping = {}
        
        # Vérifier si la série existe dans le mapping
        if CURRENT_MATCH_ID in mapping:
            # Récupérer les matchs de la série
            matches = mapping[CURRENT_MATCH_ID]
            logger.info(f"Mapping trouvé pour la série {CURRENT_MATCH_ID} avec {len(matches)} matchs")
            
            # Supprimer l'ancienne entrée
            del mapping[CURRENT_MATCH_ID]
            
            # Ajouter la nouvelle entrée
            mapping[NEW_SERIES_ID] = matches
            logger.info(f"Mapping mis à jour: {CURRENT_MATCH_ID} → {NEW_SERIES_ID}")
            
            # Sauvegarder le mapping mis à jour
            with open(SERIES_MAPPING_FILE, 'w') as f:
                json.dump(mapping, f, indent=2)
            logger.info(f"Mapping des séries mis à jour avec succès")
            return True
        else:
            # Si la série n'existe pas encore, la créer avec le match actuel
            mapping[NEW_SERIES_ID] = [CURRENT_MATCH_ID]
            logger.info(f"Nouveau mapping créé pour {NEW_SERIES_ID} avec match {CURRENT_MATCH_ID}")
            
            # Sauvegarder le mapping mis à jour
            with open(SERIES_MAPPING_FILE, 'w') as f:
                json.dump(mapping, f, indent=2)
            logger.info(f"Nouveau mapping créé avec succès")
            return True
            
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du mapping: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info(f"Mise à jour de la série active {CURRENT_MATCH_ID} → {NEW_SERIES_ID}")
    update_active_series()
    logger.info("Mise à jour terminée")

if __name__ == "__main__":
    main()
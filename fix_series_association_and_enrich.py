"""
Script pour unifier l'ID de série des matchs 8260717084 et 8260778197
"""

import os
import json
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes
LIVE_CACHE_FILE = "cache/live_series_cache.json"
SERIES_ID = "s_8260778197"
MATCH_IDS = ["8260717084", "8260778197"]

def load_cache():
    """Charge le cache live"""
    try:
        with open(LIVE_CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erreur lors du chargement du cache: {str(e)}")
        return None

def save_cache(cache_data):
    """Sauvegarde le cache modifié"""
    try:
        with open(LIVE_CACHE_FILE, "w") as f:
            json.dump(cache_data, f, indent=2)
        logger.info(f"Cache sauvegardé: {LIVE_CACHE_FILE}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache: {str(e)}")
        return False

def fix_series_association():
    """
    Unifie l'ID de série pour les matchs 8260717084 et 8260778197
    en utilisant s_8260778197 comme ID de série commun
    """
    logger.info(f"Association des matchs {', '.join(MATCH_IDS)} à la série {SERIES_ID}")
    
    # Charger le cache
    cache_data = load_cache()
    if not cache_data:
        return False
    
    # Vérifier si les matchs existent
    for match_id in MATCH_IDS:
        if match_id not in cache_data["matches"]:
            logger.error(f"Match {match_id} non trouvé dans le cache")
            return False
    
    # Vérifier si la série existe
    if SERIES_ID not in cache_data["series"]:
        logger.error(f"Série {SERIES_ID} non trouvée dans le cache")
        return False
    
    # Mettre à jour l'ID de série dans chaque match
    for match_id in MATCH_IDS:
        cache_data["matches"][match_id]["series_id"] = SERIES_ID
        logger.info(f"Match {match_id}: ID de série mis à jour à {SERIES_ID}")
    
    # S'assurer que tous les matchs sont dans la liste des matchs de la série
    if "match_ids" not in cache_data["series"][SERIES_ID]:
        cache_data["series"][SERIES_ID]["match_ids"] = []
    
    # Ajouter les matchs à la série s'ils n'y sont pas déjà
    for match_id in MATCH_IDS:
        if match_id not in cache_data["series"][SERIES_ID]["match_ids"]:
            cache_data["series"][SERIES_ID]["match_ids"].append(match_id)
            logger.info(f"Match {match_id} ajouté à la liste des matchs de la série {SERIES_ID}")
    
    # Mettre à jour le type de série (Best of 3)
    cache_data["series"][SERIES_ID]["series_type"] = 1
    
    # Pour forcer l'enrichissement, marquer les matchs comme terminés
    for match_id in MATCH_IDS:
        cache_data["matches"][match_id]["status"] = "finished"
        cache_data["matches"][match_id]["status_tag"] = "FINISHED"
        logger.info(f"Match {match_id}: Statut mis à jour à 'finished' pour forcer l'enrichissement")
    
    # Sauvegarder le cache
    return save_cache(cache_data)

def main():
    """Fonction principale"""
    logger.info("Démarrage du script de correction de l'association de série")
    
    # Corriger l'association des séries
    if fix_series_association():
        logger.info("Association des séries corrigée avec succès")
    else:
        logger.error("Échec de la correction de l'association des séries")
        return
    
    logger.info("Script terminé - L'enrichissement sera déclenché automatiquement au prochain rafraîchissement")

if __name__ == "__main__":
    main()
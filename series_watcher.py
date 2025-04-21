#!/usr/bin/env python3
"""
Script de surveillance pour maintenir la cohérence des séries.
Ce script vérifie en permanence si l'API Steam a créé une nouvelle série temporaire
et la supprime en déplaçant les matchs vers la série correcte.
"""

import json
import logging
import os
import time
from typing import Dict, Any, List

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chemins des fichiers de cache
LIVE_SERIES_CACHE_PATH = 'cache/live_series_cache.json'
SERIES_MAPPING_PATH = 'cache/series_matches_mapping.json'

def load_cache(file_path: str) -> Dict[str, Any]:
    """
    Charge un fichier de cache JSON
    
    Args:
        file_path (str): Chemin du fichier à charger
        
    Returns:
        dict: Données du cache
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Erreur lors du chargement du cache {file_path}: {e}")
        if isinstance(e, FileNotFoundError):
            return {}
        # Pour JSONDecodeError, essayer de sauvegarder le fichier corrompu et créer un nouveau
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            try:
                os.rename(file_path, backup_path)
                logger.info(f"Cache corrompu sauvegardé sous {backup_path}")
            except Exception as backup_err:
                logger.error(f"Impossible de sauvegarder le cache corrompu: {backup_err}")
        return {}

def save_cache(file_path: str, cache_data: Dict[str, Any]) -> bool:
    """
    Sauvegarde un fichier de cache JSON
    
    Args:
        file_path (str): Chemin du fichier à sauvegarder
        cache_data (dict): Données à sauvegarder
        
    Returns:
        bool: True si succès, False sinon
    """
    try:
        # Créer le dossier parent si nécessaire
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(cache_data, file, indent=2, ensure_ascii=False)
        
        logger.info(f"Cache sauvegardé: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache {file_path}: {e}")
        return False

def check_and_fix_series():
    """
    Vérifie si la série s_8261452684 existe et la corrige en déplaçant les matchs vers s_8261361161
    
    Returns:
        bool: True si une correction a été effectuée, False sinon
    """
    # Constantes
    MATCH_ID = "8261452684"  # Match à associer (Game 3)
    CORRECT_SERIES_ID = "s_8261361161"  # ID de la série correcte
    WRONG_SERIES_ID = "s_8261452684"  # ID de la série temporaire
    
    # Charger les caches
    series_cache = load_cache(LIVE_SERIES_CACHE_PATH)
    series_mapping = load_cache(SERIES_MAPPING_PATH)
    
    # Vérifier si la série temporaire existe
    if 'series' in series_cache and WRONG_SERIES_ID in series_cache['series']:
        logger.info(f"Série temporaire {WRONG_SERIES_ID} détectée, correction en cours...")
        
        # 1. Mettre à jour le mapping series_matches_mapping.json
        if CORRECT_SERIES_ID in series_mapping and MATCH_ID not in series_mapping[CORRECT_SERIES_ID]:
            series_mapping[CORRECT_SERIES_ID].append(MATCH_ID)
            logger.info(f"Match {MATCH_ID} ajouté à la série {CORRECT_SERIES_ID} dans le mapping")
        
        # Supprimer la série temporaire s_8261452684 du mapping si elle existe
        if WRONG_SERIES_ID in series_mapping:
            del series_mapping[WRONG_SERIES_ID]
            logger.info(f"Série {WRONG_SERIES_ID} supprimée du mapping")
        
        # 2. Mettre à jour le cache live_series_cache.json
        if CORRECT_SERIES_ID in series_cache['series']:
            # Ajouter le match à la série correcte s'il n'y est pas déjà
            if MATCH_ID not in series_cache['series'][CORRECT_SERIES_ID].get('match_ids', []):
                if 'match_ids' not in series_cache['series'][CORRECT_SERIES_ID]:
                    series_cache['series'][CORRECT_SERIES_ID]['match_ids'] = []
                series_cache['series'][CORRECT_SERIES_ID]['match_ids'].append(MATCH_ID)
                logger.info(f"Match {MATCH_ID} ajouté aux match_ids de la série {CORRECT_SERIES_ID}")
            
            # Mettre à jour les scores de la série correcte avec ceux de la série temporaire
            scores_updated = False
            if 'radiant_score' in series_cache['series'][WRONG_SERIES_ID]:
                series_cache['series'][CORRECT_SERIES_ID]['radiant_score'] = series_cache['series'][WRONG_SERIES_ID]['radiant_score']
                scores_updated = True
            if 'dire_score' in series_cache['series'][WRONG_SERIES_ID]:
                series_cache['series'][CORRECT_SERIES_ID]['dire_score'] = series_cache['series'][WRONG_SERIES_ID]['dire_score']
                scores_updated = True
            
            if scores_updated:
                logger.info(f"Scores de la série {CORRECT_SERIES_ID} mis à jour: radiant={series_cache['series'][CORRECT_SERIES_ID].get('radiant_score')}, dire={series_cache['series'][CORRECT_SERIES_ID].get('dire_score')}")
            
            # Supprimer la série temporaire
            del series_cache['series'][WRONG_SERIES_ID]
            logger.info(f"Série {WRONG_SERIES_ID} supprimée du cache live")
        else:
            logger.error(f"Série correcte {CORRECT_SERIES_ID} non trouvée dans le cache, impossible de corriger")
            return False
        
        # 3. Sauvegarder les caches mis à jour
        save_success = True
        if not save_cache(LIVE_SERIES_CACHE_PATH, series_cache):
            logger.error("Erreur lors de la mise à jour du cache live_series_cache.json")
            save_success = False
        
        if not save_cache(SERIES_MAPPING_PATH, series_mapping):
            logger.error("Erreur lors de la mise à jour du cache series_matches_mapping.json")
            save_success = False
        
        if save_success:
            logger.info("Correction effectuée avec succès")
        
        return True
    else:
        logger.info(f"Série temporaire {WRONG_SERIES_ID} non détectée, aucune correction nécessaire")
        return False

def main():
    """
    Fonction principale qui surveille et corrige en permanence les séries
    """
    logger.info("Démarrage du script de surveillance des séries...")
    
    # Définir l'intervalle de vérification (en secondes)
    check_interval = 5
    
    try:
        while True:
            # Vérifier et corriger les séries
            check_and_fix_series()
            
            # Attendre avant la prochaine vérification
            logger.info(f"Attente de {check_interval} secondes avant la prochaine vérification...")
            time.sleep(check_interval)
    except KeyboardInterrupt:
        logger.info("Arrêt du script de surveillance des séries")
    except Exception as e:
        logger.error(f"Erreur non gérée: {e}")

if __name__ == "__main__":
    main()
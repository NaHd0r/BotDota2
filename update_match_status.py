#!/usr/bin/env python3
"""
Script pour mettre à jour le statut des matchs précédents d'une série.

Ce script identifie les matchs précédents d'une série et les marque comme
terminés (status="finished") pour qu'ils n'apparaissent pas comme des matchs en cours
dans l'interface.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

# Configuration du logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes
CACHE_DIR = "cache"
LIVE_DATA_FILE = os.path.join(CACHE_DIR, "live_data.json")

# Séries à mettre à jour
SERIES_ID = "s_8259450653"
MATCH_IDS = ["8259450653", "8259522321", "8259581999"]

def load_cache(file_path: str) -> Dict[str, Any]:
    """Charge le cache JSON depuis un fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        logger.error(f"Erreur lors du chargement du cache {file_path}: {e}")
        return {}

def save_cache(file_path: str, data: Dict[str, Any]) -> bool:
    """Sauvegarde le cache JSON dans un fichier"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Cache sauvegardé dans {file_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache {file_path}: {e}")
        return False

def update_match_status():
    """
    Met à jour le statut des matchs précédents d'une série pour les marquer
    comme terminés (status="finished").
    """
    # Charger le cache live
    cache_data = load_cache(LIVE_DATA_FILE)
    if not cache_data:
        logger.error("Le cache est vide")
        return False
    
    # Vérifier si les matchs existent
    if "matches" not in cache_data:
        logger.error("Section 'matches' non trouvée dans le cache")
        return False
    
    # Pour chaque match de la série (sauf le dernier qui est en cours)
    for match_id in MATCH_IDS[:-1]:  # Exclure le dernier match (en cours)
        if match_id not in cache_data["matches"]:
            logger.warning(f"Match {match_id} non trouvé dans le cache")
            continue
        
        # Récupérer les données du match
        match_data = cache_data["matches"][match_id]
        
        # Ajouter le champ status="finished"
        match_data["status"] = "finished"
        match_data["status_tag"] = "TERMINÉ"
        
        # Sauvegarder les modifications
        cache_data["matches"][match_id] = match_data
        
        logger.info(f"Match {match_id} marqué comme terminé")
    
    # Pour le dernier match (en cours)
    if MATCH_IDS[-1] in cache_data["matches"]:
        match_data = cache_data["matches"][MATCH_IDS[-1]]
        if "status" not in match_data:
            match_data["status"] = "in_progress"
            match_data["status_tag"] = "EN COURS"
            cache_data["matches"][MATCH_IDS[-1]] = match_data
            logger.info(f"Match {MATCH_IDS[-1]} marqué comme en cours")
    
    # Sauvegarder le cache
    return save_cache(LIVE_DATA_FILE, cache_data)

def main():
    """Fonction principale"""
    print("===== Mise à jour du statut des matchs d'une série =====")
    print(f"Série: {SERIES_ID}")
    print(f"Matchs à marquer comme terminés: {', '.join(MATCH_IDS[:-1])}")
    print(f"Match en cours: {MATCH_IDS[-1]}")
    
    if update_match_status():
        print("Mise à jour terminée avec succès!")
    else:
        print("Échec de la mise à jour!")
    
    print("\nVérifiez l'API /matches pour voir les matchs avec leurs statuts corrects.")

if __name__ == "__main__":
    main()
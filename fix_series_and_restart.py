#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script principal pour appliquer toutes les corrections de format aux IDs de série,
puis redémarrer le serveur pour prendre en compte les modifications.

Ce script:
1. Exécute update_series_id_format.py pour corriger le format des IDs
2. Exécute fix_match_references.py pour corriger les références dans les matchs
3. Redémarre le serveur pour prendre en compte les modifications
"""

import os
import sys
import subprocess
import logging
import time

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_script(script_name):
    """Exécute un script Python et affiche sa sortie"""
    logger.info(f"Exécution du script: {script_name}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Afficher la sortie standard
        for line in result.stdout.splitlines():
            logger.info(f"[{script_name}] {line}")
        
        # Afficher les erreurs s'il y en a
        if result.stderr:
            for line in result.stderr.splitlines():
                logger.warning(f"[{script_name}] {line}")
        
        logger.info(f"Script {script_name} terminé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de l'exécution de {script_name}")
        logger.error(f"Code de sortie: {e.returncode}")
        logger.error(f"Sortie standard: {e.stdout}")
        logger.error(f"Erreur: {e.stderr}")
        return False

def main():
    """Fonction principale d'exécution du script"""
    logger.info("=== DÉBUT DE LA CORRECTION DES IDS DE SÉRIE ===")
    start_time = time.time()
    
    # 1. Exécuter le script de mise à jour des IDs
    if not run_script("update_series_id_format.py"):
        logger.error("Erreur lors de la mise à jour des IDs de série. Arrêt.")
        return
    
    # 2. Exécuter le script de correction des références
    if not run_script("fix_match_references.py"):
        logger.error("Erreur lors de la correction des références. Arrêt.")
        return
    
    # 3. Afficher un résumé
    logger.info("=== RÉSUMÉ DES OPÉRATIONS ===")
    logger.info("1. Format des IDs de série mis à jour")
    logger.info("2. Références aux matchs corrigées")
    logger.info(f"Durée totale des opérations: {time.time() - start_time:.2f}s")
    logger.info("=== FIN DE LA CORRECTION DES IDS DE SÉRIE ===")
    logger.info("Veuillez redémarrer manuellement le serveur pour prendre en compte les modifications")

if __name__ == "__main__":
    main()
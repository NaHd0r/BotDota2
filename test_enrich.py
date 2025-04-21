#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour tester l'enrichissement d'un match terminé
"""

import sys
import logging
from enrich_live_match import enrich_live_match

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        match_id = sys.argv[1]
    else:
        # Utiliser un ID de match récent qui est terminé
        match_id = "8258012658"  # Remplacer par le match récemment terminé
    
    logger.info(f"Tentative d'enrichissement du match {match_id}...")
    
    # Appeler la fonction d'enrichissement
    success = enrich_live_match(match_id)
    
    if success:
        logger.info(f"✅ Match {match_id} enrichi avec succès")
    else:
        logger.error(f"❌ Échec de l'enrichissement du match {match_id}")
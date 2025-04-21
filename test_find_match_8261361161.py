#!/usr/bin/env python3
"""
Script de test pour retrouver spécifiquement le match 8261361161
comme match précédent de la série s_8261407829, avec un filtre temporel strict.
"""

import logging
import sys
from find_previous_matches import find_previous_matches_for_series, update_series_with_previous_matches, update_series_mapping

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Fonction principale du script de test"""
    series_id = "s_8261407829"
    
    # Utiliser un filtre temporel plus strict (1 jour)
    max_days_back = 1
    
    logger.info(f"Recherche du match précédent pour la série {series_id} dans les dernières {max_days_back} jour(s)")
    
    # Rechercher les matchs précédents
    previous_matches = find_previous_matches_for_series(series_id, max_days_back)
    
    if previous_matches:
        # Afficher les matchs trouvés
        for match in previous_matches:
            match_id = match.get('match_id')
            match_time = match.get('start_time', 'unknown')
            logger.info(f"Match trouvé: {match_id} (timestamp: {match_time})")
            
        # Mode automatique pour l'environnement script
        logger.info("Mise à jour automatique de la série...")
        
        # Mettre à jour la série
        update_series_with_previous_matches(series_id, previous_matches)
        
        # Mettre à jour le mapping des séries
        match_ids = [match['match_id'] for match in previous_matches]
        update_series_mapping(series_id, match_ids)
        
        logger.info("Série mise à jour avec succès")
    else:
        logger.warning("Aucun match précédent trouvé pour cette série")
    
    logger.info("Script terminé")

if __name__ == "__main__":
    main()
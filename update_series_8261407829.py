#!/usr/bin/env python3
"""
Script pour associer automatiquement le match 8261361161 à la série s_8261407829
"""

import logging
from find_previous_matches import (
    find_previous_matches_for_series,
    update_series_with_previous_matches,
    update_series_mapping
)

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Fonction principale du script"""
    series_id = "s_8261407829"
    target_match_id = "8261361161"
    
    logger.info(f"Recherche de matchs pour la série {series_id}")
    
    # Limiter aux matchs récents (1 jour maximum)
    previous_matches = find_previous_matches_for_series(series_id, max_days_back=1)
    
    if not previous_matches:
        logger.error("Aucun match précédent trouvé")
        return
    
    # Filtrer le match spécifique que nous cherchons
    matched_matches = [m for m in previous_matches if m.get('match_id') == target_match_id]
    
    if not matched_matches:
        logger.error(f"Match {target_match_id} non trouvé dans les résultats")
        return
    
    match = matched_matches[0]
    
    logger.info(f"Match trouvé: {match.get('match_id')} (game {match.get('game_number', 1)})")
    logger.info("Association du match à la série...")
    
    # Mettre à jour la série
    update_series_with_previous_matches(series_id, [match])
    
    # Mettre à jour le mapping des séries
    update_series_mapping(series_id, [target_match_id])
    
    logger.info("Série mise à jour avec succès")

if __name__ == "__main__":
    main()
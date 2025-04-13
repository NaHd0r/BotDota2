import logging
import sys
from scraper import get_1xbet_match_url, scrape_1xbet_kill_threshold
from dota_service import get_live_matches

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_specific_match():
    """Teste le scraping pour le match Freedom Fighters vs Prime Legion"""
    radiant_name = "Freedom Fighters Team"
    dire_name = "Prime Legion"
    
    logger.info(f"Recherche du match: {radiant_name} vs {dire_name}")
    
    # Étape 1: Vérifier si le match existe sur 1xBet
    match_url = get_1xbet_match_url(radiant_name, dire_name)
    if match_url:
        logger.info(f"🎯 URL du match trouvée: {match_url}")
        
        # Étape 2: Récupérer le seuil de kills
        kill_threshold = scrape_1xbet_kill_threshold(match_url)
        if kill_threshold:
            logger.info(f"🎯 Seuil de kills trouvé: {kill_threshold}")
        else:
            logger.error("❌ Impossible de récupérer le seuil de kills")
    else:
        logger.error("❌ URL du match non trouvée sur 1xBet")
    
    # Afficher les matchs actuellement en direct via l'API Steam
    logger.info("\nRécupération des matchs en direct via l'API Steam:")
    live_matches = get_live_matches()
    if live_matches:
        logger.info(f"Nombre de matchs en direct: {len(live_matches)}")
        for match in live_matches:
            logger.info(f"Match trouvé: {match['radiant_name']} vs {match['dire_name']}")
    else:
        logger.error("Aucun match en direct trouvé via l'API Steam")

if __name__ == "__main__":
    logger.info("=== Test du scraper pour 1xBet ===")
    test_specific_match()
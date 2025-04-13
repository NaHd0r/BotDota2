import asyncio
import logging
from telegram_bot import format_match_for_telegram
from dota_service import get_live_matches, format_duration

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def simulate_matches_command():
    """Simule la commande /matches du bot Telegram"""
    logger.info("Recherche des matchs en direct en cours...")
    
    # Récupération des matchs en direct
    matches = get_live_matches()
    
    if not matches:
        logger.info("Aucun match en direct trouvé.")
        return
    
    logger.info(f"{len(matches)} match(s) en direct trouvé(s):")
    
    # Simule l'envoi des informations pour chaque match
    for match in matches:
        formatted_message = format_match_for_telegram(match)
        logger.info("Message formaté pour Telegram:")
        logger.info(formatted_message)
        logger.info("-" * 50)

async def main():
    """Fonction principale"""
    logger.info("=== Test des commandes du bot Telegram ===")
    
    # Teste la commande /matches
    await simulate_matches_command()

if __name__ == "__main__":
    asyncio.run(main())
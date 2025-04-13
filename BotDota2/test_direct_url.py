import logging
import sys
from scraper import get_random_headers, scrape_1xbet_kill_threshold
import requests
from bs4 import BeautifulSoup

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_direct_url():
    """Teste directement l'URL fournie pour le match Freedom Fighters vs Prime Legion"""
    direct_url = "https://1xsinga.com/en/live/esports/2431462-dota-2-mad-dogs-league/612677162-freedom-fighters-prime-legion"
    
    logger.info(f"Test direct de l'URL: {direct_url}")
    
    # Récupérer le seuil de kills directement depuis l'URL fournie
    kill_threshold = scrape_1xbet_kill_threshold(direct_url)
    
    if kill_threshold:
        logger.info(f"🎯 Seuil de kills trouvé: {kill_threshold}")
    else:
        logger.error("❌ Impossible de récupérer le seuil de kills")
        
        # Test supplémentaire en cas d'échec - inspection de la page
        try:
            headers = get_random_headers()
            logger.info("Tentative de récupération directe de la page...")
            response = requests.get(direct_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                logger.info("✅ Page récupérée avec succès, recherche manuelle des informations de kills")
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Recherche de texte contenant "kill"
                kill_elements = []
                for element in soup.find_all(text=lambda text: text and "kill" in text.lower()):
                    logger.info(f"Élément contenant 'kill': {element.strip()}")
                    kill_elements.append(element.strip())
                
                # Recherche d'éléments avec des scores ou des nombres
                logger.info("Éléments avec des chiffres qui pourraient contenir des seuils de kills:")
                import re
                for element in soup.find_all(text=lambda text: text and re.search(r'\d+\.\d+|\d+', text)):
                    if "kill" in element.lower() or "total" in element.lower():
                        logger.info(f"Potentiel seuil: {element.strip()}")
                
            else:
                logger.error(f"❌ Échec de la récupération de la page: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'analyse manuelle: {e}")

if __name__ == "__main__":
    logger.info("=== Test direct de l'URL du match 1xBet ===")
    test_direct_url()
import logging
import requests
import random
import time
from bs4 import BeautifulSoup
from scraper import get_random_headers

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Liste de proxy gratuits (à jour au moment de la création du script)
# Note: les proxys gratuits peuvent ne pas être fiables
FREE_PROXIES = [
    "8.219.176.202:8080",  # Singapore
    "159.89.113.155:8080", # Singapore
    "45.77.22.33:9999",    # Japan
    "38.170.153.227:8080", # Canada
    "222.179.155.90:9091", # China
]

def get_random_proxy():
    """Retourne un proxy aléatoire de la liste"""
    return random.choice(FREE_PROXIES)

def fetch_with_proxy(url):
    """Tente de récupérer une URL en utilisant un proxy"""
    for i in range(3):  # Tente 3 fois avec différents proxys
        proxy = get_random_proxy()
        logger.info(f"Tentative {i+1}/3 avec proxy: {proxy}")
        
        proxy_dict = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }
        
        headers = get_random_headers()
        # Ajouter des en-têtes pour sembler plus comme un navigateur réel
        headers["Referer"] = "https://www.google.com/"
        
        try:
            # Ajouter un délai plus long
            time.sleep(random.uniform(3, 5))
            
            response = requests.get(
                url,
                headers=headers,
                proxies=proxy_dict,
                timeout=20,
                verify=False  # Ignorer les erreurs SSL
            )
            
            if response.status_code == 200:
                logger.info("✅ Succès!")
                return response.text
            else:
                logger.error(f"❌ Échec: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Erreur avec le proxy {proxy}: {e}")
    
    return None

def extract_kill_threshold(html_content):
    """Extrait le seuil de kills du contenu HTML"""
    if not html_content:
        return None
    
    soup = BeautifulSoup(html_content, 'html.parser')
    all_text = soup.get_text().lower()
    
    # Chercher des patterns de kill threshold
    kill_patterns = ["total kills", "kills total", "kill total", "total kill"]
    
    for pattern in kill_patterns:
        if pattern in all_text:
            logger.info(f"Pattern trouvé: '{pattern}'")
            index = all_text.find(pattern)
            # Chercher un nombre dans les 60 caractères autour du pattern
            window = all_text[max(0, index-30):min(len(all_text), index+30)]
            logger.info(f"Fenêtre de texte: '{window}'")
            
            # Extraire tous les nombres
            import re
            numbers = re.findall(r'\d+\.\d+|\d+', window)
            for num in numbers:
                value = float(num)
                # Valider si c'est probablement un seuil de kills
                if 20 <= value <= 60:
                    logger.info(f"Seuil de kills probable: {value}")
                    return value
    
    return None

def test_match_url():
    """Teste la récupération des données du match avec proxy"""
    direct_url = "https://1xsinga.com/en/live/esports/2431462-dota-2-mad-dogs-league/612677162-freedom-fighters-prime-legion"
    
    logger.info(f"Test de l'URL avec proxy: {direct_url}")
    
    # Récupérer la page en utilisant un proxy
    html_content = fetch_with_proxy(direct_url)
    
    if html_content:
        # Chercher le seuil de kills
        kill_threshold = extract_kill_threshold(html_content)
        
        if kill_threshold:
            logger.info(f"🎯 Seuil de kills trouvé: {kill_threshold}")
        else:
            logger.error("❌ Seuil de kills non trouvé dans la page")
    else:
        logger.error("❌ Impossible de récupérer la page même avec un proxy")

if __name__ == "__main__":
    # Désactiver les avertissements pour les certificats SSL
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    logger.info("=== Test avec proxy pour 1xBet ===")
    test_match_url()
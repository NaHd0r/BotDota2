import requests
from bs4 import BeautifulSoup
import random
import time
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Différents User-Agents pour éviter la détection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:108.0) Gecko/20100101 Firefox/108.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/108.0.1462.54 Safari/537.36",
]

def get_random_headers():
    """Génère des en-têtes aléatoires pour les requêtes HTTP"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

def test_series_url(series_id):
    """Test direct de l'URL d'une série Dotabuff"""
    # Construire l'URL
    url = f"https://www.dotabuff.com/esports/series/{series_id}"
    
    logger.info(f"Tentative d'accès à l'URL: {url}")
    
    # Ajouter un délai aléatoire pour éviter la détection
    time.sleep(random.uniform(1.0, 2.0))
    
    # Récupérer la page
    headers = get_random_headers()
    response = requests.get(url, headers=headers, timeout=15)
    
    # Vérifier le statut de la réponse
    logger.info(f"Statut de la réponse: {response.status_code}")
    if response.status_code != 200:
        logger.error(f"Erreur d'accès à l'URL: {response.status_code}")
        return
    
    # Analyser la page HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Récupérer le titre de la page
    title = soup.find('title')
    logger.info(f"Titre de la page: {title.text if title else 'Non trouvé'}")
    
    # Vérifier si la page contient un message d'erreur
    error_element = soup.find('div', class_='empty-message')
    if error_element:
        logger.error(f"Message d'erreur trouvé: {error_element.text.strip()}")
    
    # Vérifier si la page contient un en-tête
    header = soup.find('header', class_='header-content')
    if header:
        logger.info("En-tête trouvé.")
        
        # Extraire les noms d'équipes
        team_elements = header.find_all('div', class_='team')
        logger.info(f"Nombre d'éléments d'équipe trouvés: {len(team_elements)}")
        
        for i, team in enumerate(team_elements):
            team_name = team.find('span', class_='name')
            logger.info(f"Équipe {i+1}: {team_name.text.strip() if team_name else 'Non trouvé'}")
    else:
        logger.warning("En-tête non trouvé.")
        # Essayer de trouver un autre format d'en-tête
        alt_header = soup.find('div', class_='header')
        if alt_header:
            logger.info("En-tête alternatif trouvé.")
            print(alt_header)
    
    # Vérifier si la page contient une section de jeux
    games_section = soup.find('section', class_='tabs-tab-content', id='game-menu-tab-games')
    if games_section:
        logger.info("Section de jeux trouvée.")
        
        # Chercher les éléments de jeu
        game_items = games_section.find_all('a', class_='game-item')
        logger.info(f"Nombre d'éléments de jeu trouvés: {len(game_items)}")
        
        for i, game in enumerate(game_items):
            match_id = game['href'].split('/')[-1]
            logger.info(f"Match {i+1}: ID {match_id}")
            
            # Extraire le numéro du jeu
            game_number = game.find('span', class_='game-no')
            if game_number:
                logger.info(f"Match {i+1}: Numéro {game_number.text.strip()}")
    else:
        logger.warning("Section de jeux non trouvée.")
        # Examiner les sections disponibles
        sections = soup.find_all('section')
        logger.info(f"Nombre de sections trouvées: {len(sections)}")
        for i, section in enumerate(sections):
            logger.info(f"Section {i+1}: Classes: {section.get('class', 'Aucune')}, ID: {section.get('id', 'Aucun')}")
    
    # Vérifier si la page contient des liens vers des matchs
    match_links = soup.find_all('a', href=lambda href: href and '/matches/' in href)
    logger.info(f"Nombre de liens de match trouvés: {len(match_links)}")
    for i, link in enumerate(match_links[:5]):  # Afficher seulement les 5 premiers
        match_id = link['href'].split('/')[-1]
        logger.info(f"Match trouvé {i+1}: ID {match_id}")

# URL à tester
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # Utiliser l'ID de série fourni
        series_id = sys.argv[1]
    else:
        # Utiliser un ID de série par défaut
        series_id = "2664712"
    
    test_series_url(series_id)
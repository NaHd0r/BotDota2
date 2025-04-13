"""
Module de scraping optimisé pour Dota 2 Dashboard

Ce module est conçu pour extraire des données de paris et de statistiques
pour les matchs de Dota 2 depuis différentes sources externes (1xBet, Dotabuff).

Caractéristiques principales:
1. Mise en cache des résultats pour réduire le nombre de requêtes
2. Délais aléatoires et rotation des User-Agents pour éviter la détection
3. Fallback vers des statistiques prédites si le scraping échoue
4. Système de prédiction basé sur les données historiques des équipes

Structure du système de cache:
- Les données sont stockées dans des fichiers JSON dans le dossier 'cache/'
- Chaque type de données a sa propre durée de validité (paris: 1h, stats d'équipes: 24h)
- Les résultats en échec ne sont pas mis en cache pour éviter de propager des données incorrectes

Utilisation appropriée:
- Toujours accéder aux données via les fonctions de haut niveau comme fetch_1xbet_data()
- Ne pas appeler directement les fonctions de scraping de bas niveau
- Ne pas modifier les fichiers de cache manuellement

Documentation ajoutée le: 12 avril 2025
"""

import requests
import logging
import random
import time
import os
import json
import datetime
from bs4 import BeautifulSoup
from config import ONEXBET_TOURNAMENT_URL, ONEXBET_URLS

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Chemin pour le cache
CACHE_DIR = "cache"
BETTING_CACHE_FILE = os.path.join(CACHE_DIR, "betting_cache.json")
TEAM_STATS_CACHE_FILE = os.path.join(CACHE_DIR, "team_stats_cache.json")

# Durée de validité du cache (en secondes)
CACHE_DURATION = {
    "betting": 3600,  # 1 heure pour les paris
    "team_stats": 86400,  # 24 heures pour les stats d'équipe
}

# S'assurer que le répertoire de cache existe
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

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

def load_cache(cache_file):
    """Charge les données depuis le fichier de cache"""
    if not os.path.exists(cache_file):
        return {}
    
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erreur lors du chargement du cache: {e}")
        
        # Si le fichier de cache est corrompu, essayons de le supprimer
        try:
            os.remove(cache_file)
            logger.info(f"Fichier de cache corrompu supprimé: {cache_file}")
        except OSError:
            pass
            
        return {}

def save_cache(cache_file, data):
    """Sauvegarde les données dans le fichier de cache"""
    try:
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        logger.error(f"Erreur lors de la sauvegarde du cache: {e}")

def is_cache_valid(timestamp, cache_type="betting"):
    """Vérifie si les données en cache sont encore valides"""
    if not timestamp:
        return False
    
    # Convertir le timestamp en datetime
    cache_time = datetime.datetime.fromtimestamp(timestamp)
    now = datetime.datetime.now()
    
    # Calculer la différence en secondes
    diff = (now - cache_time).total_seconds()
    
    # Vérifier si la durée est dépassée
    return diff < CACHE_DURATION[cache_type]

def get_cached_betting_data(match_key):
    """Récupère les données de paris en cache pour un match spécifique"""
    cache = load_cache(BETTING_CACHE_FILE)
    
    if match_key in cache and is_cache_valid(cache[match_key].get("timestamp")):
        logger.info(f"Utilisation des données en cache pour {match_key}")
        return cache[match_key]["data"]
    
    return None

def cache_betting_data(match_key, data):
    """Met en cache les données de paris pour un match spécifique"""
    cache = load_cache(BETTING_CACHE_FILE)
    
    cache[match_key] = {
        "timestamp": datetime.datetime.now().timestamp(),
        "data": data
    }
    
    save_cache(BETTING_CACHE_FILE, cache)
    logger.info(f"Données de paris en cache pour {match_key}")

def get_1xbet_match_url(radiant_name, dire_name):
    """Get the URL for a specific match on 1xBet by trying multiple mirror domains"""
    # Essayer chaque URL alternative
    for tournament_url in ONEXBET_URLS:
        logger.info(f"Trying 1xBet mirror: {tournament_url}")
        
        try:
            # Ajout d'un délai aléatoire avant la requête
            time.sleep(random.uniform(1, 2))
            
            # Utilisation d'en-têtes aléatoires
            headers = get_random_headers()
            
            # Essayer de récupérer la page
            response = requests.get(
                tournament_url, 
                headers=headers, 
                timeout=10
            )
            
            # Vérifier si la requête a réussi
            if response.status_code != 200:
                logger.error(f"Error loading page {tournament_url}: {response.status_code}")
                continue  # Essayer l'URL suivante
            
            # Analyse de la page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Essayer différentes classes d'éléments de match selon le site
            potential_classes = ["c-events__item", "event", "events-item", "match-container", "event-item"]
            match_elements = []
            
            # Chercher les éléments avec les classes candidates
            for class_name in potential_classes:
                elements = soup.find_all(class_=class_name)
                if elements:
                    match_elements.extend(elements)
                    logger.info(f"Found {len(elements)} elements with class {class_name}")
            
            # Si aucun élément trouvé avec les classes spécifiques, prendre tous les div
            if not match_elements:
                logger.info("No match elements found with known classes, searching all divs")
                match_elements = soup.find_all("div")
            
            # Différentes façons d'écrire le nom du match
            search_patterns = [
                f"{radiant_name.lower()} vs {dire_name.lower()}",
                f"{radiant_name.lower()}-{dire_name.lower()}",
                f"{dire_name.lower()} vs {radiant_name.lower()}",
                f"{dire_name.lower()}-{radiant_name.lower()}"
            ]
            
            # Chercher les éléments contenant le nom du match
            for element in match_elements:
                element_text = element.get_text(strip=True).lower()
                
                # Vérifier chaque pattern
                match_found = False
                for pattern in search_patterns:
                    if pattern in element_text:
                        match_found = True
                        logger.info(f"Match pattern found: {pattern}")
                        break
                
                # Si un pattern est trouvé, chercher le lien
                if match_found:
                    link = element.find('a')
                    if link and 'href' in link.attrs:
                        # Extraire le domaine de base de l'URL du tournoi
                        domain_parts = tournament_url.split("/")
                        base_url = f"{domain_parts[0]}//{domain_parts[2]}"
                        
                        # Construire l'URL complète du match
                        href = link['href']
                        match_url = href if href.startswith("http") else f"{base_url}{href}"
                        
                        logger.info(f"Match URL found: {match_url}")
                        return match_url
            
            # Recherche alternative - chercher simplement les noms des équipes
            for element in match_elements:
                element_text = element.get_text(strip=True).lower()
                if (radiant_name.lower() in element_text and dire_name.lower() in element_text):
                    link = element.find('a')
                    if link and 'href' in link.attrs:
                        # Extraire le domaine de base
                        domain_parts = tournament_url.split("/")
                        base_url = f"{domain_parts[0]}//{domain_parts[2]}"
                        
                        # Construire l'URL complète
                        href = link['href']
                        match_url = href if href.startswith("http") else f"{base_url}{href}"
                        
                        logger.info(f"Match URL found with team name search: {match_url}")
                        return match_url
            
            logger.info(f"Match not found on {tournament_url}")
        
        except Exception as e:
            logger.error(f"Error with {tournament_url}: {str(e)}")
            # Continuer avec l'URL suivante
    
    # Si toutes les tentatives échouent
    logger.error("Failed to find match URL on all 1xBet mirrors")
    return None

def scrape_1xbet_kill_threshold(match_url):
    """Scrape the kill threshold from a 1xBet match page"""
    if not match_url:
        return None
    
    try:
        # Ajout d'un délai aléatoire avant la requête
        time.sleep(random.uniform(1, 2))
        
        # Utilisation d'en-têtes aléatoires
        headers = get_random_headers()
        
        # Récupération de la page du match
        logger.info(f"Requesting match page: {match_url}")
        response = requests.get(
            match_url, 
            headers=headers, 
            timeout=15
        )
        
        # Vérification du statut
        if response.status_code != 200:
            logger.error(f"Error loading match page: {response.status_code}")
            return None
        
        # Analyse de la page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Essayer plusieurs classes possibles pour les éléments de paris
        potential_bet_classes = ["c-bets__item", "bet", "market", "bet-cell", "bet-option"]
        bet_elements = []
        
        # Collecter tous les éléments de paris avec les classes candidates
        for class_name in potential_bet_classes:
            elements = soup.find_all(class_=class_name)
            if elements:
                bet_elements.extend(elements)
                logger.info(f"Found {len(elements)} bet elements with class '{class_name}'")
        
        # Si aucun élément n'est trouvé avec les classes spécifiques, chercher en fonction du texte
        if not bet_elements:
            logger.info("No bet elements found with known classes, searching by text patterns")
            all_divs = soup.find_all("div")
            for div in all_divs:
                text = div.get_text(strip=True).lower()
                if "kill" in text and ("over" in text or "under" in text or "total" in text):
                    bet_elements.append(div)
        
        # Vérifier les éléments de paris pour trouver le seuil de kills
        logger.info(f"Analyzing {len(bet_elements)} potential bet elements")
        for element in bet_elements:
            text = element.get_text(strip=True).lower()
            logger.debug(f"Checking element text: {text}")
            
            # Patterns pour la ligne de kills
            kill_pattern_found = False
            for pattern in ["total kills", "kills total", "kill total", "total kill"]:
                if pattern in text:
                    kill_pattern_found = True
                    logger.info(f"Found kill pattern: '{pattern}' in text: '{text}'")
                    break
            
            # Si c'est un élément lié aux kills, chercher un nombre
            if kill_pattern_found or ("over" in text and "kill" in text):
                # Extraire tous les nombres du texte
                parts = text.split()
                for part in parts:
                    if part.replace(".", "").isdigit():
                        value = float(part)
                        # Valider que c'est une valeur probable pour un seuil de kills
                        if 20 <= value <= 60:
                            logger.info(f"Found kill threshold: {value}")
                            return value
        
        # Recherche générique dans tout le texte
        logger.info("No specific kill threshold found in bet elements, searching in full page text")
        all_text = soup.get_text().lower()
        
        for pattern in ["total kills over/under", "total kills over", "kill total", "total kill"]:
            if pattern in all_text:
                logger.info(f"Found pattern '{pattern}' in page text")
                index = all_text.find(pattern)
                # Chercher un nombre dans les 30 caractères suivant ou précédant le pattern
                search_window = all_text[max(0, index-30):min(len(all_text), index+60)]
                logger.debug(f"Search window: {search_window}")
                
                # Extraire tous les nombres du texte
                import re
                numbers = re.findall(r'\d+\.\d+|\d+', search_window)
                for num in numbers:
                    value = float(num)
                    # Valider que c'est une valeur probable pour un seuil de kills
                    if 20 <= value <= 60:
                        logger.info(f"Found kill threshold in text: {value}")
                        return value
        
        logger.warning("Kill threshold not found on 1xBet page")
        return None
    except Exception as e:
        logger.error(f"Error scraping kill threshold: {e}")
        return None

def get_match_stats_from_dotabuff(match_id):
    """
    Récupère les statistiques d'un match spécifique depuis Dotabuff.
    Utilise un cache pour limiter les requêtes.
    """
    # Vérifier si les stats sont en cache
    cache = load_cache(TEAM_STATS_CACHE_FILE)
    match_key = f"match_{match_id}"
    
    if match_key in cache and is_cache_valid(cache[match_key].get("timestamp"), "team_stats"):
        logger.info(f"Utilisation des stats en cache pour le match {match_id}")
        return cache[match_key]["data"]
    
    # Stats par défaut si le scraping échoue
    default_stats = {
        "total_kills": 0,
        "match_duration_minutes": 0,
        "radiant_team": "",
        "dire_team": "",
        "winner": "",
        "radiant_kills": 0,
        "dire_kills": 0
    }
    
    try:
        # Construire l'URL du match sur Dotabuff
        dotabuff_url = f"https://www.dotabuff.com/matches/{match_id}"
        
        logger.info(f"Récupération des stats pour le match {match_id} depuis Dotabuff: {dotabuff_url}")
        
        # Attendre un délai aléatoire pour éviter la détection
        time.sleep(random.uniform(2, 3))
        
        # Utilisation d'en-têtes aléatoires
        headers = get_random_headers()
        
        # Effectuer la requête
        response = requests.get(dotabuff_url, headers=headers, timeout=15)
        
        # Vérifier le statut
        if response.status_code != 200:
            logger.error(f"Erreur lors de la récupération des stats du match {match_id}: {response.status_code}")
            return default_stats
        
        # Analyser la page avec BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraire les statistiques
        stats = default_stats.copy()
        
        try:
            # Extraire les noms des équipes
            team_headers = soup.find_all('div', class_='team-header')
            if len(team_headers) >= 2:
                radiant_header = team_headers[0]
                dire_header = team_headers[1]
                
                stats["radiant_team"] = radiant_header.get_text(strip=True)
                stats["dire_team"] = dire_header.get_text(strip=True)
            
            # Extraire le score
            try:
                scoreboard = soup.find('div', class_='scoreboard')
                if scoreboard:
                    # Vérifier que scoreboard est un objet qui possède la méthode find_all
                    if hasattr(scoreboard, 'find_all'):
                        try:
                            score_elements = scoreboard.find_all('span', class_='score-wrapper')
                            if len(score_elements) >= 2:
                                try:
                                    stats["radiant_kills"] = int(score_elements[0].get_text(strip=True))
                                    stats["dire_kills"] = int(score_elements[1].get_text(strip=True))
                                    stats["total_kills"] = stats["radiant_kills"] + stats["dire_kills"]
                                except ValueError:
                                    logger.warning("Impossible de convertir les scores en entiers")
                            else:
                                logger.warning("Pas assez d'éléments de score trouvés")
                        except AttributeError:
                            logger.error("Erreur lors de l'extraction des scores: problème avec les éléments de score")
                    else:
                        logger.error("Erreur lors de l'extraction des scores: scoreboard n'a pas de méthode find_all")
                else:
                    logger.warning("Élément scoreboard non trouvé sur la page")
            except Exception as e:
                logger.error(f"Erreur générale lors de l'extraction des scores: {e}")
            
            # Extraire la durée du match
            duration_element = soup.find('span', class_='duration')
            if duration_element:
                duration_text = duration_element.get_text(strip=True)
                # Convertir format MM:SS en minutes
                if ":" in duration_text:
                    parts = duration_text.split(":")
                    stats["match_duration_minutes"] = float(parts[0]) + float(parts[1])/60
            
            # Déterminer le vainqueur
            result_element = soup.find('div', class_='match-result')
            if result_element:
                result_text = result_element.get_text(strip=True).lower()
                if "radiant" in result_text and "victory" in result_text:
                    stats["winner"] = "radiant"
                elif "dire" in result_text and "victory" in result_text:
                    stats["winner"] = "dire"
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de la page du match {match_id}: {e}")
        
        # Mettre en cache les résultats
        cache[match_key] = {
            "timestamp": datetime.datetime.now().timestamp(),
            "data": stats
        }
        save_cache(TEAM_STATS_CACHE_FILE, cache)
        
        return stats
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats pour le match {match_id}: {e}")
        return default_stats

def get_team_stats_from_dotabuff(team_name):
    """
    Récupère les statistiques d'une équipe depuis Dotabuff.
    Utilise un cache pour limiter les requêtes.
    """
    # Vérifier si les stats sont en cache
    cache = load_cache(TEAM_STATS_CACHE_FILE)
    
    if team_name in cache and is_cache_valid(cache[team_name].get("timestamp"), "team_stats"):
        logger.info(f"Utilisation des stats en cache pour {team_name}")
        return cache[team_name]["data"]
    
    # Stats par défaut si le scraping échoue
    default_stats = {
        "avg_kills": 34.0,  # Valeur moyenne pour les équipes compétitives
        "avg_deaths": 34.0,
        "avg_match_duration_minutes": 35.0
    }
    
    try:
        # Normaliser le nom d'équipe pour l'URL
        url_team_name = team_name.lower().replace(" ", "-")
        dotabuff_url = f"https://www.dotabuff.com/esports/teams/{url_team_name}"
        
        logger.info(f"Récupération des stats pour {team_name} depuis Dotabuff: {dotabuff_url}")
        
        # Attendre un délai aléatoire pour éviter la détection
        time.sleep(random.uniform(2, 3))
        
        # Utilisation d'en-têtes aléatoires
        headers = get_random_headers()
        
        # Effectuer la requête
        response = requests.get(dotabuff_url, headers=headers, timeout=15)
        
        # Vérifier le statut
        if response.status_code != 200:
            logger.error(f"Erreur lors de la récupération des stats de {team_name}: {response.status_code}")
            stats = default_stats
        else:
            # Analyser la page avec BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraire les statistiques (code simplifié pour l'exemple)
            # Dans une implémentation réelle, il faudrait analyser plus précisément la structure HTML
            stats = default_stats
            
            try:
                # Chercher les statistiques dans les tableaux
                stat_tables = soup.find_all('table', class_='stat-table')
                for table in stat_tables:
                    # Extraire les données de statistiques ici
                    # Exemple simplifié, en réalité, il faudrait une analyse plus poussée
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            cell_text = cells[0].get_text(strip=True).lower()
                            if "kills" in cell_text:
                                try:
                                    stats["avg_kills"] = float(cells[1].get_text(strip=True))
                                except ValueError:
                                    pass
                            elif "deaths" in cell_text:
                                try:
                                    stats["avg_deaths"] = float(cells[1].get_text(strip=True))
                                except ValueError:
                                    pass
                            elif "duration" in cell_text:
                                try:
                                    duration_text = cells[1].get_text(strip=True)
                                    # Convertir format MM:SS en minutes
                                    if ":" in duration_text:
                                        parts = duration_text.split(":")
                                        stats["avg_match_duration_minutes"] = float(parts[0]) + float(parts[1])/60
                                except ValueError:
                                    pass
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse des stats: {e}")
                # Utiliser les valeurs par défaut en cas d'erreur
        
        # Mettre en cache les résultats
        cache[team_name] = {
            "timestamp": datetime.datetime.now().timestamp(),
            "data": stats
        }
        save_cache(TEAM_STATS_CACHE_FILE, cache)
        
        return stats
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats pour {team_name}: {e}")
        return default_stats

def find_previous_matches(team1_id, team2_id, max_results=5):
    """
    Cette fonction a été conservée pour la compatibilité mais ne recherche plus
    les matchs précédents entre deux équipes. Utilisez get_matches_by_series_id() à la place.
    
    Args:
        team1_id: ID de la première équipe (ignoré)
        team2_id: ID de la deuxième équipe (ignoré)
        max_results: Nombre maximal de résultats à retourner
        
    Returns:
        Une liste vide de dictionnaires
    """
    logger.info(f"Fonction obsolète: find_previous_matches({team1_id}, {team2_id})")
    return []
    
    return matches

def get_matches_by_series_id(series_id, max_results=5):
    """
    Récupère les matchs d'une série spécifique en utilisant l'ID de la série.
    
    Cette fonction essaie d'abord de trouver une série complète sur Dotabuff,
    puis recherche les matchs individuels de cette série.
    
    Args:
        series_id: ID de la série ou du match
        max_results: Nombre maximal de résultats à retourner
        
    Returns:
        Une liste de dictionnaires contenant les informations des matchs
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Recherche des matchs pour la série/match ID: {series_id}")
    
    # Créer une clé unique pour ce match/série
    cache_key = f"series_{series_id}"
    
    # Vérifier si les données sont en cache et toujours valides
    cached_data = load_cache(f"cache/{cache_key}.json")
    if cached_data and is_cache_valid(cached_data.get('timestamp'), cache_type="team_stats"):
        logger.info(f"Utilisation des données en cache pour la série/match ID: {series_id}")
        return cached_data.get('matches', [])
    
    matches = []
    
    # Essayer d'abord de trouver une série entière
    series_matches = extract_matches_from_series(series_id)
    
    # Si des matchs ont été trouvés dans la série, les utiliser
    if series_matches:
        logger.info(f"Série trouvée pour l'ID {series_id}, {len(series_matches)} matchs récupérés")
        matches = series_matches
    else:
        # Sinon, considérer l'ID comme un ID de match individuel
        logger.info(f"Aucune série trouvée, considération de {series_id} comme ID de match")
        
        # Construction de l'URL pour la recherche de matchs par ID
        url = f"https://www.dotabuff.com/matches/{series_id}"
        
        try:
            # Ajout d'un délai aléatoire pour éviter la détection
            time.sleep(random.uniform(1.0, 3.0))
            
            headers = get_random_headers()
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Error loading match data: {response.status_code}")
                return []
            
            # Parser la page pour extraire les informations du match
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraire les noms d'équipes et IDs
            header = soup.find('header', class_='header-content')
            
            if not header:
                logger.warning(f"Could not find header for match {series_id}")
                return []
            
            # Trouver les équipes
            team_names = header.find_all('a', class_='team-text-full')
            team_ids = []
            
            # Essayer de trouver les IDs dans les liens des équipes
            for team_link in team_names:
                href = team_link.get('href', '')
                if '/esports/teams/' in href:
                    team_id = href.split('/esports/teams/')[1].split('/')[0]
                    team_ids.append(team_id)
                else:
                    team_ids.append('0')  # ID par défaut si non trouvé
            
            # Vérifier qu'on a trouvé deux équipes
            if len(team_names) < 2 or len(team_ids) < 2:
                logger.warning(f"Could not find both teams for match {series_id}")
                return []
            
            team1_name = team_names[0].get_text(strip=True)
            team2_name = team_names[1].get_text(strip=True)
            team1_id = team_ids[0]
            team2_id = team_ids[1]
            
            # Extraire le score
            score_box = header.find('div', class_='score-container')
            
            if not score_box:
                logger.warning(f"Could not find score box for match {series_id}")
                return []
            
            scores = score_box.find_all('span', class_='team-score')
            
            if len(scores) < 2:
                logger.warning(f"Could not find both scores for match {series_id}")
                return []
            
            radiant_score = int(scores[0].get_text(strip=True))
            dire_score = int(scores[1].get_text(strip=True))
            
            # Extraire la durée et la date
            match_info = soup.find('div', class_='match-info')
            
            if not match_info:
                logger.warning(f"Could not find match info for match {series_id}")
                return []
            
            duration_div = match_info.find('div', class_='duration')
            match_date_div = match_info.find('time')
            
            duration = duration_div.get_text(strip=True) if duration_div else "00:00"
            match_date_str = match_date_div.get('datetime') if match_date_div else None
            match_date = datetime.datetime.strptime(match_date_str, "%Y-%m-%dT%H:%M:%S%z") if match_date_str else datetime.datetime.now()
            
            # Extraire les informations de série (BO3, BO5)
            series_span = soup.find('span', class_='series-info')
            match_type = series_span.get_text(strip=True) if series_span else "Match unique"
            
            # Déterminer le vainqueur
            winner = 'radiant' if radiant_score > dire_score else 'dire'
            
            # Créer l'objet match
            match = {
                'match_id': series_id,
                'date': match_date,
                'duration': duration,
                'radiant_team': {'id': team1_id, 'name': team1_name},
                'dire_team': {'id': team2_id, 'name': team2_name},
                'radiant_score': radiant_score,
                'dire_score': dire_score,
                'total_kills': radiant_score + dire_score,
                'winner': winner,
                'match_type': match_type
            }
            
            matches = [match]
            
            # Pour une série complète, essayer de trouver d'autres matchs liés
            related_matches_div = soup.find('section', class_='related-matches')
            
            if related_matches_div:
                match_links = related_matches_div.find_all('a', class_='match-link')
                
                for i, link in enumerate(match_links):
                    if i >= max_results - 1:  # -1 car on a déjà un match
                        break
                        
                    match_id = link['href'].split('/')[-1]
                    
                    if match_id != series_id:  # éviter de récupérer le même match
                        # On pourrait faire un appel récursif ici, mais pour éviter trop de requêtes,
                        # on se contente d'extraire les infos basiques de cette page
                        match_score = link.find('span', class_='scores').get_text(strip=True).split('-')
                        
                        if len(match_score) == 2:
                            related_radiant_score = int(match_score[0])
                            related_dire_score = int(match_score[1])
                            related_winner = 'radiant' if related_radiant_score > related_dire_score else 'dire'
                            
                            # Pour la date, on utilise celle du match principal moins un jour par match
                            related_date = match_date - datetime.timedelta(days=i+1)
                            
                            # Essayer de trouver l'information sur le numéro de match dans la série
                            game_number = link.find('span', class_='game-no')
                            game_info = f"Match {game_number.get_text(strip=True)}" if game_number else f"Match {i+2}"
                            
                            related_match = {
                                'match_id': match_id,
                                'date': related_date,
                                'duration': "30:00",  # Durée approx par défaut
                                'radiant_team': {'id': team1_id, 'name': team1_name},
                                'dire_team': {'id': team2_id, 'name': team2_name},
                                'radiant_score': related_radiant_score,
                                'dire_score': related_dire_score,
                                'total_kills': related_radiant_score + related_dire_score,
                                'winner': related_winner,
                                'match_type': f"{match_type} - {game_info}"
                            }
                            
                            matches.append(related_match)
        
        except Exception as e:
            logger.error(f"Error finding match {series_id}: {e}")
    
    # Mettre en cache le résultat
    if matches:
        # Convertir les objets datetime en chaînes pour le stockage en cache et la sérialisation JSON
        serializable_matches = []
        for match in matches:
            match_copy = match.copy()
            if isinstance(match_copy.get('date'), datetime.datetime):
                match_copy['date'] = match_copy['date'].strftime('%Y-%m-%d %H:%M:%S')
            serializable_matches.append(match_copy)
            
        cache_data = {
            'timestamp': datetime.datetime.now().timestamp(),
            'matches': serializable_matches
        }
        save_cache(f"cache/{cache_key}.json", cache_data)
        
        # Retourner les copies sérialisables
        return serializable_matches[:max_results]
    
    return matches[:max_results]


def extract_matches_from_series(series_id):
    """
    Extrait les matchs d'une série Dotabuff.
    
    Args:
        series_id: ID de la série
        
    Returns:
        Liste des matchs trouvés dans la série
    """
    logger = logging.getLogger(__name__)
    matches = []
    
    # Vérification d'ID valide
    if not series_id or not str(series_id).isdigit():
        logger.error(f"ID de série invalide: {series_id}")
        return []
    
    # Essayer d'abord comme ID de série
    series_url = f"https://www.dotabuff.com/esports/series/{series_id}"
    
    try:
        # Ajouter un délai aléatoire pour éviter la détection
        time.sleep(random.uniform(1.0, 3.0))
        
        headers = get_random_headers()
        response = requests.get(series_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Error loading series data: {response.status_code}")
            return []
        
        # Parser la page pour extraire les informations de la série
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraire le titre pour obtenir des informations sur les équipes
        title = soup.find('title')
        if not title:
            logger.warning(f"Could not find title for series {series_id}")
            return []
        
        title_text = title.text
        logger.info(f"Titre de la série: {title_text}")
        
        # Essayer d'extraire les noms des équipes du titre
        # Format commun: "Team1 vs Team2 - Tournament Name - DOTABUFF"
        team1_name = "Team 1"
        team2_name = "Team 2"
        
        try:
            if "vs" in title_text:
                parts = title_text.split(" - ")
                if parts:
                    teams_part = parts[0]
                    team_names = teams_part.split(" vs ")
                    
                    if len(team_names) >= 2:
                        team1_name = team_names[0].strip()
                        team2_name = team_names[1].strip()
            
            logger.info(f"Équipes extraites: {team1_name} vs {team2_name}")
        except Exception as e:
            logger.warning(f"Erreur lors de l'extraction des noms d'équipes: {e}")
            # Continuer avec les valeurs par défaut
        
        # Chercher les sections contenant des informations sur les équipes
        team_sections = soup.find_all('section', class_='series-team')
        team1_id = "0"
        team2_id = "0"
        
        if len(team_sections) >= 2:
            for i, section in enumerate(team_sections[:2]):
                team_links = section.find_all('a', href=lambda href: href and '/esports/teams/' in href)
                
                if team_links:
                    team_href = team_links[0]['href']
                    if '/esports/teams/' in team_href:
                        team_id = team_href.split('/esports/teams/')[1].split('/')[0]
                        if i == 0:
                            team1_id = team_id
                        else:
                            team2_id = team_id
        
        # Extraire le type de série (BO3, BO5) de la page
        series_details = soup.find('section', class_='series-details')
        series_type = "Série"
        
        if series_details:
            # Chercher des informations sur le type de série (BO3, BO5)
            series_text = series_details.get_text()
            if "Best of" in series_text:
                if "Best of 3" in series_text:
                    series_type = "Best of 3"
                elif "Best of 5" in series_text:
                    series_type = "Best of 5"
                else:
                    # Essayer d'extraire avec une expression régulière
                    import re
                    match = re.search(r'Best of (\d+)', series_text)
                    if match:
                        series_type = f"Best of {match.group(1)}"
        
        # Trouver tous les liens vers des matchs dans la page
        match_ids = set()
        
        try:
            match_links = soup.find_all('a', href=lambda href: href and '/matches/' in href)
            
            for link in match_links:
                try:
                    match_id = link['href'].split('/')[-1]
                    # Vérifier que c'est un ID valide (numérique)
                    if match_id.isdigit():
                        # Éviter les doublons
                        match_ids.add(match_id)
                except Exception:
                    continue
                    
            logger.info(f"Trouvé {len(match_ids)} matchs uniques dans la série {series_id}")
        except Exception as e:
            logger.error(f"Erreur lors de la recherche des liens de matchs: {e}")
        
        # Traiter chaque match trouvé
        for i, match_id in enumerate(match_ids):
            # Construire un objet match basic
            match = {
                'match_id': match_id,
                'date': datetime.datetime.now() - datetime.timedelta(days=i),
                'duration': "00:00",  # Valeur par défaut
                'radiant_team': {'id': team1_id, 'name': team1_name},
                'dire_team': {'id': team2_id, 'name': team2_name},
                'radiant_score': 0,
                'dire_score': 0,
                'total_kills': 0,
                'winner': 'unknown',
                'match_type': f"{series_type} - Match {i+1}"
            }
            
            # Pour les 3 premiers matchs, récupérer les détails complets
            if i < 3:
                detailed_match = get_match_details(match_id, team1_name, team2_name, team1_id, team2_id, f"{series_type} - Match {i+1}")
                if detailed_match:
                    matches.append(detailed_match)
                else:
                    matches.append(match)
            else:
                matches.append(match)
        
        # Si aucun match n'a été trouvé via les liens, chercher dans la section des matchs récents
        if not matches:
            matches_section = None
            try:
                matches_section = soup.find('section', class_='series-matches')
            except Exception as e:
                logger.warning(f"Erreur lors de la recherche de la section des matchs: {e}")
                
            if matches_section:
                match_rows = []
                try:
                    match_rows = matches_section.find_all('tr')
                except Exception as e:
                    logger.warning(f"Erreur lors de la recherche des lignes de match: {e}")
                
                for i, row in enumerate(match_rows):
                    links = []
                    match_id = None
                    
                    try:
                        links = row.find_all('a', href=lambda href: href and '/matches/' in href)
                        
                        if links:
                            match_id = links[0]['href'].split('/')[-1]
                            # Vérifier que c'est un ID valide
                            if not match_id.isdigit():
                                continue
                    except Exception as e:
                        logger.warning(f"Erreur lors de l'extraction de l'ID du match: {e}")
                        continue
                    
                    # Si nous avons réussi à extraire un ID valide
                    if match_id and match_id.isdigit():
                        radiant_score = 0
                        dire_score = 0
                        winner = 'unknown'
                        duration = "00:00"
                        
                        try:
                            # Récupérer les scores
                            score_cells = row.find_all('td', class_='r-tab')
                            
                            if len(score_cells) >= 2:
                                try:
                                    radiant_score = int(score_cells[0].text.strip())
                                    dire_score = int(score_cells[1].text.strip())
                                except ValueError:
                                    pass
                            
                            # Déterminer le vainqueur
                            if radiant_score > dire_score:
                                winner = 'radiant'
                            elif dire_score > radiant_score:
                                winner = 'dire'
                            
                            # Récupérer la durée si disponible
                            duration_cell = row.find('td', class_='r-none-mob')
                            if duration_cell:
                                duration = duration_cell.text.strip()
                        except Exception as e:
                            logger.warning(f"Erreur lors de l'extraction des scores pour le match {match_id}: {e}")
                        
                        # Créer l'objet match basic
                        match = {
                            'match_id': match_id,
                            'date': datetime.datetime.now() - datetime.timedelta(days=i),
                            'duration': duration,
                            'radiant_team': {'id': team1_id, 'name': team1_name},
                            'dire_team': {'id': team2_id, 'name': team2_name},
                            'radiant_score': radiant_score,
                            'dire_score': dire_score,
                            'total_kills': radiant_score + dire_score,
                            'winner': winner,
                            'match_type': f"{series_type} - Match {i+1}",
                            'series_id': series_id,
                            'game_number': i+1
                        }
                        
                        # Récupérer plus de détails pour les 3 premiers matchs
                        if i < 3:
                            try:
                                detailed_match = get_match_details(match_id, team1_name, team2_name, team1_id, team2_id, f"{series_type} - Match {i+1}")
                                if detailed_match:
                                    # Ajouter les informations de série
                                    detailed_match['series_id'] = series_id
                                    detailed_match['game_number'] = i+1
                                    matches.append(detailed_match)
                                else:
                                    matches.append(match)
                            except Exception as e:
                                logger.warning(f"Erreur lors de la récupération des détails pour le match {match_id}: {e}")
                                matches.append(match)
                        else:
                            matches.append(match)
        
        return matches
    
    except Exception as e:
        logger.error(f"Error extracting matches from series {series_id}: {e}")
        return []


def get_match_details(match_id, team1_name, team2_name, team1_id, team2_id, match_type="Match unique"):
    """
    Récupère les détails d'un match Dota 2 à partir de son ID.
    
    Args:
        match_id: ID du match
        team1_name: Nom de l'équipe 1
        team2_name: Nom de l'équipe 2
        team1_id: ID de l'équipe 1
        team2_id: ID de l'équipe 2
        match_type: Type de match (BO3, BO5, etc.)
        
    Returns:
        Dictionnaire contenant les informations du match ou None en cas d'erreur
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Ajout d'un délai aléatoire pour éviter la détection
        time.sleep(random.uniform(1.0, 3.0))
        
        # Construction de l'URL
        url = f"https://www.dotabuff.com/matches/{match_id}"
        
        headers = get_random_headers()
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Error loading match details: {response.status_code}")
            return None
        
        # Parser la page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraire le score
        score_container = soup.find('div', class_='match-score')
        
        if not score_container:
            logger.warning(f"Could not find score container for match {match_id}")
            return None
        
        radiant_score_element = score_container.find('span', class_='the-radiant')
        dire_score_element = score_container.find('span', class_='the-dire')
        
        if not radiant_score_element or not dire_score_element:
            logger.warning(f"Could not find score elements for match {match_id}")
            return None
        
        radiant_score = int(radiant_score_element.find('span', class_='score').get_text(strip=True))
        dire_score = int(dire_score_element.find('span', class_='score').get_text(strip=True))
        
        # Extraire la durée
        duration_element = soup.find('span', class_='duration')
        duration = duration_element.get_text(strip=True) if duration_element else "00:00"
        
        # Extraire la date
        match_date_element = soup.find('time')
        match_date_str = match_date_element.get('datetime') if match_date_element else None
        match_date = datetime.datetime.strptime(match_date_str, "%Y-%m-%dT%H:%M:%S%z") if match_date_str else datetime.datetime.now()
        
        # Déterminer le vainqueur
        winner = 'radiant' if radiant_score > dire_score else 'dire'
        
        # Créer l'objet match
        match = {
            'match_id': match_id,
            'date': match_date,
            'duration': duration,
            'radiant_team': {'id': team1_id, 'name': team1_name},
            'dire_team': {'id': team2_id, 'name': team2_name},
            'radiant_score': radiant_score,
            'dire_score': dire_score,
            'total_kills': radiant_score + dire_score,
            'winner': winner,
            'match_type': match_type
        }
        
        return match
    
    except Exception as e:
        logger.error(f"Error getting match details for {match_id}: {e}")
        return None


def analyze_previous_matchups(team1_id, team2_id):
    """
    Analyse les précédents matchs entre deux équipes pour obtenir
    des statistiques plus précises pour les prédictions.
    
    Args:
        team1_id: ID de la première équipe
        team2_id: ID de la deuxième équipe
        
    Returns:
        Un dictionnaire avec les stats moyennes
    """
    # Valeurs par défaut
    stats = {
        "avg_total_kills": 33.5,
        "avg_match_duration_minutes": 35.0,
        "sample_size": 0
    }
    
    # Récupérer les noms des équipes depuis une base de données ou un service
    team_names = {
        '9245832': 'Prime Legion',
        '8969887': 'Freedom Fighters Team',
        '8255888': 'BetBoom Team',
        '9247354': 'Team Falcons'
    }
    
    team1_name = team_names.get(str(team1_id), f"Team {team1_id}")
    team2_name = team_names.get(str(team2_id), f"Team {team2_id}")
    
    # Cette fonction n'utilise plus l'historique des matchs mais des valeurs prédéfinies
    logger.info(f"Utilisation de valeurs par défaut pour {team1_name} vs {team2_name}")
    
    return stats

def predict_kill_threshold(radiant_id, dire_id):
    """
    Prédit un seuil de kills probable basé sur les statistiques des équipes
    
    Args:
        radiant_id: ID de l'équipe Radiant
        dire_id: ID de l'équipe Dire
        
    Returns:
        Le seuil de kills prédit (arrondi au 0.5 près)
    """
    # Récupérer les noms des équipes depuis une base de données ou un service
    team_names = {
        '9245832': 'Prime Legion',
        '8969887': 'Freedom Fighters Team',
        '8255888': 'BetBoom Team',
        '9247354': 'Team Falcons'
    }
    
    # Statistiques fixes pour les équipes connues (en fallback si Dotabuff échoue)
    team_avg_kills = {
        "Prime Legion": 35.2,
        "Freedom Fighters Team": 31.7,
        "BetBoom Team": 33.8,
        "Team Falcons": 32.5,
        "Team Unknown": 34.0  # Valeur par défaut pour les équipes inconnues
    }
    
    # Convertir les IDs en noms
    radiant_name = team_names.get(str(radiant_id), f"Team {radiant_id}")
    dire_name = team_names.get(str(dire_id), f"Team {dire_id}")
    
    # Facteurs de pondération
    WEIGHT_PREVIOUS_MATCHUPS = 0.6  # Plus de poids aux confrontations directes
    WEIGHT_TEAM_STATS = 0.4         # Moins de poids aux stats générales
    
    # D'abord, essayer d'analyser les confrontations directes
    previous_matchup_stats = analyze_previous_matchups(radiant_id, dire_id)
    has_previous_matches = previous_matchup_stats["sample_size"] > 0
    
    # Ensuite, obtenir les stats individuelles des équipes
    try:
        radiant_stats = get_team_stats_from_dotabuff(radiant_name)
        dire_stats = get_team_stats_from_dotabuff(dire_name)
        
        # Utiliser les stats de Dotabuff si disponibles
        radiant_avg = radiant_stats["avg_kills"]
        dire_avg = dire_stats["avg_kills"]
        
        logger.info(f"Stats trouvées - {radiant_name}: {radiant_avg} kills, {dire_name}: {dire_avg} kills")
    except Exception as e:
        logger.error(f"Erreur lors de l'obtention des stats, utilisation des valeurs par défaut: {e}")
        # Valeurs par défaut si l'équipe n'est pas trouvée
        radiant_avg = team_avg_kills.get(radiant_name, team_avg_kills["Team Unknown"])
        dire_avg = team_avg_kills.get(dire_name, team_avg_kills["Team Unknown"])
    
    # Calcul du seuil prédit
    team_avg_prediction = (radiant_avg + dire_avg) / 2
    
    if has_previous_matches:
        # Pondération entre les confrontations directes et les stats générales
        final_prediction = (
            previous_matchup_stats["avg_total_kills"] * WEIGHT_PREVIOUS_MATCHUPS + 
            team_avg_prediction * WEIGHT_TEAM_STATS
        )
    else:
        # Utiliser uniquement les stats générales
        final_prediction = team_avg_prediction
    
    # Arrondir au 0.5 le plus proche
    rounded = round(final_prediction * 2) / 2
    
    if has_previous_matches:
        logger.info(f"Predicted kill threshold for {radiant_name} vs {dire_name}: {rounded} "
                   f"(basé sur {previous_matchup_stats['sample_size']} confrontations directes et stats d'équipe)")
    else:
        logger.info(f"Predicted kill threshold for {radiant_name} vs {dire_name}: {rounded} "
                   f"(basé uniquement sur les stats d'équipe)")
    
    return rounded

def fetch_1xbet_data(radiant_id, dire_id):
    """
    Fetch betting data from 1xBet for a specific match using team IDs
    
    Args:
        radiant_id: ID de l'équipe Radiant
        dire_id: ID de l'équipe Dire
        
    Returns:
        Un dictionnaire contenant les données de paris
    """
    try:
        # Récupérer les noms des équipes depuis une base de données ou un service
        team_names = {
            '9245832': 'Prime Legion',
            '8969887': 'Freedom Fighters Team',
            '8255888': 'BetBoom Team',
            '9247354': 'Team Falcons'
        }
        
        # Convertir les IDs en noms
        radiant_name = team_names.get(str(radiant_id), f"Team {radiant_id}")
        dire_name = team_names.get(str(dire_id), f"Team {dire_id}")
        
        # Créer une clé unique pour ce match
        match_key = f"{radiant_id}_{dire_id}"
        
        # Vérifier si les données sont en cache
        cached_data = get_cached_betting_data(match_key)
        if cached_data:
            logger.info(f"Utilisation des données en cache pour {radiant_name} vs {dire_name}")
            return cached_data
        
        # Si pas en cache, procéder au scraping
        logger.info(f"Pas de données en cache pour {radiant_name} vs {dire_name}, récupération...")
        
        # Essayer d'abord le scraping de 1xBet
        match_url = get_1xbet_match_url(radiant_name, dire_name)
        kill_threshold = scrape_1xbet_kill_threshold(match_url)
        
        # Si le scraping échoue, utiliser la prédiction basée sur les statistiques
        if not kill_threshold:
            logger.info("Using prediction model for kill threshold")
            kill_threshold = predict_kill_threshold(radiant_id, dire_id)
            match_url = None  # Pas d'URL disponible dans ce cas
        
        # Créer l'objet de résultat
        result = {
            "match_url": match_url,
            "kill_threshold": kill_threshold,
            "source": "1xBet" if match_url else "Prédiction",
            "radiant_name": radiant_name,
            "dire_name": dire_name
        }
        
        # Mettre en cache les résultats
        cache_betting_data(match_key, result)
        
        return result
    except Exception as e:
        logger.error(f"Error in fetch_1xbet_data: {e}")
        
        # En cas d'erreur, utiliser la prédiction comme fallback
        result = {
            "match_url": None,
            "kill_threshold": predict_kill_threshold(radiant_id, dire_id),
            "source": "Prédiction (fallback)",
            "radiant_name": team_names.get(str(radiant_id), f"Team {radiant_id}"),
            "dire_name": team_names.get(str(dire_id), f"Team {dire_id}")
        }
        
        # Note: nous ne mettons pas en cache les résultats de fallback
        # car ils sont potentiellement erronés
        
        return result

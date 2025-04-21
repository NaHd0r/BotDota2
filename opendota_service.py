"""
Module d'intégration avec l'API OpenDota pour Dota 2 Dashboard

Ce module fournit des fonctions pour récupérer des données de matchs Dota 2
depuis l'API OpenDota (https://docs.opendota.com/).

Avantages par rapport à Dotabuff:
1. API ouverte et bien documentée
2. Limites de requêtes plus généreuses
3. Format JSON plus facile à traiter que le scraping HTML

Structure:
- Les fonctions de ce module récupèrent des données brutes de l'API
- Les données sont ensuite converties au format attendu par notre application
- Le cache est utilisé pour limiter les requêtes et améliorer les performances

Fonctionnalités principales:
- Enrichissement de match: récupération des données détaillées d'un match terminé
- Mise à jour des gagnants: détermination des vainqueurs des matchs basés sur les données officielles
- Récupération des statistiques: obtention des statistiques détaillées sur les joueurs et équipes

Documentation ajoutée le: 15 avril 2025
Dernière mise à jour: 19 avril 2025
"""

import os
import time
import json
import logging
import datetime
import urllib.parse
import requests
import random
from typing import Dict, List, Optional, Any, Union

from config import CacheConfig
from dual_cache_system import CacheSystem

# Initialiser le système de cache
cache = CacheSystem()

# Configuration du logger
logger = logging.getLogger(__name__)

# URLs de base de l'API OpenDota
OPENDOTA_API_BASE = "https://api.opendota.com/api"

# Liste d'User-Agents pour simuler différents navigateurs
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36 Edg/96.0.1054.53",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:94.0) Gecko/20100101 Firefox/94.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
]

# Liste de proxies libres - ces adresses IP sont fictives et doivent être remplacées par des vraies
# Nous allons utiliser différentes adresses IP pour contourner les limitations
PROXY_LIST = [
    None,  # Pas de proxy = IP directe
    # Les vraies adresses proxy seraient ajoutées ici
]

# Compteur pour alterner les proxies
proxy_index = 0

def get_next_proxy():
    """Retourne le prochain proxy de la liste en alternant"""
    global proxy_index
    proxy = PROXY_LIST[proxy_index]
    proxy_index = (proxy_index + 1) % len(PROXY_LIST)
    return proxy

# Fonction pour obtenir des headers aléatoires pour les requêtes
def get_random_headers():
    """Génère des en-têtes HTTP aléatoires pour éviter la détection de bot"""
    user_agent = random.choice(USER_AGENTS)
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.opendota.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache"
    }
    return headers

# Délai entre les requêtes (secondes)
MIN_REQUEST_DELAY = 2.0  # Augmenté pour éviter les erreurs 429
MAX_REQUEST_DELAY = 5.0  # Augmenté pour éviter les erreurs 429

# Cache pour mémoriser les réponses aux requêtes récentes
API_RESPONSE_CACHE = {}

def add_random_delay():
    """Ajoute un délai aléatoire entre les requêtes pour éviter la détection"""
    delay = random.uniform(MIN_REQUEST_DELAY, MAX_REQUEST_DELAY)
    time.sleep(delay)

def get_opendota_match(match_id: str) -> Optional[Dict[str, Any]]:
    """
    Récupère les détails d'un match depuis l'API OpenDota.
    
    Args:
        match_id: ID du match à récupérer
        
    Returns:
        Dictionnaire contenant les données du match ou None en cas d'erreur
    """
    logger.info(f"Récupération des données du match {match_id} depuis OpenDota")
    
    # Vérifier si les données sont en cache
    cached_data = get_cached_match_data(match_id)
    if cached_data and cached_data.get('data_source') == 'opendota':
        logger.info(f"Utilisation des données en cache pour le match {match_id}")
        return cached_data
    
    # URL de l'API pour les détails d'un match
    url = f"{OPENDOTA_API_BASE}/matches/{match_id}"
    
    try:
        # Ajouter un délai aléatoire pour éviter la détection
        add_random_delay()
        
        # Obtenir des headers aléatoires pour simuler un navigateur réel
        headers = get_random_headers()
        
        # Obtenir un proxy de notre liste rotative
        proxy = get_next_proxy()
        proxies = None
        if proxy:
            proxies = {
                "http": proxy,
                "https": proxy
            }
        
        # Faire la requête avec le proxy si disponible
        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Erreur lors de la récupération du match {match_id} depuis OpenDota: {response.status_code}")
            return None
        
        # Parser les données JSON
        match_data = response.json()
        
        # Convertir au format utilisé par notre application
        processed_data = process_opendota_match(match_data)
        
        # Mettre en cache les données
        if processed_data:
            cache_match_data(match_id, processed_data)
        
        return processed_data
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données du match {match_id} depuis OpenDota: {str(e)}")
        return None

def process_opendota_match(match_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convertit les données d'un match OpenDota au format utilisé par notre application.
    
    Args:
        match_data: Données brutes du match depuis l'API OpenDota
        
    Returns:
        Dictionnaire au format attendu par notre application
    """
    try:
        # Extraire les informations de base
        match_id = str(match_data.get('match_id', '0'))
        duration = match_data.get('duration', 0)  # Durée en secondes
        
        # Conversion de la durée au format MM:SS
        minutes = duration // 60
        seconds = duration % 60
        duration_str = f"{minutes:02}:{seconds:02}"
        
        # Extraire les scores
        radiant_score = match_data.get('radiant_score', 0)
        dire_score = match_data.get('dire_score', 0)
        
        # Déterminer le vainqueur en utilisant radiant_win
        radiant_win = match_data.get('radiant_win', False)
        winner = 'radiant' if radiant_win else 'dire'
        
        # Enrichir avec la traduction équipe1/équipe2 gagnante
        # On utilise isRadiant pour déterminer si l'équipe1 est radiant ou dire
        radiant_team = match_data.get('radiant_team', {})  
        dire_team = match_data.get('dire_team', {})
        
        # Ajouter des informations plus claires sur le vainqueur
        if radiant_win:
            winning_team_id = str(match_data.get('radiant_team_id', '0'))
            winning_team_name = match_data.get('radiant_name', 'Équipe Radiant')
        else:
            winning_team_id = str(match_data.get('dire_team_id', '0'))
            winning_team_name = match_data.get('dire_name', 'Équipe Dire')
            
        # S'assurer que la valeur radiant_win est explicitement un booléen pour éviter les ambiguïtés
        radiant_win = bool(radiant_win)
        
        # Extraire les informations des équipes
        # OpenDota utilise les team_id pour les équipes professionnelles
        radiant_team_id = str(match_data.get('radiant_team_id', '0'))
        dire_team_id = str(match_data.get('dire_team_id', '0'))
        
        radiant_team_name = match_data.get('radiant_name', 'Équipe Radiant')
        dire_team_name = match_data.get('dire_name', 'Équipe Dire')
        
        # Si les noms d'équipe ne sont pas disponibles, utiliser des valeurs par défaut
        if not radiant_team_name:
            radiant_team_name = "Équipe Radiant"
        if not dire_team_name:
            dire_team_name = "Équipe Dire"
        
        # Déterminer le type de match (BO3, BO5, etc.)
        match_type = "Match unique"
        series_type = match_data.get('series_type', 0)
        if series_type == 1:
            match_type = "Best of 3"
        elif series_type == 2:
            match_type = "Best of 5"
        
        # Extraire l'ID de la ligue
        league_id = str(match_data.get('leagueid', '0'))
        
        # Créer un ID de série basé sur la ligue et les équipes impliquées
        # Utiliser min/max pour garantir que l'ordre des équipes n'a pas d'importance
        # Cela permet de regrouper tous les matchs d'une même série même sans series_id explicite
        series_id = f"{league_id}_{min(radiant_team_id, dire_team_id)}_{max(radiant_team_id, dire_team_id)}"
        
        # Créer le dictionnaire au format attendu
        result = {
            'match_id': match_id,
            'duration': duration_str,
            'radiant_team': {
                'id': radiant_team_id,
                'name': radiant_team_name
            },
            'dire_team': {
                'id': dire_team_id,
                'name': dire_team_name
            },
            'radiant_score': radiant_score,
            'dire_score': dire_score,
            'total_kills': radiant_score + dire_score,
            'winner': winner,
            'radiant_win': radiant_win,
            'winning_team_id': winning_team_id,
            'winning_team_name': winning_team_name,
            'match_type': match_type,
            'series_id': series_id,        # ID de série généré
            'league_id': league_id,        # ID de la ligue
            'data_source': 'opendota',     # Marquer la source des données
            'detailed_data': True          # Indique que ce sont des données complètes
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement des données OpenDota: {str(e)}")
        return None

def get_cached_match_data(match_id: str) -> Optional[Dict[str, Any]]:
    """
    Récupère les données de match en cache pour un match spécifique.
    Cette fonction permet d'éviter de refaire des requêtes à OpenDota
    pendant toute la durée d'une partie.
    
    Args:
        match_id: ID du match à récupérer
        
    Returns:
        Dictionnaire contenant les données du match ou None si non trouvé
    """
    # Cette fonction est similaire à celle dans scraper.py
    # Elle serait idéalement partagée ou centralisée
    
    cache_file = CacheConfig.MATCH_DATA_CACHE_FILE
    
    try:
        if not os.path.exists(cache_file):
            return None
        
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        
        # Vérifier si le match est en cache et si les données sont encore valides
        if match_id in cache_data:
            match_data = cache_data[match_id]
            cached_time = match_data.get('cached_time', 0)
            
            # Vérifier si les données sont encore valides
            now = time.time()
            if cached_time + CacheConfig.MATCH_DATA_EXPIRY > now:
                return match_data.get('data')
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données en cache pour le match {match_id}: {str(e)}")
    
    return None

def cache_match_data(match_id: str, data: Dict[str, Any]) -> None:
    """
    Met en cache les données de match OpenDota pour un match spécifique.
    Les données resteront en cache pendant toute la durée d'une partie (8 heures).
    
    Args:
        match_id: ID du match à mettre en cache
        data: Données du match à mettre en cache
    """
    # Cette fonction est similaire à celle dans scraper.py
    # Elle serait idéalement partagée ou centralisée
    
    cache_file = CacheConfig.MATCH_DATA_CACHE_FILE
    
    try:
        # Créer le répertoire de cache s'il n'existe pas
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        
        # Charger les données existantes
        cache_data = {}
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
        
        # Ajouter ou mettre à jour les données du match
        cache_data[match_id] = {
            'cached_time': time.time(),
            'data': data
        }
        
        # Enregistrer les données mises à jour
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        logger.info(f"Données du match {match_id} mises en cache")
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise en cache des données pour le match {match_id}: {str(e)}")

def cached_api_request(url: str, cache_duration: int = 600) -> Optional[Dict[str, Any]]:
    """
    Effectue une requête API avec mise en cache pour éviter les appels répétés.
    
    Args:
        url: L'URL de l'API à appeler
        cache_duration: Durée de validité du cache en secondes (défaut: 10 minutes)
        
    Returns:
        Données JSON de la réponse ou None en cas d'erreur
    """
    now = time.time()
    
    # Vérifier si l'URL est dans le cache et si les données sont encore valides
    if url in API_RESPONSE_CACHE:
        cache_entry = API_RESPONSE_CACHE[url]
        cached_time = cache_entry.get('timestamp', 0)
        
        # Si les données sont encore valides, les retourner
        if cached_time + cache_duration > now:
            logger.info(f"Utilisation des données en cache pour {url}")
            return cache_entry.get('data')
    
    # Obtenir des headers aléatoires pour simuler un navigateur réel
    headers = get_random_headers()
    
    # Obtenir un proxy de notre liste rotative
    proxy = get_next_proxy()
    proxies = None
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy
        }
    
    try:
        # Ajouter un délai aléatoire pour éviter la détection
        add_random_delay()
        
        # Faire la requête avec le proxy si disponible
        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Erreur lors de la requête API à {url}: {response.status_code}")
            return None
        
        # Parser les données JSON
        data = response.json()
        
        # Mettre en cache les données
        API_RESPONSE_CACHE[url] = {
            'timestamp': now,
            'data': data
        }
        
        return data
        
    except Exception as e:
        logger.error(f"Erreur lors de la requête API à {url}: {str(e)}")
        return None

def get_match_details(match_id: str) -> Optional[Dict[str, Any]]:
    """
    Récupère les détails d'un match depuis l'API OpenDota.
    Fonction utilisée par le système d'enrichissement des matchs terminés.
    
    Args:
        match_id: ID du match à récupérer
        
    Returns:
        dict: Données du match ou None en cas d'erreur
    """
    return get_opendota_match(match_id)

def get_team_matches(team_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Récupère les derniers matchs d'une équipe depuis l'API OpenDota.
    
    Args:
        team_id: ID de l'équipe
        limit: Nombre maximum de matchs à récupérer
        
    Returns:
        Liste des matchs de l'équipe
    """
    logger.info(f"Récupération des matchs récents de l'équipe {team_id} depuis OpenDota")
    
    # URL de l'API pour les matchs d'une équipe
    url = f"{OPENDOTA_API_BASE}/teams/{team_id}/matches"
    
    try:
        # Utiliser la fonction de requête avec cache
        matches_data = cached_api_request(url)
        
        if not matches_data:
            return []
            
        # Limiter le nombre de matchs
        matches_data = matches_data[:limit]
        
        # Récupérer les détails complets de chaque match
        detailed_matches = []
        for match in matches_data:
            match_id = str(match.get('match_id', '0'))
            match_details = get_opendota_match(match_id)
            if match_details:
                detailed_matches.append(match_details)
        
        return detailed_matches
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des matchs de l'équipe {team_id} depuis OpenDota: {str(e)}")
        return []

def get_matches_by_series(series_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Récupère les matchs d'une série spécifique.
    
    Note: OpenDota n'a pas d'API dédiée pour les séries, nous utilisons donc une approche
    basée sur les matchs ayant le même league_id et impliquant les mêmes équipes dans un intervalle de temps proche.
    
    Args:
        series_id: ID de la série ou d'un match de la série
        limit: Nombre maximum de matchs à récupérer
        
    Returns:
        Liste des matchs de la série
    """
    logger.info(f"Récupération des matchs de la série {series_id} depuis OpenDota")
    
    # Si series_id est un ID de match, utiliser ce match comme point de départ
    match_details = get_opendota_match(series_id)
    
    if not match_details:
        logger.error(f"Impossible de récupérer les détails du match/série {series_id}")
        return []
    
    # Extraire les informations pour identifier la série
    radiant_team_id = match_details.get('radiant_team', {}).get('id', '0')
    dire_team_id = match_details.get('dire_team', {}).get('id', '0')
    
    # Si nous avons des IDs d'équipe valides, chercher les matchs récents entre ces équipes
    if radiant_team_id != '0' and dire_team_id != '0':
        logger.info(f"Recherche de matchs entre les équipes {radiant_team_id} et {dire_team_id} pour la série {series_id}")
        
        # Passer l'ID de série pour enrichir les données des matchs
        matches = get_team_vs_team_matches(radiant_team_id, dire_team_id, limit, series_id=series_id)
        
        # Vérifier que le premier match existe et est bien le match de point de départ
        if matches and matches[0].get('match_id') != series_id:
            # Si le match de point de départ n'est pas dans les résultats, l'ajouter 
            # (si nous avons utilisé un ID de match comme point de départ)
            match_details['series_id'] = series_id
            match_details['game_number'] = 1  # Par défaut, considérer comme le premier match
            
            # Réarranger la liste pour mettre ce match en premier
            matches = [match_details] + [m for m in matches if m.get('match_id') != series_id][:limit-1]
            
        # Trier les matchs par date pour une attribution chronologique des numéros de jeu
        matches.sort(key=lambda x: int(x.get('start_time', 0)) if x.get('start_time') else 0)
        
        # S'assurer que tous les matchs ont l'ID de série et un numéro de jeu chronologique
        for i, match in enumerate(matches):
            if not match.get('series_id'):
                match['series_id'] = series_id
            
            # Assigner le numéro de jeu de manière chronologique
            match['game_number'] = i + 1
            
            # Ajouter le type de match si non défini
            if not match.get('match_type'):
                if len(matches) == 3:
                    match['match_type'] = "Best of 3"
                elif len(matches) == 5:
                    match['match_type'] = "Best of 5"
                else:
                    match['match_type'] = f"Série de {len(matches)} matchs"
        
        # Remettre dans l'ordre du plus récent au plus ancien pour l'affichage
        matches.sort(key=lambda x: int(x.get('start_time', 0)) if x.get('start_time') else 0, reverse=True)
        
        return matches
    
    # Sinon, retourner juste ce match
    match_details['series_id'] = series_id  # Ajouter l'ID de série
    return [match_details]

def enrich_match(match_id: str) -> bool:
    """
    Enrichit les données d'un match terminé en récupérant les informations détaillées
    depuis l'API OpenDota et en mettant à jour le cache.
    
    Cette fonction est généralement appelée automatiquement quand un match passe à 
    l'état "finished" pour obtenir les données officielles de durée et de vainqueur.
    
    Args:
        match_id: ID du match à enrichir
        
    Returns:
        Boolean indiquant si l'enrichissement a réussi
    """
    logger.info(f"🔄 Début de l'enrichissement du match {match_id} via OpenDota")
    
    try:
        # Récupérer les données actuelles du match
        current_match_data = cache.get_match_from_live_cache(match_id)
        
        if not current_match_data:
            logger.warning(f"❌ Match {match_id} non trouvé dans le cache live")
            return False
        
        # Récupérer les données enrichies depuis OpenDota
        opendota_data = get_opendota_match(match_id)
        
        if not opendota_data:
            logger.warning(f"❌ Impossible de récupérer les données du match {match_id} depuis OpenDota")
            return False
        
        # Mise à jour des informations importantes
        current_match_data["duration"] = opendota_data.get("duration", current_match_data.get("duration", "0:00"))
        current_match_data["radiant_score"] = opendota_data.get("radiant_score", current_match_data.get("radiant_score", 0))
        current_match_data["dire_score"] = opendota_data.get("dire_score", current_match_data.get("dire_score", 0))
        current_match_data["total_kills"] = opendota_data.get("total_kills", current_match_data.get("total_kills", 0))
        
        # Mise à jour du vainqueur
        winner = opendota_data.get("winner", "pending")
        if winner != "pending":
            current_match_data["winner"] = winner
            logger.info(f"✅ Mise à jour du vainqueur pour le match {match_id}: {winner}")
        
        # Mise à jour du statut
        current_match_data["status"] = "finished"
        current_match_data["status_tag"] = "finished"
        
        # Ajout d'un marqueur d'enrichissement
        current_match_data["enriched"] = True
        current_match_data["enriched_time"] = int(time.time())
        
        # Mise à jour du cache
        cache.add_match_to_live_cache(current_match_data)
        cache.transfer_match_to_historical_cache(match_id)
        
        logger.info(f"✅ Enrichissement du match {match_id} terminé avec succès")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'enrichissement du match {match_id}: {str(e)}")
        return False

def update_series_with_previous_match(current_series_id: str, previous_match_id: str) -> bool:
    """
    Met à jour les scores de série en récupérant les informations du match précédent via OpenDota
    
    Args:
        current_series_id: ID de la série actuelle
        previous_match_id: ID du match précédent à récupérer
        
    Returns:
        Boolean indiquant si la mise à jour a réussi
    """
    logger.info(f"Tentative de mise à jour de la série {current_series_id} avec le match précédent {previous_match_id}")
    
    # Récupérer les informations du match précédent
    match_data = get_opendota_match(previous_match_id)
    if not match_data:
        logger.error(f"Impossible de récupérer les données du match {previous_match_id} depuis OpenDota")
        return False
    
    # Traiter les données du match
    processed_match = match_data  # Si le résultat de get_opendota_match est déjà traité
    
    # Vérifier si le match est terminé
    if not processed_match.get('radiant_win') and processed_match.get('winner') is None:
        logger.warning(f"Le match {previous_match_id} n'est pas marqué comme terminé")
        return False
    
    # Mettre à jour directement le cache des séries
    radiant_win = processed_match.get('radiant_win', False)
    
    # Charger le cache des séries
    series_cache_file = os.path.join(CacheConfig.CACHE_DIRECTORY, "series_cache.json")
    try:
        if os.path.exists(series_cache_file):
            with open(series_cache_file, 'r') as f:
                series_cache = json.load(f)
        else:
            series_cache = {}
    except Exception as e:
        logger.error(f"Erreur lors du chargement du cache des séries: {str(e)}")
        return False
    
    # Mettre à jour le score de la série
    series_key = str(current_series_id)
    match_id_str = str(previous_match_id)
    
    if series_key in series_cache:
        series_data = series_cache[series_key]
        logger.info(f"Mise à jour du score pour la série {series_key} avec match {match_id_str}")
        
        # Vérifier si le match a déjà été comptabilisé
        match_found = False
        for match in series_data.get('matches', []):
            if str(match.get('match_id', '')) == match_id_str:
                match_found = True
                logger.info(f"Match {match_id_str} déjà comptabilisé, pas de mise à jour")
                break
        
        if not match_found:
            # Mettre à jour le score
            if radiant_win:
                series_data['radiant_score'] = series_data.get('radiant_score', 0) + 1
            else:
                series_data['dire_score'] = series_data.get('dire_score', 0) + 1
            
            # Ajouter le match à la liste des matchs de la série
            match_data = {
                'match_id': match_id_str,
                'radiant_win': radiant_win,
                'match_outcome': 1 if radiant_win else 2,  # 1 = victoire radiant, 2 = victoire dire
                'timestamp': int(time.time()),
                'match_end_time': int(time.time())
            }
            
            # Ajouter les informations de l'équipe et de la ligue si elles sont présentes
            if 'radiant_team' in processed_match:
                match_data['radiant_team_id'] = processed_match['radiant_team'].get('id', '')
                match_data['radiant_team_name'] = processed_match['radiant_team'].get('name', '')
            
            if 'dire_team' in processed_match:
                match_data['dire_team_id'] = processed_match['dire_team'].get('id', '')
                match_data['dire_team_name'] = processed_match['dire_team'].get('name', '')
            
            if 'league_id' in processed_match:
                match_data['league_id'] = processed_match['league_id']
            
            # Ajouter le score et la durée si disponibles
            if 'radiant_score' in processed_match:
                match_data['radiant_score'] = processed_match['radiant_score']
            
            if 'dire_score' in processed_match:
                match_data['dire_score'] = processed_match['dire_score']
            
            if 'duration' in processed_match:
                match_data['duration'] = processed_match['duration']
                match_data['duration_formatted'] = processed_match.get('duration', '0:00')
            
            # Ajouter le total des kills si disponible
            if 'total_kills' in processed_match:
                match_data['total_kills'] = processed_match['total_kills']
            elif 'radiant_score' in processed_match and 'dire_score' in processed_match:
                match_data['total_kills'] = processed_match['radiant_score'] + processed_match['dire_score']
            
            # Ajouter le match à la liste
            if 'matches' not in series_data:
                series_data['matches'] = []
            
            series_data['matches'].append(match_data)
            logger.info(f"Match {match_id_str} ajouté à la série {series_key} avec le résultat final")
            
            # Mettre à jour la date de dernière mise à jour
            series_data['last_update_time'] = int(time.time())
            
            # Enregistrer les modifications
            with open(series_cache_file, 'w') as f:
                json.dump(series_cache, f)
            
            logger.info(f"Série {series_key} mise à jour avec succès : match {match_id_str}, victoire radiant: {radiant_win}")
            return True
        
    else:
        logger.warning(f"Série {series_key} non trouvée dans le cache")
    
    return False

def get_team_vs_team_matches(team1_id: str, team2_id: str, limit: int = 5, series_id: str = None) -> List[Dict[str, Any]]:
    """
    Récupère les matchs récents entre deux équipes spécifiques.
    
    Args:
        team1_id: ID de la première équipe
        team2_id: ID de la deuxième équipe
        limit: Nombre maximum de matchs à récupérer
        series_id: ID de série optionnel pour enrichir les données
        
    Returns:
        Liste des matchs entre les deux équipes
    """
    logger.info(f"Récupération des matchs entre les équipes {team1_id} et {team2_id} depuis OpenDota")
    
    # S'assurer que les IDs d'équipe sont toujours des chaînes pour la comparaison
    team1_id = str(team1_id)
    team2_id = str(team2_id)
    
    # APPROCHE 1: Utiliser l'API teams/{team_id}/matches pour la première équipe
    # Cette méthode devrait théoriquement fonctionner mais peut ne pas renvoyer les matchs très récents
    team1_matches = get_team_matches(team1_id, 20)  # Récupérer plus de matchs pour augmenter les chances
    
    # Filtrer pour ne garder que les matchs contre la deuxième équipe
    vs_matches = []
    for match in team1_matches:
        # Extraire et normaliser les IDs des équipes (toujours en chaîne)
        dire_team = match.get('dire_team', {})
        radiant_team = match.get('radiant_team', {})
        
        # Possibilité 1: Utiliser la structure OpenDota (.get('id'))
        dire_team_id = str(dire_team.get('id', '0'))
        radiant_team_id = str(radiant_team.get('id', '0'))
        
        # Possibilité 2: Utiliser l'ancien format (team_id présent)
        if dire_team_id == '0' and 'team_id' in dire_team:
            dire_team_id = str(dire_team.get('team_id', '0'))
        if radiant_team_id == '0' and 'team_id' in radiant_team:
            radiant_team_id = str(radiant_team.get('team_id', '0'))
        
        # Possibilité 3: Au cas où les IDs seraient directement dans la structure match
        if dire_team_id == '0' and match.get('dire_team_id'):
            dire_team_id = str(match.get('dire_team_id', '0'))
        if radiant_team_id == '0' and match.get('radiant_team_id'):
            radiant_team_id = str(match.get('radiant_team_id', '0'))
        
        logger.debug(f"Comparaison d'équipes - Match: {match.get('match_id')} - Dire: {dire_team_id}, Radiant: {radiant_team_id} vs recherchée: {team2_id}")
        
        # Vérifier si l'équipe 2 est impliquée dans ce match (comparaison entre chaînes)
        if dire_team_id == team2_id or radiant_team_id == team2_id:
            logger.info(f"Match trouvé entre équipes {team1_id} et {team2_id}: {match.get('match_id')}")
            
            # Si une série est spécifiée, enrichir les données du match
            if series_id:
                # Ajouter l'ID de série si manquant
                if not match.get('series_id'):
                    match['series_id'] = series_id
                # Ajouter le numéro de match dans la série
                if 'game_number' not in match and len(vs_matches) == 0:
                    match['game_number'] = 1  # Premier match trouvé = Game 1
                elif 'game_number' not in match:
                    match['game_number'] = len(vs_matches) + 1
            
            vs_matches.append(match)
            
            # Limiter le nombre de matchs
            if len(vs_matches) >= limit:
                break
    
    # Si nous avons trouvé des matchs, les retourner
    if vs_matches:
        logger.info(f"Trouvé {len(vs_matches)} matchs entre les équipes {team1_id} et {team2_id} via l'API équipe")
        return vs_matches
    
    # APPROCHE 2: Recherche bidirectionnelle pour être plus exhaustif
    logger.info(f"Recherche bidirectionnelle des matchs entre {team1_id} et {team2_id}")

    try:
        vs_matches = []

        # 1ère direction: Récupérer les matchs récents de l'équipe 1 et chercher ceux contre l'équipe 2
        url1 = f"{OPENDOTA_API_BASE}/teams/{team1_id}/matches"
        
        # Ajouter un délai aléatoire pour éviter la détection
        add_random_delay()
        
        # Obtenir des headers aléatoires pour simuler un navigateur réel
        headers = get_random_headers()
        
        # Obtenir un proxy de notre liste rotative
        proxy = get_next_proxy()
        proxies = None
        if proxy:
            proxies = {
                "http": proxy,
                "https": proxy
            }
        
        response1 = requests.get(url1, headers=headers, proxies=proxies, params={'limit': 50}, timeout=5)
        
        if response1.status_code == 200:
            team1_matches = response1.json()
            
            for match in team1_matches:
                match_id = str(match.get('match_id', '0'))
                opposing_team_id = str(match.get('opposing_team_id', '0'))
                
                if opposing_team_id == team2_id:
                    match_details = get_opendota_match(match_id)
                    if match_details:
                        if series_id and not match_details.get('series_id'):
                            match_details['series_id'] = series_id
                        
                        match_details['game_number'] = len(vs_matches) + 1
                        vs_matches.append(match_details)
                        
                        if len(vs_matches) >= limit:
                            break
        
        # Si on n'a pas assez de matchs, essayer dans l'autre direction
        if len(vs_matches) < limit:
            # 2ème direction: Récupérer les matchs récents de l'équipe 2 et chercher ceux contre l'équipe 1
            url2 = f"{OPENDOTA_API_BASE}/teams/{team2_id}/matches"
            
            # Ajouter un délai aléatoire pour éviter la détection
            add_random_delay()
            
            # Obtenir des headers aléatoires pour simuler un navigateur réel
            headers = get_random_headers()
            
            # Obtenir un proxy de notre liste rotative
            proxy = get_next_proxy()
            proxies = None
            if proxy:
                proxies = {
                    "http": proxy,
                    "https": proxy
                }
            
            response2 = requests.get(url2, headers=headers, proxies=proxies, params={'limit': 50}, timeout=5)
            
            if response2.status_code == 200:
                team2_matches = response2.json()
                
                for match in team2_matches:
                    match_id = str(match.get('match_id', '0'))
                    opposing_team_id = str(match.get('opposing_team_id', '0'))
                    
                    # Vérifier si c'est un match contre l'équipe 1 et qu'il n'est pas déjà dans notre liste
                    if opposing_team_id == team1_id and not any(m.get('match_id') == match_id for m in vs_matches):
                        match_details = get_opendota_match(match_id)
                        if match_details:
                            if series_id and not match_details.get('series_id'):
                                match_details['series_id'] = series_id
                            
                            # Ajouter les informations sur l'équipe gagnante si disponibles
                            radiant_win = match_details.get('radiant_win', False)
                            if 'radiant_win' in match_details:
                                if radiant_win:
                                    match_details['winner'] = 'radiant'
                                    # Trouver quel ID d'équipe est radiant
                                    if match_details.get('radiant_team', {}).get('team_id', '0') in [team1_id, team2_id]:
                                        match_details['winning_team_id'] = match_details.get('radiant_team', {}).get('team_id', '0')
                                        match_details['winning_team_name'] = match_details.get('radiant_team', {}).get('name', 'Équipe Radiant')
                                else:
                                    match_details['winner'] = 'dire'
                                    # Trouver quel ID d'équipe est dire
                                    if match_details.get('dire_team', {}).get('team_id', '0') in [team1_id, team2_id]:
                                        match_details['winning_team_id'] = match_details.get('dire_team', {}).get('team_id', '0')
                                        match_details['winning_team_name'] = match_details.get('dire_team', {}).get('name', 'Équipe Dire')
                            
                            match_details['game_number'] = len(vs_matches) + 1
                            vs_matches.append(match_details)
                            
                            if len(vs_matches) >= limit:
                                break
        
        # Trier les matchs par date (du plus ancien au plus récent) pour l'affectation correcte des numéros de jeu
        vs_matches.sort(key=lambda x: int(x.get('start_time', 0)) if x.get('start_time') else 0)
        
        # Réassigner les numéros de jeu selon l'ordre chronologique
        for i, match in enumerate(vs_matches):
            match['game_number'] = i + 1
            
        # Retrier les matchs par date (du plus récent au plus ancien) pour l'affichage
        vs_matches.sort(key=lambda x: int(x.get('start_time', 0)) if x.get('start_time') else 0, reverse=True)
        
        logger.info(f"Trouvé {len(vs_matches)} matchs entre {team1_id} et {team2_id} via la recherche bidirectionnelle")
        return vs_matches[:limit]  # Limiter le nombre de résultats
            
    except Exception as e:
        logger.error(f"Erreur lors de la recherche de matchs: {str(e)}")
        return []
        
    # Si aucune méthode n'a fonctionné, retourner une liste vide
    return []

if __name__ == "__main__":
    # Code de test pour le module
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Test avec un ID de match terminé (match historique connu)
    match_id = "7224753820"  # Un match professionnel terminé
    match_details = get_opendota_match(match_id)
    
    if match_details:
        logger.info(f"Détails du match {match_id}:")
        logger.info(f"  {match_details.get('radiant_team', {}).get('name', 'Équipe Radiant')} vs {match_details.get('dire_team', {}).get('name', 'Équipe Dire')}")
        logger.info(f"  Score: {match_details.get('radiant_score', '?')} - {match_details.get('dire_score', '?')}")
        logger.info(f"  Durée: {match_details.get('duration', '?')}")
        logger.info(f"  Vainqueur: {match_details.get('winner', 'inconnu')}")
    else:
        logger.error(f"Impossible de récupérer les détails du match {match_id}")
        
    # Test de récupération des matchs entre équipes
    team1_id = "15"  # PSG.LGD
    team2_id = "2163"  # Team Spirit
    
    logger.info(f"Récupération des matchs entre {team1_id} et {team2_id}")
    vs_matches = get_team_vs_team_matches(team1_id, team2_id, 2)
    
    logger.info(f"Nombre de matchs trouvés: {len(vs_matches)}")
    for i, match in enumerate(vs_matches):
        logger.info(f"Match {i+1}:")
        logger.info(f"  {match.get('radiant_team', {}).get('name', 'Équipe Radiant')} vs {match.get('dire_team', {}).get('name', 'Équipe Dire')}")
        logger.info(f"  Score: {match.get('radiant_score', '?')} - {match.get('dire_score', '?')}")
        logger.info(f"  Durée: {match.get('duration', '?')}")
        logger.info(f"  Vainqueur: {match.get('winner', 'inconnu')}")
import time
import logging
import json
import requests
from datetime import datetime
from scraper import fetch_1xbet_data
from config import (
    STEAM_API_KEY, BASE_URL_LIVE, LEAGUE_IDS, LEAGUE_NAMES,
    TEAMS, HELLFIRE_ID, HEADERS
)

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# S'assurer que notre logger est au niveau DEBUG
logger.setLevel(logging.DEBUG)

# Les données TEAMS et HELLFIRE_ID sont maintenant importées de config.py

def fetch_live_matches():
    """Fetch live matches from Steam API for all monitored leagues"""
    all_games = []
    
    for league_id in LEAGUE_IDS:
        params = {"key": STEAM_API_KEY, "league_id": league_id}
        try:
            response = requests.get(BASE_URL_LIVE, params=params, headers=HEADERS)
            if response.status_code != 200:
                logger.error(f"API Live Error for league {league_id}: {response.status_code} - {response.text}")
                continue
                
            data = response.json()
            games = data.get("result", {}).get("games", [])
            
            # Ajouter le nom et l'ID de la ligue à chaque match
            for game in games:
                game["league_name"] = LEAGUE_NAMES.get(league_id, f"League {league_id}")
                game["league_id"] = league_id
            
            all_games.extend(games)
            logger.info(f"Live matches found in {LEAGUE_NAMES.get(league_id, f'League {league_id}')}: {len(games)}")
            
        except Exception as e:
            logger.error(f"Error fetching live matches for league {league_id}: {e}")
    
    logger.info(f"Total live matches found: {len(all_games)}")
    return all_games

def format_duration(seconds):
    """Format duration in seconds to MM:SS format"""
    seconds = int(seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"

def process_team_details(team_id, players):
    """Process and format team details including players and net worth"""
    processed_players = {}
    total_net_worth = 0
    
    logger.debug(f"Processing team {team_id} with players: {players}")
    
    for account_id, net_worth in players.items():
        if isinstance(net_worth, (int, float)):
            processed_players[account_id] = net_worth
            total_net_worth += net_worth
        else:
            processed_players[account_id] = "N/A"
    
    result = {
        "team_id": team_id,
        "players": processed_players,
        "total_net_worth": total_net_worth
    }
    
    logger.debug(f"Processed team details: {result}")
    return result

def get_match_type(match):
    """
    Obtient des informations sur le type de match/série
    
    Valeurs possibles pour series_type :
    0: Non défini ou partie unique
    1: Meilleur des 3 (Bo3)
    2: Meilleur des 5 (Bo5)
    """
    series_type = match.get("series_type", 0)
    radiant_series_wins = match.get("radiant_series_wins", 0)
    dire_series_wins = match.get("dire_series_wins", 0)
    
    match_types = {
        0: "Single Match",
        1: f"Best of 3 ({radiant_series_wins}-{dire_series_wins})",
        2: f"Best of 5 ({radiant_series_wins}-{dire_series_wins})"
    }
    
    return {
        "series_type": series_type,
        "description": match_types.get(series_type, "Unknown format"),
        "radiant_series_wins": radiant_series_wins,
        "dire_series_wins": dire_series_wins
    }

def is_draft_phase(match):
    """
    Détermine si un match est en phase de draft ou en jeu
    Critères pour la phase de draft:
    - 0 kills pour les deux équipes
    - Durée inférieure à 60 secondes (le match n'a pas encore vraiment commencé)
    """
    scoreboard = match.get("scoreboard", {})
    radiant_score = scoreboard.get("radiant", {}).get("score", 0)
    dire_score = scoreboard.get("dire", {}).get("score", 0)
    duration = scoreboard.get("duration", 0)
    
    # Si pas de kills et durée < 60 secondes, probablement en draft
    if radiant_score == 0 and dire_score == 0 and duration < 60:
        return True
    
    return False

def get_live_matches():
    """Get and process live matches data"""
    matches = fetch_live_matches()
    if not matches:
        return []
    
    processed_matches = []
    
    for match in matches:
        try:
            # On récupère les données directement de l'API sans transformation
            match_id = match.get("match_id", "Unknown")
            
            # Données des équipes - exactement comme retournées par l'API
            radiant_team = match.get("radiant_team", {})
            dire_team = match.get("dire_team", {})
            
            # Score et durée
            scoreboard = match.get("scoreboard", {})
            
            # Logs détaillés pour déboguer
            logger.debug(f"Scoreboard raw data: {json.dumps(scoreboard, indent=2)}")
            
            radiant_board = scoreboard.get("radiant", {})
            dire_board = scoreboard.get("dire", {})
            
            logger.debug(f"Radiant scoreboard: {json.dumps(radiant_board, indent=2)}")
            logger.debug(f"Dire scoreboard: {json.dumps(dire_board, indent=2)}")
            
            radiant_score = radiant_board.get("score", 0)
            dire_score = dire_board.get("score", 0)
            total_kills = radiant_score + dire_score
            duration = scoreboard.get("duration", 0)
            
            # Déterminer si le match est en phase de draft
            is_draft = is_draft_phase(match)
            
            # Obtenir les informations sur le type de match/série
            match_type_info = get_match_type(match)
            
            logger.debug(f"Scores - Radiant: {radiant_score}, Dire: {dire_score}, Duration: {duration}")
            
            # Logger les informations brutes
            radiant_name = radiant_team.get("team_name", "Unknown Radiant")
            dire_name = dire_team.get("team_name", "Unknown Dire")
            match_state = "DRAFT" if is_draft else "IN PROGRESS"
            logger.info(f"Match {match_id}: {radiant_name}({radiant_team.get('team_id')}) vs {dire_name}({dire_team.get('team_id')})")
            logger.info(f"Score: {radiant_score}-{dire_score}, Duration: {format_duration(duration)}, State: {match_state}")
            logger.info(f"Series: {match_type_info['description']}")
            
            # On transmet ces données telles quelles au frontend
            processed_match = {
                "match_id": match_id,
                "league_id": match.get("league_id", 0),
                "league_name": match.get("league_name", "Unknown League"),
                "radiant_team": radiant_team,  # Données brutes de l'équipe
                "dire_team": dire_team,        # Données brutes de l'équipe
                "duration": format_duration(duration),
                "duration_seconds": duration,
                "radiant_score": radiant_score,
                "dire_score": dire_score,
                "total_kills": total_kills,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "scoreboard": scoreboard,      # On ajoute le scoreboard pour avoir accès aux données des joueurs
                "is_draft": is_draft,          # Ajouter l'information sur l'état du match
                "match_type": match_type_info  # Ajouter les informations sur le type de match/série
            }
            
            processed_matches.append(processed_match)
        except Exception as e:
            logger.error(f"Error processing match: {e}")
    
    return processed_matches

def format_matches_for_display(matches):
    """Format matches for display in the web UI"""
    if not matches:
        return []
    
    # The matches are already processed in get_live_matches
    return matches

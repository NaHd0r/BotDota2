import logging
from dota_service import fetch_live_matches, get_live_matches, process_team_details
import json

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_steam_api():
    """Test direct de l'API Steam pour récupérer les matchs"""
    logger.info("Récupération des matchs en direct via l'API Steam...")
    raw_matches = fetch_live_matches()
    
    if raw_matches:
        logger.info(f"✅ Succès! {len(raw_matches)} matchs trouvés")
        
        # Afficher les informations de base sur les matchs
        for i, match in enumerate(raw_matches):
            match_id = match.get("match_id", "Inconnu")
            radiant_team_id = match.get("radiant_team", {}).get("team_id", 0)
            dire_team_id = match.get("dire_team", {}).get("team_id", 0)
            
            from dota_service import TEAMS
            radiant_name = TEAMS.get(radiant_team_id, f"Équipe inconnue ({radiant_team_id})")
            dire_name = TEAMS.get(dire_team_id, f"Équipe inconnue ({dire_team_id})")
            
            logger.info(f"Match {i+1}: {match_id}")
            logger.info(f"  Équipes: {radiant_name} vs {dire_name}")
            
            # Pour débugger le type de match/game
            if 'game_mode' in match:
                logger.info(f"  Mode de jeu: {match['game_mode']}")
            if 'lobby_type' in match:
                logger.info(f"  Type de lobby: {match['lobby_type']}")
            if 'match_flags' in match:
                logger.info(f"  Match flags: {match['match_flags']}")
            if 'server_steam_id' in match:
                logger.info(f"  Server ID: {match['server_steam_id']}")
                
            # Informations supplémentaires
            logger.info("  Toutes les clés disponibles: " + ", ".join([key for key in match.keys()]))
            
            # Extraire le score
            scoreboard = match.get("scoreboard", {})
            if scoreboard:
                radiant_score = scoreboard.get("radiant", {}).get("score", 0)
                dire_score = scoreboard.get("dire", {}).get("score", 0)
                duration = scoreboard.get("duration", 0)
                
                logger.info(f"  Score: {radiant_score} - {dire_score}")
                # La durée est un nombre à virgule, on convertit en int avant de formater
                minutes = int(duration) // 60
                seconds = int(duration) % 60
                logger.info(f"  Durée: {minutes}:{seconds:02d}")
            
            logger.info("----------------------------------")
        
        # Traiter les matchs avec notre service
        logger.info("\nTraitement des matchs avec notre service:")
        processed_matches = get_live_matches()
        
        if processed_matches:
            logger.info(f"✅ {len(processed_matches)} matchs traités avec succès")
            
            # Afficher les matchs traités
            for i, match in enumerate(processed_matches):
                logger.info(f"Match {i+1} traité:")
                logger.info(f"  Teams: {match['radiant']['team_name']} vs {match['dire']['team_name']}")
                logger.info(f"  Score: {match['radiant_score']} - {match['dire_score']}")
                logger.info(f"  Total kills: {match['total_kills']}")
                logger.info(f"  Duration: {match['duration']}")
                logger.info(f"  Net worth difference: {match['net_worth_difference']}")
                logger.info(f"  Leading team: {match['leading_team']}")
                
                if match['alerts']['low_kill_alert']:
                    logger.info("  ⚠️ ALERTE: Moins de 10 kills à 10 minutes!")
                    
                if match['alerts']['special_matchup']:
                    logger.info("  🌟 Match spécial: Monlight Wispers vs Project Achilles!")
                    
                if match['hellfire']['playing']:
                    logger.info(f"  🔥 Hellfire joue pour {match['hellfire']['team']}")
                
                # Betting info
                logger.info(f"  Betting info: {json.dumps(match['betting'], indent=2)}")
                logger.info("----------------------------------")
                
    else:
        logger.error("❌ Échec de la récupération des matchs en direct")

if __name__ == "__main__":
    logger.info("=== Test de l'API Dota 2 ===")
    test_steam_api()
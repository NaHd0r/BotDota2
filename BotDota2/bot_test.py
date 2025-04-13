#!/usr/bin/env python3
import os
import logging
from config import TELEGRAM_BOT_TOKEN
from dota_service import get_live_matches

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_match_info(match):
    """Format match information for display"""
    radiant_name = match["radiant"]["team_name"]
    dire_name = match["dire"]["team_name"]
    match_id = match["match_id"]
    duration = match["duration"]
    radiant_score = match["radiant_score"]
    dire_score = match["dire_score"]
    total_kills = match["total_kills"]
    
    output = []
    output.append(f"🎮 Match ID: {match_id}")
    output.append(f"⚔️ {radiant_name} vs {dire_name}")
    output.append(f"⏱️ Durée: {duration}")
    output.append(f"🔴 {radiant_name}: {radiant_score} kills")
    output.append(f"🔵 {dire_name}: {dire_score} kills")
    output.append(f"📊 Total: {total_kills} kills")
    output.append("")
    
    # Add betting information
    if match["betting"].get("kill_threshold"):
        output.append(f"💰 Seuil Total Kills (1xBet): {match['betting']['kill_threshold']}")
        if match["betting"].get("match_url"):
            output.append(f"🔗 {match['betting']['match_url']}")
        output.append("")
    else:
        output.append("💰 Informations de paris non disponibles")
        output.append("")
    
    # Net worth
    radiant_nw = match["radiant"]["total_net_worth"]
    dire_nw = match["dire"]["total_net_worth"]
    nw_diff = match["net_worth_difference"]
    
    output.append(f"💲 Net Worth:")
    output.append(f"🔴 {radiant_name}: {radiant_nw} or")
    output.append(f"🔵 {dire_name}: {dire_nw} or")
    
    if nw_diff > 0:
        output.append(f"📈 {radiant_name} a un avantage de {nw_diff} or")
    elif nw_diff < 0:
        output.append(f"📈 {dire_name} a un avantage de {abs(nw_diff)} or")
    else:
        output.append(f"📊 Net Worth égal")
    output.append("")
    
    # Alerts
    if match["alerts"]["low_kill_alert"]:
        output.append(f"⚠️ ALERTE: Moins de 10 kills à la 10ème minute!")
        output.append("")
    
    # Special match
    if match["alerts"]["special_matchup"]:
        output.append(f"🌟 Match spécial: Monlight Wispers vs Project Achilles!")
        if match["hellfire"]["playing"]:
            hellfire_team = match["hellfire"]["team"]
            hellfire_nw = match["hellfire"]["net_worth"]
            output.append(f"🔥 Hellfire joue pour {hellfire_team}, Net Worth: {hellfire_nw} or")
        output.append("")
    
    return "\n".join(output)

def test_bot():
    """Test le bot Telegram en local"""
    logger.info("=== Test du Bot Telegram ===")
    
    # Vérifier si le token Telegram est configuré
    if not TELEGRAM_BOT_TOKEN:
        logger.error("⚠️ ERREUR: Token Telegram non configuré!")
        logger.error("Vérifiez le fichier .env ou export TELEGRAM_BOT_TOKEN=votre_token")
        return
    
    # Afficher la valeur masquée du token
    token_length = len(TELEGRAM_BOT_TOKEN)
    visible_chars = 4
    masked_token = TELEGRAM_BOT_TOKEN[:visible_chars] + "*" * (token_length - 2*visible_chars) + TELEGRAM_BOT_TOKEN[-visible_chars:]
    logger.info(f"Token Telegram configuré: {masked_token}")
    
    # Tester les fonctionnalités de base
    logger.info("Test des fonctionnalités de base...")
    
    # Récupérer les matchs en direct
    logger.info("Récupération des matchs en direct...")
    matches = get_live_matches()
    
    if not matches:
        logger.info("Aucun match en direct trouvé. 😔")
    else:
        logger.info(f"{len(matches)} match(s) en direct trouvé(s):")
        
        # Afficher les informations pour chaque match
        for i, match in enumerate(matches):
            logger.info(f"Match {i+1}:")
            logger.info("-" * 50)
            logger.info(format_match_info(match))
            logger.info("-" * 50)
    
    logger.info("Test terminé!")

if __name__ == "__main__":
    test_bot()
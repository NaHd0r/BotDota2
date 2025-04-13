import logging
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
    if match["betting"]["kill_threshold"]:
        output.append(f"💰 Seuil Total Kills (1xBet): {match['betting']['kill_threshold']}")
        if match["betting"]["match_url"]:
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

def test_matches_command():
    """Test the matches command functionality"""
    logger.info("Recherche des matchs en direct en cours...")
    
    # Get live matches
    matches = get_live_matches()
    
    if not matches:
        logger.info("Aucun match en direct trouvé. 😔")
        return
    
    logger.info(f"{len(matches)} match(s) en direct trouvé(s):")
    
    # Show information for each match
    for i, match in enumerate(matches):
        logger.info(f"\nMatch {i+1}:")
        logger.info("-" * 50)
        logger.info(format_match_info(match))
        logger.info("-" * 50)

def main():
    """Main function"""
    logger.info("=== Test du bot Dota 2 en local ===")
    
    test_matches_command()
    
    logger.info("Test terminé!")

if __name__ == "__main__":
    main()
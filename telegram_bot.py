import logging
import asyncio
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
except ImportError:
    from python_telegram_bot import Update
    from python_telegram_bot.ext import Application, CommandHandler, ContextTypes
import html
from dota_service import get_live_matches, format_duration
from config import (
    TELEGRAM_BOT_TOKEN, 
    NO_MATCH_CHECK_INTERVAL, 
    MATCH_CHECK_INTERVAL_MIN, 
    MATCH_CHECK_INTERVAL_MAX
)

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Token du bot Telegram (à partir du fichier de configuration)
BOT_TOKEN = TELEGRAM_BOT_TOKEN

# Fonction de démarrage du bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envoie un message quand la commande /start est utilisée."""
    user = update.effective_user
    await update.message.reply_html(
        f"Bonjour {html.escape(user.first_name)} 👋\n\n"
        f"Je suis un bot qui surveille les matchs de Dota 2 (Mad Dogs League) et fournit des informations sur les paris 1xBet.\n\n"
        f"Commandes disponibles:\n"
        f"/matches - Voir les matchs en direct\n"
        f"/info - Informations sur le bot\n"
        f"/help - Aide"
    )

# Fonction d'aide
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envoie un message quand la commande /help est utilisée."""
    await update.message.reply_text(
        "Commandes disponibles:\n\n"
        "/matches - Affiche les matchs en direct de la Mad Dogs League\n"
        "/info - Affiche des informations sur le bot\n"
        "/help - Affiche ce message d'aide"
    )

# Fonction d'info
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envoie un message avec des informations sur le bot."""
    await update.message.reply_text(
        "🎮 Dota 2 Match Tracker Bot 🎮\n\n"
        "Ce bot surveille les matchs en direct de la Mad Dogs League (ID 17911) et récupère les informations de paris de 1xBet.\n\n"
        "Fonctionnalités:\n"
        "- Surveillance des matchs en direct\n"
        "- Score et durée des matchs\n"
        "- Net Worth et avantage d'or\n"
        "- Seuils de paris (Total Kills) de 1xBet\n"
        "- Alertes spéciales pour moins de 10 kills à 10 minutes\n"
        "- Suivi du joueur Hellfire dans les matchs spéciaux\n\n"
        "Configuration:\n"
        f"- Rafraîchissement sans match: Toutes les {NO_MATCH_CHECK_INTERVAL//60} minutes\n"
        f"- Rafraîchissement avec match: Toutes les {MATCH_CHECK_INTERVAL_MIN}-{MATCH_CHECK_INTERVAL_MAX} secondes\n"
    )

# Fonction pour formater un match en texte pour Telegram
def format_match_for_telegram(match):
    """Formate les données d'un match pour l'affichage dans Telegram."""
    radiant_name = match["radiant"]["team_name"]
    dire_name = match["dire"]["team_name"]
    match_id = match["match_id"]
    league_name = match.get("league_name", "Unknown League")
    duration = match["duration"]
    radiant_score = match["radiant_score"]
    dire_score = match["dire_score"]
    total_kills = match["total_kills"]
    
    message = f"🎮 *Match ID: {match_id}*\n"
    message += f"🏆 *League: {league_name}*\n"
    message += f"⚔️ *{radiant_name}* vs *{dire_name}*\n"
    message += f"⏱️ Durée: {duration}\n"
    message += f"🔴 {radiant_name}: {radiant_score} kills\n"
    message += f"🔵 {dire_name}: {dire_score} kills\n"
    message += f"📊 Total: {total_kills} kills\n\n"
    
    # Ajouter les informations de paris
    if match["betting"]["kill_threshold"]:
        message += f"💰 *Seuil Total Kills (1xBet)*: {match['betting']['kill_threshold']}\n"
        if match["betting"]["match_url"]:
            message += f"🔗 [Voir sur 1xBet]({match['betting']['match_url']})\n\n"
    else:
        message += "💰 Informations de paris non disponibles\n\n"
    
    # Net worth
    radiant_nw = match["radiant"]["total_net_worth"]
    dire_nw = match["dire"]["total_net_worth"]
    nw_diff = match["net_worth_difference"]
    
    message += f"💲 *Net Worth*:\n"
    message += f"🔴 {radiant_name}: {radiant_nw} or\n"
    message += f"🔵 {dire_name}: {dire_nw} or\n"
    
    if nw_diff > 0:
        message += f"📈 {radiant_name} a un avantage de {nw_diff} or\n\n"
    elif nw_diff < 0:
        message += f"📈 {dire_name} a un avantage de {abs(nw_diff)} or\n\n"
    else:
        message += f"📊 Net Worth égal\n\n"
    
    # Section Alertes
    message += f"🚨 *Alertes*:\n"
    
    # Alerte faible nombre de kills
    if match["alerts"]["low_kill_alert"]:
        message += f"⚠️ *ALERTE: Moins de 10 kills à la 10ème minute!*\n"
    
    # Match spécial
    if match["alerts"]["special_matchup"]:
        message += f"🌟 *Match spécial: Monlight Wispers vs Project Achilles!*\n"
        if match["hellfire"]["playing"]:
            hellfire_team = match["hellfire"]["team"]
            hellfire_nw = match["hellfire"]["net_worth"]
            message += f"🔥 Hellfire joue pour {hellfire_team}, Net Worth: {hellfire_nw} or\n"
    
    if not match["alerts"]["low_kill_alert"] and not match["alerts"]["special_matchup"]:
        message += "Aucune alerte active\n"
    
    message += "\n"
    
    return message

# Fonction pour afficher les matchs en direct
async def matches_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Affiche les matchs en direct."""
    await update.message.reply_text("Recherche des matchs en direct en cours... ⏳")
    
    # Récupération des matchs en direct
    matches = get_live_matches()
    
    if not matches:
        await update.message.reply_text("Aucun match en direct trouvé. 😔")
        return
    
    await update.message.reply_text(f"*{len(matches)} match(s) en direct trouvé(s)*:", parse_mode="Markdown")
    
    # Envoi des informations pour chaque match
    for match in matches:
        formatted_message = format_match_for_telegram(match)
        await update.message.reply_text(formatted_message, parse_mode="Markdown", disable_web_page_preview=True)

# Fonction principale
def main() -> None:
    """Démarrage du bot."""
    # Vérification du token Telegram
    if not BOT_TOKEN:
        logger.error("⚠️ ERREUR: Token Telegram non configuré!")
        logger.error("Pour configurer le token, exécutez: export TELEGRAM_BOT_TOKEN=votre_token")
        logger.error("Vous pouvez obtenir un token en parlant à @BotFather sur Telegram")
        return
    
    try:
        # Création de l'application
        application = Application.builder().token(BOT_TOKEN).build()

        # Ajout des gestionnaires de commandes
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("info", info))
        application.add_handler(CommandHandler("matches", matches_command))

        # Démarrage du bot
        logger.info("Démarrage du bot Telegram...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot: {e}")

if __name__ == "__main__":
    main()
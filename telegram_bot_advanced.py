import logging
import asyncio
import time
from typing import Dict, List, Set, Optional
try:
    from telegram import Update, Bot
    from telegram.ext import Application, CommandHandler, ContextTypes
except ImportError:
    from python_telegram_bot import Update, Bot
    from python_telegram_bot.ext import Application, CommandHandler, ContextTypes
import html
from dota_service import get_live_matches, format_duration
from config import (
    TELEGRAM_BOT_TOKEN, 
    CHECK_INTERVAL, 
    NO_MATCH_CHECK_INTERVAL, 
    MATCH_CHECK_INTERVAL_MIN, 
    MATCH_CHECK_INTERVAL_MAX
)

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Token du bot Telegram (à partir du fichier de configuration)
BOT_TOKEN = TELEGRAM_BOT_TOKEN

# Variables globales pour suivre les utilisateurs et les matchs
subscribed_users: Set[int] = set()  # Ensemble des IDs des utilisateurs abonnés
known_matches: Dict[str, Dict] = {}  # Dictionnaire des matchs connus par ID
last_kill_thresholds: Dict[str, float] = {}  # Derniers seuils de kills connus par ID de match
notification_task = None  # Tâche asynchrone pour les notifications

# Fonction de démarrage du bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envoie un message quand la commande /start est utilisée."""
    user = update.effective_user
    await update.message.reply_html(
        f"Bonjour {html.escape(user.first_name)} 👋\n\n"
        f"Je suis un bot qui surveille les matchs de Dota 2 (Mad Dogs League) et fournit des informations sur les paris 1xBet.\n\n"
        f"Commandes disponibles:\n"
        f"/matches - Voir les matchs en direct\n"
        f"/subscribe - S'abonner aux notifications\n"
        f"/unsubscribe - Se désabonner des notifications\n"
        f"/info - Informations sur le bot\n"
        f"/help - Aide"
    )

# Fonction d'aide
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envoie un message quand la commande /help est utilisée."""
    await update.message.reply_text(
        "Commandes disponibles:\n\n"
        "/matches - Affiche les matchs en direct de la Mad Dogs League\n"
        "/subscribe - S'abonne aux notifications automatiques\n"
        "/unsubscribe - Se désabonne des notifications automatiques\n"
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
        "- Suivi du joueur Hellfire dans les matchs spéciaux\n"
        "- Notifications automatiques pour les abonnés\n\n"
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
    duration = match["duration"]
    radiant_score = match["radiant_score"]
    dire_score = match["dire_score"]
    total_kills = match["total_kills"]
    
    message = f"🎮 *Match ID: {match_id}*\n"
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
    
    # Alertes
    if match["alerts"]["low_kill_alert"]:
        message += f"⚠️ *ALERTE: Moins de 10 kills à la 10ème minute!*\n\n"
    
    # Match spécial
    if match["alerts"]["special_matchup"]:
        message += f"🌟 *Match spécial: Monlight Wispers vs Project Achilles!*\n"
        if match["hellfire"]["playing"]:
            hellfire_team = match["hellfire"]["team"]
            hellfire_nw = match["hellfire"]["net_worth"]
            message += f"🔥 Hellfire joue pour {hellfire_team}, Net Worth: {hellfire_nw} or\n\n"
    
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

# Fonction pour s'abonner aux notifications
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Abonne un utilisateur aux notifications."""
    user_id = update.effective_user.id
    
    if user_id in subscribed_users:
        await update.message.reply_text("Vous êtes déjà abonné aux notifications. 👍")
        return
    
    subscribed_users.add(user_id)
    await update.message.reply_text(
        "✅ Vous êtes maintenant abonné aux notifications!\n\n"
        "Vous recevrez des alertes pour:\n"
        "- Nouveaux matchs en direct\n"
        "- Changements de seuil de kills sur 1xBet\n"
        "- Alertes spéciales (moins de 10 kills à 10 minutes)\n"
        "- Présence du joueur Hellfire dans les matchs spéciaux\n\n"
        "Utilisez /unsubscribe pour vous désabonner."
    )
    
    # Démarrer la tâche de notification si c'est le premier abonné
    if len(subscribed_users) == 1:
        ensure_notification_task_running(context)
        
    logger.info(f"User {user_id} subscribed to notifications. Total subscribers: {len(subscribed_users)}")

# Fonction pour se désabonner des notifications
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Désabonne un utilisateur des notifications."""
    user_id = update.effective_user.id
    
    if user_id not in subscribed_users:
        await update.message.reply_text("Vous n'êtes pas abonné aux notifications. 🤔")
        return
    
    subscribed_users.remove(user_id)
    await update.message.reply_text("❌ Vous êtes maintenant désabonné des notifications.")
    
    logger.info(f"User {user_id} unsubscribed from notifications. Total subscribers: {len(subscribed_users)}")

# S'assurer que la tâche de notification est en cours d'exécution
def ensure_notification_task_running(context: ContextTypes.DEFAULT_TYPE) -> None:
    """S'assure que la tâche de notification est en cours d'exécution."""
    global notification_task
    
    if notification_task is None or notification_task.done():
        notification_task = asyncio.create_task(notification_loop(context.bot))
        logger.info("Notification task started")

# Boucle de notification
async def notification_loop(bot: Bot) -> None:
    """Boucle principale pour vérifier les matchs et envoyer des notifications."""
    global known_matches, last_kill_thresholds
    
    while subscribed_users:  # Continue tant qu'il y a des utilisateurs abonnés
        try:
            # Récupération des matchs en direct
            matches = get_live_matches()
            current_match_ids = set()
            
            if matches:
                for match in matches:
                    match_id = str(match["match_id"])
                    current_match_ids.add(match_id)
                    
                    # Vérifier s'il s'agit d'un nouveau match
                    if match_id not in known_matches:
                        # Nouveau match trouvé
                        known_matches[match_id] = match
                        radiant_name = match["radiant"]["team_name"]
                        dire_name = match["dire"]["team_name"]
                        notification_msg = (
                            f"🚨 *Nouveau match en direct!*\n"
                            f"⚔️ *{radiant_name}* vs *{dire_name}*\n\n"
                            f"Utilisez /matches pour voir les détails"
                        )
                        await send_notification_to_all(bot, notification_msg)
                        
                        # Enregistrer le seuil de kills initial
                        if match["betting"]["kill_threshold"]:
                            last_kill_thresholds[match_id] = match["betting"]["kill_threshold"]
                    
                    else:
                        # Match existant - vérifier les changements
                        old_match = known_matches[match_id]
                        
                        # Vérifier si le seuil de kills a changé
                        if (match["betting"]["kill_threshold"] and 
                            match_id in last_kill_thresholds and 
                            match["betting"]["kill_threshold"] != last_kill_thresholds[match_id]):
                            
                            radiant_name = match["radiant"]["team_name"]
                            dire_name = match["dire"]["team_name"]
                            old_threshold = last_kill_thresholds[match_id]
                            new_threshold = match["betting"]["kill_threshold"]
                            
                            notification_msg = (
                                f"📊 *Changement de seuil de kills sur 1xBet!*\n"
                                f"⚔️ *{radiant_name}* vs *{dire_name}*\n"
                                f"Le seuil est passé de {old_threshold} à {new_threshold}\n\n"
                                f"Utilisez /matches pour voir les détails"
                            )
                            await send_notification_to_all(bot, notification_msg)
                            
                            # Mettre à jour le seuil connu
                            last_kill_thresholds[match_id] = new_threshold
                        
                        # Vérifier si l'alerte de faible nombre de kills vient d'être déclenchée
                        if match["alerts"]["low_kill_alert"] and not old_match["alerts"]["low_kill_alert"]:
                            radiant_name = match["radiant"]["team_name"]
                            dire_name = match["dire"]["team_name"]
                            notification_msg = (
                                f"⚠️ *ALERTE: Moins de 10 kills à 10 minutes!*\n"
                                f"⚔️ *{radiant_name}* vs *{dire_name}*\n"
                                f"Total des kills: {match['total_kills']}\n\n"
                                f"Utilisez /matches pour voir les détails"
                            )
                            await send_notification_to_all(bot, notification_msg)
                        
                        # Mettre à jour le match connu
                        known_matches[match_id] = match
            
            # Nettoyer les matchs qui ne sont plus en direct
            for match_id in list(known_matches.keys()):
                if match_id not in current_match_ids:
                    ended_match = known_matches[match_id]
                    radiant_name = ended_match["radiant"]["team_name"]
                    dire_name = ended_match["dire"]["team_name"]
                    
                    notification_msg = (
                        f"🏁 *Match terminé!*\n"
                        f"⚔️ *{radiant_name}* ({ended_match['radiant_score']}) vs "
                        f"*{dire_name}* ({ended_match['dire_score']})\n"
                        f"📊 Total des kills: {ended_match['total_kills']}\n\n"
                    )
                    
                    # Ajouter des informations sur le seuil de kills et le résultat du pari
                    if match_id in last_kill_thresholds:
                        threshold = last_kill_thresholds[match_id]
                        total_kills = ended_match['total_kills']
                        
                        notification_msg += (
                            f"💰 *Résultat du pari sur le total de kills:*\n"
                            f"Seuil: {threshold} | Réel: {total_kills}\n"
                            f"Résultat: {'Plus' if total_kills > threshold else 'Moins'} que le seuil\n\n"
                        )
                        
                        # Supprimer du dictionnaire des seuils
                        del last_kill_thresholds[match_id]
                    
                    await send_notification_to_all(bot, notification_msg)
                    
                    # Supprimer le match terminé
                    del known_matches[match_id]
            
            # Déterminer l'intervalle de vérification en fonction de la présence de matchs
            if matches:
                # Match en cours, intervalle plus court et variable pour éviter les patterns
                import random
                sleep_time = random.randint(MATCH_CHECK_INTERVAL_MIN, MATCH_CHECK_INTERVAL_MAX)
                logger.info(f"Matchs en cours, prochaine vérification dans {sleep_time} secondes")
            else:
                # Pas de match, intervalle plus long
                sleep_time = NO_MATCH_CHECK_INTERVAL
                logger.info(f"Aucun match en cours, prochaine vérification dans {sleep_time // 60} minutes")
            
            # Attendre avant la prochaine vérification
            await asyncio.sleep(sleep_time)
        
        except Exception as e:
            logger.error(f"Error in notification loop: {e}")
            await asyncio.sleep(60)  # Attendre plus longtemps en cas d'erreur

# Envoyer une notification à tous les utilisateurs abonnés
async def send_notification_to_all(bot: Bot, message: str) -> None:
    """Envoie une notification à tous les utilisateurs abonnés."""
    for user_id in subscribed_users.copy():  # Copie pour éviter les erreurs de modification pendant l'itération
        try:
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")
            # Optionnel: désabonner l'utilisateur si le bot ne peut pas lui envoyer de messages
            # subscribed_users.remove(user_id)

# Fonction principale
def main() -> None:
    """Démarrage du bot."""
    # Création de l'application
    application = Application.builder().token(BOT_TOKEN).build()

    # Ajout des gestionnaires de commandes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("matches", matches_command))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Démarrage du bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
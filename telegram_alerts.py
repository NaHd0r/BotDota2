"""
Module pour envoyer des alertes Telegram.
Fonctions simples pour envoyer des messages au bot Telegram configuré.
"""

import logging
import requests
import os
from config import AlertConfig, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Configuration du logging
logger = logging.getLogger(__name__)

def send_telegram_message(message: str) -> bool:
    """
    Envoie un message Telegram.
    
    Args:
        message: Le message à envoyer (supporte le Markdown)
        
    Returns:
        True si l'envoi a réussi, False sinon
    """
    # Vérifier si les notifications Telegram sont activées
    if not AlertConfig.TELEGRAM_NOTIFICATIONS_ENABLED:
        logger.info("Notifications Telegram désactivées - Message non envoyé")
        return False
    
    # Vérifier si le token est configuré
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Token Telegram non configuré dans les variables d'environnement")
        return False
    
    try:
        response = requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            json={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown'
            },
            timeout=10
        )
        
        result = response.json()
        if result.get('ok'):
            logger.info(f"Message Telegram envoyé avec succès, message_id: {result.get('result', {}).get('message_id')}")
            return True
        else:
            logger.error(f"Échec de l'envoi du message Telegram: {result.get('description')}")
            return False
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message Telegram: {e}")
        return False

def send_alert_to_telegram(match, alert):
    """
    Envoie une alerte Telegram basée sur le format d'alerte existant.
    
    Args:
        match: Données du match
        alert: Données de l'alerte
        
    Returns:
        True si l'envoi a réussi, False sinon
    """
    try:
        # Extraire le type et le message de l'alerte
        alert_type = alert.get('type', 'unknown')
        alert_message = alert.get('message', 'Alerte inconnue')
        severity = alert.get('severity', 'info')
        
        # Extraire les données du match
        match_id = match.get('match_id', 'Unknown')
        radiant_team = match.get('radiant', {})
        dire_team = match.get('dire', {})
        radiant_name = radiant_team.get('team_name', 'Radiant')
        dire_name = dire_team.get('team_name', 'Dire')
        
        # Scores
        radiant_score = match.get('radiant_score', 0)
        dire_score = match.get('dire_score', 0)
        total_kills = radiant_score + dire_score
        
        # Durée
        duration = match.get('duration', '0:00')
        
        # Emoji pour le type d'alerte
        emoji = "ℹ️"  # Par défaut
        if severity == 'warning':
            emoji = "⚠️"
        elif severity == 'error':
            emoji = "🚨"
        
        # Emojis spécifiques selon le type d'alerte
        if alert_type == 'few_kills':
            emoji = "😴"
        elif alert_type == 'many_kills':
            emoji = "🔥"
        elif alert_type == 'kill_difference':
            emoji = "⚔️"
        elif alert_type == 'networth_difference':
            emoji = "💰"
        elif alert_type == 'kills_17min':
            emoji = "🎯"
        
        # Construire le message
        message = f"{emoji} *ALERTE: {alert_message}*\n\n"
        message += f"⚔️ *{radiant_name}* vs *{dire_name}*\n"
        message += f"⏱️ Durée: {duration}\n"
        message += f"🔴 {radiant_name}: {radiant_score} kills\n"
        message += f"🔵 {dire_name}: {dire_score} kills\n"
        message += f"📊 Total: {total_kills} kills\n\n"
        
        # Ajouter les informations de paris si disponibles
        betting_info = match.get('betting', {})
        if betting_info and betting_info.get('kill_threshold'):
            message += f"💰 *Seuil Total Kills (1xBet)*: {betting_info.get('kill_threshold')}\n\n"
        
        # Envoyer le message
        return send_telegram_message(message)
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'alerte Telegram: {e}")
        return False

def send_new_series_alert(series_data):
    """
    Envoie une notification pour une nouvelle série.
    
    Args:
        series_data: Données de la série
        
    Returns:
        True si l'envoi a réussi, False sinon
    """
    try:
        # Extraire les informations nécessaires
        series_id = series_data.get('series_id', 'Unknown')
        team1_name = series_data.get('team1_name', 'Unknown Team 1')
        team2_name = series_data.get('team2_name', 'Unknown Team 2')
        league_id = str(series_data.get('league_id', ''))
        from config import LEAGUE_NAMES
        league_name = LEAGUE_NAMES.get(league_id, 'Unknown League')
        
        # Créer le message
        message = f"🚀 *Nouvelle série en direct!*\n\n"
        message += f"🏆 *Ligue*: {league_name}\n"
        message += f"⚔️ *{team1_name}* vs *{team2_name}*\n\n"
        message += f"🎯 *Série ID*: {series_id}\n"
        message += f"👉 Surveillez les détails des matchs à venir dans cette série!"
        
        # Envoyer le message
        return send_telegram_message(message)
    except Exception as e:
        logger.error(f"Erreur lors de la création de la notification de nouvelle série: {e}")
        return False
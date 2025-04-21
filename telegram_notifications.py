"""
Module de notifications Telegram pour Dota 2 Dashboard.
Ce module gère l'envoi de notifications via Telegram pour les événements importants.
"""

import os
import logging
import requests
from typing import Dict, Any, Optional

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Récupération du token depuis les variables d'environnement
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = 840765051  # Chat ID du destinataire des notifications

def send_telegram_message(message: str) -> bool:
    """
    Envoie un message via l'API Telegram.
    
    Args:
        message: Texte du message à envoyer (supporte le Markdown)
        
    Returns:
        True si l'envoi a réussi, False sinon
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Token Telegram non configuré. Impossible d'envoyer la notification.")
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

def notify_series_started(series_data: Dict[str, Any]) -> None:
    """
    Envoie une notification quand une nouvelle série débute.
    
    Args:
        series_data: Données de la série qui vient de débuter
    """
    try:
        # Extracting data
        series_id = series_data.get('series_id', 'Unknown')
        team1_name = series_data.get('team1_name', 'Unknown Team 1')
        team2_name = series_data.get('team2_name', 'Unknown Team 2')
        league_name = series_data.get('league_name', 'Unknown League')
        
        # Creating the message
        message = f"🚀 *Nouvelle série en direct!*\n\n"
        message += f"🏆 *Ligue*: {league_name}\n"
        message += f"⚔️ *{team1_name}* vs *{team2_name}*\n\n"
        message += f"🎯 *Série ID*: {series_id}\n"
        message += f"👉 Surveillez les détails des matchs à venir dans cette série!"
        
        # Sending the notification
        send_telegram_message(message)
    except Exception as e:
        logger.error(f"Erreur lors de la création de la notification de début de série: {e}")

def notify_match_started(match_data: Dict[str, Any]) -> None:
    """
    Envoie une notification quand un nouveau match débute.
    
    Args:
        match_data: Données du match qui vient de débuter
    """
    try:
        # Extracting data
        match_id = match_data.get('match_id', 'Unknown')
        series_id = match_data.get('series_id', 'Unknown')
        radiant_name = match_data.get('radiant', {}).get('team_name', 'Unknown Radiant')
        dire_name = match_data.get('dire', {}).get('team_name', 'Unknown Dire')
        
        # Creating the message
        message = f"🎮 *Nouveau match en direct!*\n\n"
        message += f"⚔️ *{radiant_name}* vs *{dire_name}*\n"
        message += f"🎯 *Match ID*: {match_id}\n"
        message += f"📊 *Série ID*: {series_id}\n\n"
        
        # Add betting info if available
        if match_data.get('betting', {}).get('kill_threshold'):
            kill_threshold = match_data['betting']['kill_threshold']
            message += f"💰 *Seuil Total Kills (1xBet)*: {kill_threshold}\n"
        
        # Sending the notification
        send_telegram_message(message)
    except Exception as e:
        logger.error(f"Erreur lors de la création de la notification de début de match: {e}")

def notify_kill_threshold_alert(match_data: Dict[str, Any], time: int, threshold: int) -> None:
    """
    Envoie une alerte quand le nombre de kills est inférieur à un seuil à un temps donné.
    
    Args:
        match_data: Données du match
        time: Temps en minutes
        threshold: Seuil de kills attendu
    """
    try:
        # Extracting data
        match_id = match_data.get('match_id', 'Unknown')
        radiant_name = match_data.get('radiant', {}).get('team_name', 'Unknown Radiant')
        dire_name = match_data.get('dire', {}).get('team_name', 'Unknown Dire')
        total_kills = match_data.get('total_kills', 0)
        
        # Creating the message
        message = f"🚨 *ALERTE: Moins de {threshold} kills à {time} minutes!*\n\n"
        message += f"⚔️ *{radiant_name}* vs *{dire_name}*\n"
        message += f"📊 Total des kills: {total_kills}\n"
        message += f"⏱️ Temps prévu: {time}:00\n\n"
        
        # Add betting info if available
        if match_data.get('betting', {}).get('kill_threshold'):
            kill_threshold = match_data['betting']['kill_threshold']
            message += f"💰 *Seuil Total Kills (1xBet)*: {kill_threshold}\n\n"
        
        message += f"Cette alerte est déclenchée car le nombre total de kills est significativement en dessous de la moyenne attendue à ce stade du match."
        
        # Sending the notification
        send_telegram_message(message)
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'alerte de seuil de kills: {e}")
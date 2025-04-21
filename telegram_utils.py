"""
Module utilitaire pour l'envoi de notifications Telegram.
Ce module fournit des fonctions partagées pour envoyer des alertes vers Telegram.
"""

import logging
import requests
import os
from typing import Dict, Any, Optional
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, AlertConfig

# Configuration du logging
logger = logging.getLogger(__name__)

def send_telegram_message(message: str) -> bool:
    """
    Envoie un message Telegram au canal configuré.
    
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
    
    # Vérifier si l'ID du chat est configuré
    if not TELEGRAM_CHAT_ID:
        logger.error("ID de chat Telegram non configuré")
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

def notify_new_series(series_data: Dict[str, Any]) -> bool:
    """
    Envoie une notification pour une nouvelle série.
    
    Args:
        series_data: Données de la série
        
    Returns:
        True si l'envoi a réussi, False sinon
    """
    # Vérifier si les notifications de nouvelles séries sont activées
    if not AlertConfig.NOTIFY_NEW_SERIES:
        logger.info("Notifications de nouvelles séries désactivées")
        return False
    
    try:
        # Extraire les informations nécessaires
        series_id = series_data.get('series_id', 'Unknown')
        team1_name = series_data.get('team1_name', 'Unknown Team 1')
        team2_name = series_data.get('team2_name', 'Unknown Team 2')
        league_id = str(series_data.get('league_id', ''))
        league_name = series_data.get('league_name', 'Unknown League')
        
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

def notify_match_alert(match_data: Dict[str, Any], alert_type: str, alert_message: str) -> bool:
    """
    Envoie une alerte concernant un match.
    
    Args:
        match_data: Données du match
        alert_type: Type d'alerte (ex: 'kill_difference', 'low_kills', 'networth_difference')
        alert_message: Message décrivant l'alerte
        
    Returns:
        True si l'envoi a réussi, False sinon
    """
    # Vérifier si les notifications d'alertes de seuil sont activées
    if not AlertConfig.NOTIFY_KILL_THRESHOLD:
        return False
    
    try:
        # Extraire les informations du match
        match_id = match_data.get('match_id', 'Unknown')
        radiant_name = match_data.get('radiant', {}).get('team_name', 'Radiant')
        dire_name = match_data.get('dire', {}).get('team_name', 'Dire')
        duration = match_data.get('duration', '0:00')
        radiant_score = match_data.get('radiant_score', 0)
        dire_score = match_data.get('dire_score', 0)
        total_kills = radiant_score + dire_score
        
        # Créer l'emoji approprié selon le type d'alerte
        emoji = "⚠️"
        if alert_type == 'kill_difference':
            emoji = "🔪"
        elif alert_type == 'networth_difference':
            emoji = "💰"
        elif alert_type == 'few_kills':
            emoji = "😴"
        elif alert_type == 'many_kills':
            emoji = "🔥"
        
        # Créer le message
        message = f"{emoji} *ALERTE: {alert_message}*\n\n"
        message += f"⚔️ *{radiant_name}* vs *{dire_name}*\n"
        message += f"⏱️ Durée: {duration}\n"
        message += f"🔴 {radiant_name}: {radiant_score} kills\n"
        message += f"🔵 {dire_name}: {dire_score} kills\n"
        message += f"📊 Total: {total_kills} kills\n\n"
        
        # Ajouter les informations de paris si disponibles
        if match_data.get('betting', {}).get('kill_threshold'):
            message += f"💰 *Seuil Total Kills (1xBet)*: {match_data['betting']['kill_threshold']}\n\n"
        
        # Envoyer le message
        return send_telegram_message(message)
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'alerte: {e}")
        return False

def notify_match_finished(match_data: Dict[str, Any]) -> bool:
    """
    Envoie une notification pour un match terminé.
    
    Args:
        match_data: Données du match
        
    Returns:
        True si l'envoi a réussi, False sinon
    """
    # Vérifier si les notifications de matchs terminés sont activées
    if not AlertConfig.NOTIFY_MATCH_FINISHED:
        return False
        
    try:
        # Extraire les informations du match
        match_id = match_data.get('match_id', 'Unknown')
        radiant_name = match_data.get('radiant', {}).get('team_name', 'Radiant')
        dire_name = match_data.get('dire', {}).get('team_name', 'Dire')
        radiant_score = match_data.get('radiant_score', 0)
        dire_score = match_data.get('dire_score', 0)
        total_kills = radiant_score + dire_score
        
        # Déterminer le vainqueur
        winner = "Inconnu"
        if match_data.get('radiant_win') is not None:
            winner = radiant_name if match_data['radiant_win'] else dire_name
        
        # Créer le message
        message = f"🏁 *Match terminé*\n\n"
        message += f"⚔️ *{radiant_name}* vs *{dire_name}*\n"
        message += f"🏆 Vainqueur: *{winner}*\n"
        message += f"📊 Score final: {radiant_score} - {dire_score}\n"
        message += f"📊 Total des kills: {total_kills}\n\n"
        
        # Ajouter les informations de paris si disponibles
        if match_data.get('betting', {}).get('kill_threshold'):
            threshold = match_data['betting']['kill_threshold']
            result = "Plus" if total_kills > threshold else "Moins"
            message += f"💰 *Résultat du pari sur le total de kills:*\n"
            message += f"Seuil: {threshold} | Réel: {total_kills}\n"
            message += f"Résultat: {result} que le seuil\n"
        
        # Envoyer le message
        return send_telegram_message(message)
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la notification de match terminé: {e}")
        return False
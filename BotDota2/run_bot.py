#!/usr/bin/env python3
import argparse
import logging
import os
from config import (
    TELEGRAM_BOT_TOKEN,
    NO_MATCH_CHECK_INTERVAL,
    MATCH_CHECK_INTERVAL_MIN,
    MATCH_CHECK_INTERVAL_MAX
)

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_telegram_token():
    """Vérifie si le token Telegram est configuré"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("⚠️ ERREUR: Token Telegram non configuré!")
        logger.error("Pour configurer le token, exécutez: export TELEGRAM_BOT_TOKEN=votre_token")
        logger.error("Vous pouvez obtenir un token en parlant à @BotFather sur Telegram")
        return False
    return True

def print_help():
    """Affiche l'aide du script"""
    logger.info("Usage:")
    logger.info("  python run_bot.py [simple|advanced]")
    logger.info("")
    logger.info("Arguments:")
    logger.info("  simple    - Lance la version simple du bot (commandes de base)")
    logger.info("  advanced  - Lance la version avancée du bot (avec notifications)")
    logger.info("")
    logger.info("Configuration:")
    logger.info(f"  - Taux de rafraîchissement sans match: Toutes les {NO_MATCH_CHECK_INTERVAL//60} minutes")
    logger.info(f"  - Taux de rafraîchissement avec match: Entre {MATCH_CHECK_INTERVAL_MIN} et {MATCH_CHECK_INTERVAL_MAX} secondes")
    logger.info("")
    logger.info("Si aucun argument n'est fourni, la version simple sera lancée.")

def run_simple_bot():
    """Lance la version simple du bot Telegram"""
    logger.info("🚀 Lancement du bot Telegram (version simple)...")
    try:
        from telegram_bot import main
        main()
    except ImportError as e:
        logger.error(f"Erreur d'importation: {e}")
        logger.error("Vérifiez que le module 'python-telegram-bot' est installé.")
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot: {e}")

def run_advanced_bot():
    """Lance la version avancée du bot Telegram"""
    logger.info("🚀 Lancement du bot Telegram (version avancée)...")
    try:
        from telegram_bot_advanced import main
        main()
    except ImportError as e:
        logger.error(f"Erreur d'importation: {e}")
        logger.error("Vérifiez que le module 'python-telegram-bot' est installé.")
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lance le bot Telegram pour suivre les matchs Dota 2")
    parser.add_argument("mode", nargs="?", choices=["simple", "advanced"], default="simple",
                        help="Mode de fonctionnement du bot (simple ou advanced)")
    args = parser.parse_args()
    
    # Vérifier si le token est configuré
    if not check_telegram_token():
        exit(1)
    
    # Afficher la valeur du token (les premiers et derniers caractères)
    token_length = len(TELEGRAM_BOT_TOKEN)
    visible_chars = 4
    masked_token = TELEGRAM_BOT_TOKEN[:visible_chars] + "*" * (token_length - 2*visible_chars) + TELEGRAM_BOT_TOKEN[-visible_chars:]
    logger.info(f"Token Telegram configuré: {masked_token}")
    
    # Lancer le bot selon le mode choisi
    if args.mode == "simple":
        run_simple_bot()
    elif args.mode == "advanced":
        run_advanced_bot()
    else:
        print_help()
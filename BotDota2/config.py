import os
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes pour Dota 2 API
STEAM_API_KEY = "6A5951358A6AE0B658B818C78DE30A4A"
BASE_URL_LIVE = "https://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v1/"

# Ligues à surveiller
LEAGUE_IDS = [17911, 17211]  # Mad Dogs League, Space League
LEAGUE_NAMES = {
    17911: "Mad Dogs League",
    17211: "Space League"
}

# Liste d'URLs alternatives pour 1xBet
ONEXBET_URLS = [
    # Singapour (SG)
    "https://1xbet.sg/en/live/esports/2431462-dota-2-mad-dogs-league",
    "https://1xsinga.com/en/live/esports/2431462-dota-2-mad-dogs-league",
    # Mexique (MX)
    "https://1xbet.mx/es/live/esports/2431462-dota-2-mad-dogs-league",
    # Autres régions
    "https://1xbet.info/en/live/esports/2431462-dota-2-mad-dogs-league",
    "https://1xbet.cm/en/live/esports/2431462-dota-2-mad-dogs-league",
    "https://1xbet.ke/en/live/esports/2431462-dota-2-mad-dogs-league",
    "https://1xbet.ng/en/live/esports/2431462-dota-2-mad-dogs-league",
    "https://1xbet.gh/en/live/esports/2431462-dota-2-mad-dogs-league",
    "https://1xbet.com/en/live/esports/2431462-dota-2-mad-dogs-league"
]
# URL par défaut (on commence par Singapour)
ONEXBET_TOURNAMENT_URL = ONEXBET_URLS[0]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "*/*"
}

# Mapping des équipes
TEAMS = {
    9245832: "Prime Legion",
    9245833: "Project Achilles",
    9339710: "Dark Templars",
    8969891: "Stormriders",
    9339714: "Immortal Squad",
    8969895: "Peacekeepers Team",
    9245835: "Monlight Wispers",
    8969893: "Hellspawn",
    9086888: "Azure Dragons",
    8969887: "Freedom Fighters Team",
    # Autres équipes connues
    8255888: "Heroic",
    9247354: "Entity"
}

# ID du joueur Hellfire
HELLFIRE_ID = 1423256731

# Token du bot Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.warning("⚠️ TELEGRAM_BOT_TOKEN non défini dans les variables d'environnement")
    logger.warning("Le bot Telegram ne pourra pas fonctionner correctement")
    logger.warning("Utilisez 'export TELEGRAM_BOT_TOKEN=votre_token' pour définir le token")

# Configurations supplémentaires
# Intervalles de vérification des matchs
NO_MATCH_CHECK_INTERVAL = 300  # 5 minutes en secondes (quand pas de match en direct)
MATCH_CHECK_INTERVAL_MIN = 8    # Intervalle minimum quand des matchs sont en cours (secondes)
MATCH_CHECK_INTERVAL_MAX = 11   # Intervalle maximum quand des matchs sont en cours (secondes)
CHECK_INTERVAL = 30  # Intervalle par défaut (secondes)

# Configurations pour les alertes
LOW_KILL_ALERT_MIN = 600  # 10 minutes en secondes
LOW_KILL_ALERT_MAX = 660  # 11 minutes en secondes
LOW_KILL_THRESHOLD = 10   # Seuil d'alerte pour un faible nombre de kills
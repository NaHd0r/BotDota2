import os
import logging
import datetime
from flask import Flask, render_template, jsonify, request
from dota_service import get_live_matches, format_matches_for_display
from scraper import find_previous_matches, get_match_stats_from_dotabuff

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Jinja2 filter pour les horodatages
@app.template_filter('timestamp')
def _jinja2_filter_timestamp(timestamp):
    """Convertit un timestamp en chaîne"""
    return str(timestamp)

# Fonction context processor pour ajouter des variables globales au template
@app.context_processor
def inject_now():
    """Injecte l'heure actuelle dans tous les templates"""
    return {'now': datetime.datetime.now}

@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')

@app.route('/api/matches')
def matches():
    """API endpoint to get the latest match data"""
    try:
        matches = get_live_matches()
        
        # Log the raw match data for debugging
        for match in matches:
            logger.info("====== MATCH RAW DATA ======")
            logger.info(f"Match ID: {match.get('match_id')}")
            
            # Équipe Radiant
            radiant = match.get('radiant', {})
            logger.info(f"Radiant Team ID: {radiant.get('team_id')}")
            
            # Équipe Dire
            dire = match.get('dire', {})
            logger.info(f"Dire Team ID: {dire.get('team_id')}")
            
            # Score et durée
            logger.info(f"Radiant Score: {match.get('radiant_score', 0)}")
            logger.info(f"Dire Score: {match.get('dire_score', 0)}")
            logger.info(f"Duration: {match.get('duration', '0:00')}")
            logger.info(f"Total Kills: {match.get('total_kills', 0)}")
            logger.info("============================")
        
        return jsonify({
            'success': True,
            'matches': matches
        })
    except Exception as e:
        logger.error(f"Error fetching match data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/match-history')
def match_history():
    """API endpoint to get match history between two teams or by series ID"""
    try:
        # Vérifier si nous avons un ID de série
        series_id = request.args.get('series_id')
        
        if series_id:
            # Vérifier que l'ID de série est valide
            if not series_id.isdigit():
                logger.warning(f"Invalid series ID: {series_id}")
                return jsonify({
                    'success': False,
                    'error': f"ID de série invalide: {series_id}"
                }), 400
                
            # Si nous avons un ID de série, nous utilisons la fonction de recherche par série
            logger.info(f"Searching match history for series ID: {series_id}")
            
            try:
                # Importer la fonction get_matches_by_series_id si elle n'est pas déjà importée
                from scraper import get_matches_by_series_id
                
                # Récupérer les matchs de la série
                matches = get_matches_by_series_id(series_id, max_results=5)
                
                if not matches:
                    logger.warning(f"No matches found for series ID: {series_id}")
                    # Créer un match factice pour éviter les erreurs d'affichage
                    team_names = {
                        '9245832': 'Prime Legion',
                        '8969887': 'Freedom Fighters Team',
                        '8255888': 'BetBoom Team',
                        '9247354': 'Team Falcons'
                    }
                    
                    # Utiliser des valeurs par défaut pour les équipes pas encore connues
                    fallback_match = {
                        'match_id': series_id,
                        'date': datetime.datetime.now().strftime('%d/%m/%Y'),
                        'duration': "00:00",
                        'radiant_team': {'id': '0', 'name': "Équipe 1"},
                        'dire_team': {'id': '0', 'name': "Équipe 2"},
                        'radiant_score': 0,
                        'dire_score': 0,
                        'total_kills': 0,
                        'winner': 'unknown',
                        'match_type': "Série",
                        'series_id': series_id,
                        'game_number': 1,
                        'note': "Données de match non disponibles pour ce match"
                    }
                    
                    return jsonify({
                        'success': True,
                        'matches': [fallback_match],
                        'warning': "Aucun match trouvé pour cet ID de série. Affichage de données minimales."
                    })
                
                logger.info(f"Found {len(matches)} matches for series ID: {series_id}")
                
                # Convertir les objets datetime en chaînes pour la sérialisation JSON
                for match in matches:
                    if isinstance(match.get('date'), datetime.datetime):
                        match['date'] = match['date'].strftime('%d/%m/%Y')
                
                return jsonify({
                    'success': True,
                    'matches': matches
                })
            except Exception as e:
                logger.error(f"Error in get_matches_by_series_id: {str(e)}")
                # Retourner un message d'erreur plus clair pour le débogage
                return jsonify({
                    'success': False,
                    'error': f"Erreur lors de la récupération des matchs pour la série {series_id}: {str(e)}"
                }), 500
        else:
            # Sinon, nous utilisons la méthode standard de recherche par équipes
            # Récupérer les IDs des équipes depuis les paramètres de requête
            team1_id = request.args.get('team1')
            team2_id = request.args.get('team2')
            
            if not team1_id or not team2_id:
                return jsonify({
                    'success': False,
                    'error': 'Team IDs or Series ID are required'
                }), 400
            
            # Récupérer les noms des équipes depuis le service de base de données des équipes
            team_names = {
                '9245832': 'Prime Legion',
                '8969887': 'Freedom Fighters Team',
                '8255888': 'BetBoom Team',
                '9247354': 'Team Falcons'
            }
            
            team1_name = team_names.get(team1_id, f'Team {team1_id}')
            team2_name = team_names.get(team2_id, f'Team {team2_id}')
            
            logger.info(f"Searching match history between {team1_name} (ID: {team1_id}) and {team2_name} (ID: {team2_id})")
            
            # Récupérer les matchs précédents entre ces équipes en utilisant notre fonction améliorée
            # qui retourne directement les informations complètes des matchs
            from scraper import find_previous_matches
            matches = find_previous_matches(team1_id, team2_id, max_results=5)
            
            if not matches:
                logger.warning(f"No match history found between {team1_name} and {team2_name}")
                return jsonify({
                    'success': True,
                    'matches': []
                })
            
            logger.info(f"Found {len(matches)} previous matches between {team1_name} and {team2_name}")
            
            # Convertir les objets datetime en chaînes pour la sérialisation JSON
            for match in matches:
                if isinstance(match.get('date'), datetime.datetime):
                    match['date'] = match['date'].strftime('%d/%m/%Y')
            
            return jsonify({
                'success': True,
                'matches': matches
            })
    except Exception as e:
        logger.error(f"Error fetching match history: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

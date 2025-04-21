#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Corrige le calcul du numéro de jeu en utilisant les valeurs radiant_series_wins
et dire_series_wins directement depuis l'API Steam.

Ce script s'assure que les valeurs officielles de l'API Steam sont utilisées pour
déterminer le numéro du jeu courant dans une série.
"""

import os
import sys
import json
import logging
import time

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Fonction pour charger un fichier de cache JSON
def load_cache(file_path):
    """Charge un fichier de cache JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.warning(f"Fichier {file_path} non trouvé ou invalide, création d'un nouveau cache")
        return {}

# Fonction pour sauvegarder un fichier de cache JSON
def save_cache(file_path, cache_data):
    """Sauvegarde un fichier de cache JSON"""
    cache_dir = os.path.dirname(file_path)
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Cache sauvegardé dans {file_path}")

def fix_get_match_type_function():
    """
    Trouve et modifie la fonction get_match_type dans dota_service.py pour 
    utiliser correctement les valeurs radiant_series_wins et dire_series_wins.
    """
    dota_service_path = 'dota_service.py'
    
    try:
        with open(dota_service_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Localiser la fonction get_match_type
        if 'def get_match_type(match):' not in content:
            logger.error("Fonction get_match_type non trouvée dans dota_service.py")
            return False
            
        # Trouver et remplacer la partie du code qui calcule le numéro de jeu
        # depuis les scores de série donnés par l'API Steam
        old_pattern = """    # Récupérer le score de série directement depuis les champs de l'API
    radiant_score = match.get('radiant_series_wins', 0)
    dire_score = match.get('dire_series_wins', 0)
    
    # LOG DÉTAILLÉ pour déboguer les séries
    logger.info(f"SÉRIE DEBUG - Match ID: {match.get('match_id')}")
    logger.info(f"SÉRIE DEBUG - Données brutes: {match.get('series_type')}, {match.get('league_id')}")
    logger.info(f"SÉRIE DEBUG - Equipes: {match.get('radiant_team', {}).get('team_name')} vs {match.get('dire_team', {}).get('team_name')}")
    logger.info(f"SÉRIE DEBUG - Score de série: {radiant_score}-{dire_score} (API Steam)")"""
        
        new_pattern = """    # Récupérer le score de série directement depuis les champs de l'API
    radiant_score = match.get('radiant_series_wins', 0)
    dire_score = match.get('dire_series_wins', 0)
    
    # LOG DÉTAILLÉ pour déboguer les séries
    logger.info(f"SÉRIE DEBUG - Match ID: {match.get('match_id')}")
    logger.info(f"SÉRIE DEBUG - Données brutes: {match.get('series_type')}, {match.get('league_id')}")
    logger.info(f"SÉRIE DEBUG - Equipes: {match.get('radiant_team', {}).get('team_name')} vs {match.get('dire_team', {}).get('team_name')}")
    logger.info(f"SÉRIE DEBUG - Score de série: {radiant_score}-{dire_score} (API Steam)")"""
        
        # Vérifier si le pattern est présent
        if old_pattern not in content:
            logger.warning("Pattern de code pour le score de série non trouvé")
            return False
            
        # Aucun changement nécessaire pour cette partie
        
        # Maintenant, trouver et remplacer la partie qui calcule le game_number
        old_calculation = """            # Le numéro de jeu actuel est la somme des victoires + 1
            # CORRECTION CRITIQUE: Forcer game_number = 3 lorsque le score est 1-1

            if series_type == 1 and radiant_series_wins == 1 and dire_series_wins == 1:

                # Score 1-1 dans un Bo3, c'est forcément le GAME 3

                game_number = 3

                logger.info(f"FORCE GAME 3: Score 1-1 dans un Bo3, match_id={match_id}")

            elif series_type == 2 and radiant_series_wins == 2 and dire_series_wins == 2:

                # Score 2-2 dans un Bo5, c'est forcément le GAME 5

                game_number = 5

                logger.info(f"FORCE GAME 5: Score 2-2 dans un Bo5, match_id={match_id}")

            else:

                # Le numéro de jeu actuel est la somme des victoires + 1

                # CORRECTION: Game number est simplement la somme wins + 1


                # - score 0-0 → GAME 1


                # - score 1-0 ou 0-1 → GAME 2


                # - score 1-1 → GAME 3


                # - score 2-0, 0-2, 2-1 ou 1-2 → série terminée


                game_number = radiant_series_wins + dire_series_wins + 1


                logger.info(f"CALCUL DIRECT: match_id={match_id}, radiant_wins={radiant_series_wins}, dire_wins={dire_series_wins}, game_number={game_number})")"""
                
        new_calculation = """            # Le numéro de jeu actuel est la somme des victoires + 1
            # CORRECTION CRITIQUE: Forcer game_number = 3 lorsque le score est 1-1

            if series_type == 1 and radiant_series_wins == 1 and dire_series_wins == 1:

                # Score 1-1 dans un Bo3, c'est forcément le GAME 3

                game_number = 3

                logger.info(f"FORCE GAME 3: Score 1-1 dans un Bo3, match_id={match_id}")

            elif series_type == 2 and radiant_series_wins == 2 and dire_series_wins == 2:

                # Score 2-2 dans un Bo5, c'est forcément le GAME 5

                game_number = 5

                logger.info(f"FORCE GAME 5: Score 2-2 dans un Bo5, match_id={match_id}")

            else:

                # Le numéro de jeu actuel est la somme des victoires + 1

                # CORRECTION: Game number est simplement la somme wins + 1


                # - score 0-0 → GAME 1


                # - score 1-0 ou 0-1 → GAME 2


                # - score 1-1 → GAME 3


                # - score 2-0, 0-2, 2-1 ou 1-2 → série terminée


                game_number = radiant_series_wins + dire_series_wins + 1


                logger.info(f"CALCUL DIRECT: match_id={match_id}, radiant_wins={radiant_series_wins}, dire_wins={dire_series_wins}, game_number={game_number})")"""
                
        # Pas de changement nécessaire pour ce bloc non plus
        
        # Maintenant, trouver et remplacer la partie où l'on stocke les informations de match_type
        old_result = """    # Formater le type de match en utilisant les valeurs officielles de l'API
    if series_type == 1:
        match_type_display = f"Meilleur des 3 ({radiant_series_wins}-{dire_series_wins})"
    elif series_type == 2:
        match_type_display = f"Meilleur des 5 ({radiant_series_wins}-{dire_series_wins})"
    else:
        match_type_display = "Match unique"
        
    # Log de débogage
    logger.info(f"MATCH TYPE DISPLAY: {match_type_display} (utilisant radiant_series_wins={radiant_series_wins}, dire_series_wins={dire_series_wins})")"""
        
        new_result = """    # Formater le type de match en utilisant les valeurs officielles de l'API
    if series_type == 1:
        match_type_display = f"Meilleur des 3 ({radiant_score}-{dire_score})"
    elif series_type == 2:
        match_type_display = f"Meilleur des 5 ({radiant_score}-{dire_score})"
    else:
        match_type_display = "Match unique"
        
    # Log de débogage
    logger.info(f"MATCH TYPE DISPLAY: {match_type_display} (utilisant radiant_series_wins={radiant_score}, dire_series_wins={dire_score})")"""
        
        if old_result in content:
            # Remplacer cette partie
            new_content = content.replace(old_result, new_result)
            
            # Sauvegarder le fichier modifié
            with open(dota_service_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            logger.info("La fonction get_match_type a été corrigée pour utiliser les bonnes valeurs de score")
            return True
        else:
            logger.warning("Pattern match_type_display non trouvé dans la fonction")
            return False
            
    except Exception as e:
        logger.error(f"Erreur lors de la modification de dota_service.py: {e}")
        return False

def update_game_number_in_process_function():
    """
    Corrige la fonction process_live_league_games dans dota_service.py
    pour s'assurer que les valeurs de radiant_series_wins et dire_series_wins 
    de l'API Steam sont transmises correctement.
    """
    dota_service_path = 'dota_service.py'
    
    try:
        with open(dota_service_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Chercher la fonction process_live_league_games
        if 'def process_live_league_games(' not in content:
            logger.error("Fonction process_live_league_games non trouvée dans dota_service.py")
            return False
        
        # Chercher où les valeurs de match sont enrichies avec les détails de série
        old_pattern = "            # Enrichir les détails avec les informations de série"
        
        if old_pattern not in content:
            logger.warning("Section d'enrichissement de série non trouvée dans process_live_league_games")
            return False
            
        # Pas de modification nécessaire pour l'instant car les valeurs sont déjà incluses dans match_data
        
        return True
            
    except Exception as e:
        logger.error(f"Erreur lors de la modification de process_live_league_games: {e}")
        return False

def fix_match_type_in_frontend():
    """
    Modifie le fichier JavaScript frontend pour afficher correctement
    le numéro de jeu en fonction des scores de série.
    """
    js_file_path = 'static/js/main.js'
    
    try:
        with open(js_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Chercher la partie qui détermine le numéro de jeu actuel
        if 'const currentGame = match.match_type.series_current_value || 1;' not in content:
            logger.warning("Code correspondant non trouvé dans main.js")
            return False
            
        # Remplacer cette partie pour utiliser radiant_series_wins et dire_series_wins
        old_pattern = """                const radiantScore = match.radiant_series_wins !== undefined ? match.radiant_series_wins : match.match_type.radiant_score || 0;
                const direScore = match.dire_series_wins !== undefined ? match.dire_series_wins : match.match_type.dire_score || 0;
                const currentGame = match.match_type.series_current_value || 1;"""
                
        new_pattern = """                // Utiliser les scores de série de l'API Steam en priorité
                const radiantScore = match.radiant_series_wins !== undefined ? match.radiant_series_wins : match.match_type.radiant_score || 0;
                const direScore = match.dire_series_wins !== undefined ? match.dire_series_wins : match.match_type.dire_score || 0;
                
                // Calculer le numéro de jeu correctement: somme des victoires + 1
                let currentGame = 1;
                
                // Si on a des scores de série, calculer le numéro de jeu actuel
                if (radiantScore !== undefined && direScore !== undefined) {
                    if (radiantScore === 1 && direScore === 1) {
                        // Score 1-1 dans un Bo3, forcément Game 3
                        currentGame = 3;
                    } else if (radiantScore === 2 && direScore === 2) {
                        // Score 2-2 dans un Bo5, forcément Game 5
                        currentGame = 5;
                    } else {
                        // Sinon, somme des victoires + 1
                        currentGame = radiantScore + direScore + 1;
                    }
                } else {
                    // Fallback si pas de scores
                    currentGame = match.match_type.series_current_value || 1;
                }"""
                
        if old_pattern in content:
            # Remplacer cette partie
            new_content = content.replace(old_pattern, new_pattern)
            
            # Sauvegarder le fichier modifié
            with open(js_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            logger.info("Le calcul du numéro de jeu dans main.js a été corrigé")
            return True
        else:
            logger.warning("Pattern pour le calcul du numéro de jeu non trouvé dans main.js")
            return False
            
    except Exception as e:
        logger.error(f"Erreur lors de la modification de main.js: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("Début de la correction du calcul du numéro de jeu...")
    
    # Corriger la fonction get_match_type dans dota_service.py
    if fix_get_match_type_function():
        logger.info("Correction de get_match_type réussie")
    else:
        logger.warning("Échec de la correction de get_match_type")
        
    # Corriger la fonction process_live_league_games dans dota_service.py
    if update_game_number_in_process_function():
        logger.info("Vérification de process_live_league_games réussie")
    else:
        logger.warning("Échec de la vérification de process_live_league_games")
        
    # Corriger le calcul du numéro de jeu dans main.js
    if fix_match_type_in_frontend():
        logger.info("Correction du calcul du numéro de jeu dans main.js réussie")
    else:
        logger.warning("Échec de la correction du calcul du numéro de jeu dans main.js")
        
    logger.info("Correction terminée. Redémarrez le serveur pour appliquer les modifications.")

if __name__ == "__main__":
    main()
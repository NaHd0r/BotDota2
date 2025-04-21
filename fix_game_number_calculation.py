"""
Script de correction pour le problème de numérotation des jeux dans les séries

Ce script corrige le problème où les valeurs radiant_series_wins et dire_series_wins de l'API Steam
sont perdues lors de la transformation des données.
"""

import json
import logging
import os

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_series_wins_to_processed_match(processed_match, raw_match):
    """
    Ajoute les valeurs radiant_series_wins et dire_series_wins directement depuis l'API Steam
    au match traité.
    
    Args:
        processed_match (dict): Le match déjà traité par le système
        raw_match (dict): Les données brutes du match depuis l'API Steam
        
    Returns:
        dict: Le match avec les valeurs ajoutées
    """
    # Si nous avons les valeurs dans les données brutes, les ajouter au match traité
    if 'radiant_series_wins' in raw_match:
        processed_match['radiant_series_wins'] = raw_match['radiant_series_wins']
        logger.info(f"Ajout de radiant_series_wins={raw_match['radiant_series_wins']} au match {processed_match['match_id']}")
    
    if 'dire_series_wins' in raw_match:
        processed_match['dire_series_wins'] = raw_match['dire_series_wins']
        logger.info(f"Ajout de dire_series_wins={raw_match['dire_series_wins']} au match {processed_match['match_id']}")
    
    # Mise à jour du numéro de jeu et de l'affichage en fonction des scores de série
    radiant_wins = processed_match.get('radiant_series_wins', 0)
    dire_wins = processed_match.get('dire_series_wins', 0)
    total_wins = radiant_wins + dire_wins
    game_number = total_wins + 1
    
    # Les séries BO3 peuvent aller jusqu'à 3 jeux, les BO5 jusqu'à 5
    max_games = 3 if processed_match.get('series_type', 0) == 1 else 5
    
    processed_match['game_display'] = f"GAME {game_number} SUR {max_games}"
    logger.info(f"Mise à jour du numéro de jeu: Game {game_number} sur {max_games} (radiant_wins={radiant_wins}, dire_wins={dire_wins})")
    
    # Mise à jour de l'affichage du type de match
    processed_match['match_type_display'] = f"Meilleur des {max_games} ({radiant_wins}-{dire_wins})"
    
    return processed_match

def patch_get_live_matches_function():
    """
    Modifie la fonction get_live_matches dans dota_service.py pour ajouter les valeurs de série
    """
    file_path = 'dota_service.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Rechercher l'endroit où ajouter notre code de correction
    target_line = "                # Ajouter le match traité à la liste"
    
    if target_line in content:
        # Code à insérer avant l'ajout du match à la liste
        patch_code = """                # Ajouter les valeurs radiant_series_wins et dire_series_wins directement depuis l'API Steam
                if 'radiant_series_wins' in match:
                    processed_match['radiant_series_wins'] = match['radiant_series_wins']
                    logger.info(f"[PATCH] Ajout de radiant_series_wins={match['radiant_series_wins']} au match {match_id}")
                    
                if 'dire_series_wins' in match:
                    processed_match['dire_series_wins'] = match['dire_series_wins']
                    logger.info(f"[PATCH] Ajout de dire_series_wins={match['dire_series_wins']} au match {match_id}")
                
                # Mise à jour du numéro de jeu basé sur les scores de série
                radiant_wins = processed_match.get('radiant_series_wins', 0)
                dire_wins = processed_match.get('dire_series_wins', 0)
                total_wins = radiant_wins + dire_wins
                game_number = total_wins + 1
                max_games = 3 if processed_match.get('series_type', 0) == 1 else 5
                
                # Mise à jour de l'affichage du jeu
                processed_match['game_display'] = f"GAME {game_number} SUR {max_games}"
                
                # Mise à jour de l'affichage du type de match pour inclure le score de série
                processed_match['match_type_display'] = f"Meilleur des {max_games} ({radiant_wins}-{dire_wins})"
                logger.info(f"[PATCH] Match {match_id}: Game {game_number}/{max_games}, Score série: {radiant_wins}-{dire_wins}")
"""
        
        # Remplacer la ligne cible par notre code suivi de la ligne cible
        new_content = content.replace(target_line, patch_code + "\n" + target_line)
        
        # Écrire le contenu modifié dans le fichier
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info(f"Fichier {file_path} modifié avec succès!")
        return True
    else:
        logger.error(f"Ligne cible non trouvée dans {file_path}")
        return False

def main():
    """Fonction principale pour appliquer les corrections"""
    logger.info("Application des corrections pour le problème de numérotation des jeux...")
    
    # Appliquer le patch à la fonction get_live_matches
    if patch_get_live_matches_function():
        logger.info("Correction appliquée avec succès!")
    else:
        logger.error("Échec de l'application de la correction.")

if __name__ == "__main__":
    main()
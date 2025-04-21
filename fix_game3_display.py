#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fix simple et direct pour forcer l'affichage de GAME 3 quand le score est 1-1.
Modifie directement la fonction get_match_type dans dota_service.py.
"""

import os
import sys
import subprocess
import time
import logging

# Config du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_match_type_calculation():
    try:
        # Tuer tous les serveurs gunicorn existants
        logger.info("Arrêt des serveurs gunicorn...")
        try:
            subprocess.run(['pkill', '-f', 'gunicorn.*main:app'], check=False)
            time.sleep(1)
            # Force kill si nécessaire
            subprocess.run(['pkill', '-9', '-f', 'gunicorn.*main:app'], check=False)
            time.sleep(1)
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du serveur: {e}")
        
        # Ajouter la correction dans dota_service.py
        logger.info("Modification de dota_service.py...")
        
        file_path = "dota_service.py"
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Chercher la fonction get_match_type
        target_function = "def get_match_type(match):"
        if target_function not in content:
            logger.error("Fonction get_match_type non trouvée!")
            return False
        
        # Chercher la section qui gère series_current_value
        if "series_current_value" in content and "radiant_series_wins + dire_series_wins + 1" in content:
            # Section trouvée, appliquer la correction
            logger.info("Section trouvée, application de la correction...")
            
            # Remplacer la section qui calcule game_number
            old_code = """            # Le numéro de jeu actuel est la somme des victoires + 1
            game_number = radiant_series_wins + dire_series_wins + 1"""
            
            new_code = """            # CORRECTION CRITIQUE: Forcer game_number = 3 lorsque le score est 1-1
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
                game_number = radiant_series_wins + dire_series_wins + 1"""
            
            # Appliquer le remplacement
            if old_code in content:
                modified_content = content.replace(old_code, new_code)
                with open(file_path, 'w') as f:
                    f.write(modified_content)
                logger.info("Correction appliquée avec succès!")
            else:
                logger.warning("Le code exact à remplacer n'a pas été trouvé, tentative générique...")
                
                # Tenter un remplacement plus générique
                import re
                pattern = r'(\s+)game_number\s*=\s*radiant_series_wins\s*\+\s*dire_series_wins\s*\+\s*1'
                match = re.search(pattern, content)
                
                if match:
                    indentation = match.group(1)
                    generic_new_code = f"""{indentation}# CORRECTION CRITIQUE: Forcer game_number = 3 lorsque le score est 1-1
{indentation}if series_type == 1 and radiant_series_wins == 1 and dire_series_wins == 1:
{indentation}    # Score 1-1 dans un Bo3, c'est forcément le GAME 3
{indentation}    game_number = 3
{indentation}    logger.info(f"FORCE GAME 3: Score 1-1 dans un Bo3, match_id={{match_id}}")
{indentation}elif series_type == 2 and radiant_series_wins == 2 and dire_series_wins == 2:
{indentation}    # Score 2-2 dans un Bo5, c'est forcément le GAME 5
{indentation}    game_number = 5
{indentation}    logger.info(f"FORCE GAME 5: Score 2-2 dans un Bo5, match_id={{match_id}}")
{indentation}else:
{indentation}    # Le numéro de jeu actuel est la somme des victoires + 1
{indentation}    game_number = radiant_series_wins + dire_series_wins + 1"""
                    
                    # Remplacer avec pattern regex
                    modified_content = re.sub(pattern, generic_new_code, content)
                    with open(file_path, 'w') as f:
                        f.write(modified_content)
                    logger.info("Correction générique appliquée avec succès!")
                else:
                    logger.error("Impossible de trouver le code à remplacer!")
                    return False
        else:
            logger.error("Section de calcul game_number non trouvée!")
            return False
        
        # Redémarrer le serveur
        logger.info("Redémarrage du serveur...")
        subprocess.Popen(["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--reload", "main:app"])
        logger.info("Serveur redémarré avec succès!")
        
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors de la correction: {e}")
        return False

if __name__ == "__main__":
    logger.info("Début de la correction GAME 3 SUR 3...")
    success = fix_match_type_calculation()
    if success:
        logger.info("Correction appliquée et serveur redémarré avec succès!")
    else:
        logger.error("Échec de la correction!")
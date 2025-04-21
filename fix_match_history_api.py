#!/usr/bin/env python3
"""
Script pour corriger l'API match_history d'app.py.

Ce script résout le problème où l'API /match-history ne renvoie pas tous les matchs
d'une série même lorsque ceux-ci sont correctement stockés dans le cache.
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chemins des fichiers
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_FILE = os.path.join(SCRIPT_DIR, "app.py")
BACKUP_FILE = os.path.join(SCRIPT_DIR, "app.py.bak")

def backup_file(file_path: str, backup_path: str) -> bool:
    """Crée une sauvegarde du fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as src:
            content = src.read()
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(content)
        logger.info(f"Sauvegarde créée: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la création de la sauvegarde: {e}")
        return False

def fix_match_history_function() -> bool:
    """Corrige la fonction match_history dans app.py"""
    try:
        # Créer une sauvegarde
        backup_file(APP_FILE, BACKUP_FILE)
        
        # Lire le contenu du fichier
        with open(APP_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Partie à remplacer: la première partie de la fonction match_history
        old_code = """@app.route('/api/match-history')
def match_history():
    """API endpoint to get match history between two teams or by series ID"""
    try:
        # Vérifier si un ID de série est fourni
        series_id = request.args.get('series_id')
        if series_id:
            # Récupérer les données de la série depuis le cache
            series_data = cache.get_series_from_historical_cache(series_id)
            if not series_data:
                # Si la série n'est pas dans le cache historique, vérifier le cache live
                series_data = cache.get_series_from_live_cache(series_id)
            
            if not series_data:
                return jsonify({'error': 'Série non trouvée'}), 404
            
            # Vérifier si nous avons des matchs précédents déjà formatés dans la série
            if 'previous_matches' in series_data and series_data['previous_matches'] and len(series_data['previous_matches']) > 0:
                matches = series_data['previous_matches']
                logger.info(f"Utilisation de {len(matches)} matchs précédents préformatés pour la série {series_id}")
                # S'assurer que les match_ids dans l'API correspondent à ceux dans previous_matches
                series_data["match_ids"] = [match["match_id"] for match in matches]"""
        
        # Nouveau code avec correction
        new_code = '''@app.route('/api/match-history')
def match_history():
    """API endpoint to get match history between two teams or by series ID"""'''
    try:
        # Vérifier si un ID de série est fourni
        series_id = request.args.get('series_id')
        if series_id:
            # Récupérer les données de la série depuis le cache
            series_data = cache.get_series_from_historical_cache(series_id)
            if not series_data:
                # Si la série n'est pas dans le cache historique, vérifier le cache live
                series_data = cache.get_series_from_live_cache(series_id)
            
            if not series_data:
                return jsonify({'error': 'Série non trouvée'}), 404
                
            # Afficher le contenu des previous_matches dans les logs pour debug
            if 'previous_matches' in series_data:
                logger.info(f"Série {series_id} a {len(series_data['previous_matches'])} matchs précédents")
                for i, match in enumerate(series_data['previous_matches']):
                    logger.info(f"  - Match #{i+1}: {match.get('match_id')} (Game {match.get('game_number')})")
            else:
                logger.info(f"Série {series_id} n'a pas de champ previous_matches")
            
            # Utiliser les matchs précédents s'ils existent déjà dans le cache
            if 'previous_matches' in series_data and series_data['previous_matches'] and len(series_data['previous_matches']) > 0:
                matches = series_data['previous_matches']
                logger.info(f"Utilisation de {len(matches)} matchs précédents préformatés pour la série {series_id}")
                # S'assurer que les match_ids dans l'API correspondent à ceux dans previous_matches
                series_data["match_ids"] = [match["match_id"] for match in matches]"""
        
        # Remplacer le code
        new_content = content.replace(old_code, new_code)
        
        # Partie à remplacer: la partie qui gère les previous_matches
        old_code_2 = """            # Pour s'assurer que l'API renvoie bien tous les matchs, on force l'utilisation des previous_matches
            if 'previous_matches' in series_data and len(series_data['previous_matches']) > 0:
                matches = series_data['previous_matches']"""
        
        new_code_2 = """            # Pour s'assurer que l'API renvoie bien tous les matchs, on force l'utilisation des previous_matches
            if 'previous_matches' in series_data and len(series_data['previous_matches']) > 0:
                logger.info(f"Force l'utilisation des {len(series_data['previous_matches'])} matchs précédents")
                matches = series_data['previous_matches'].copy()"""
        
        # Remplacer le second code
        new_content = new_content.replace(old_code_2, new_code_2)
        
        # Sauvegarder le fichier modifié
        with open(APP_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info(f"Fichier {APP_FILE} mis à jour avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du fichier: {e}")
        return False

def main():
    """Fonction principale"""
    print("===== Correction de l'API match_history =====")
    
    if fix_match_history_function():
        print("Correction terminée avec succès!")
    else:
        print("Échec de la correction!")
    
    print("\nRedémarrez le serveur pour appliquer les modifications.")

if __name__ == "__main__":
    main()
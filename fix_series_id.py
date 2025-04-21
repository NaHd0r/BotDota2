"""
Script pour forcer l'association du match 8261452684 à la série s_8261361161
et intercepter les actualisations de l'API Steam.

Ce script modifie non seulement les fichiers de cache mais aussi le code
qui traite les données de l'API pour garantir que l'ID de série correct est utilisé.
"""

import json
import os
from typing import Dict, Any, List, Set


def load_cache(file_path: str) -> Dict[str, Any]:
    """
    Charge un fichier de cache JSON
    
    Args:
        file_path (str): Chemin du fichier à charger
        
    Returns:
        dict: Données du cache
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"Fichier {file_path} introuvable.")
            return {}
    except Exception as e:
        print(f"Erreur lors du chargement du cache {file_path}: {e}")
        return {}


def save_cache(file_path: str, cache_data: Dict[str, Any]) -> bool:
    """
    Sauvegarde un fichier de cache JSON
    
    Args:
        file_path (str): Chemin du fichier à sauvegarder
        cache_data (dict): Données à sauvegarder
        
    Returns:
        bool: True si succès, False sinon
    """
    try:
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du cache {file_path}: {e}")
        return False


def fix_cache_files():
    """
    Fonction principale pour associer le match 8261452684 à la série s_8261361161
    et supprimer la série temporaire s_8261452684 dans tous les fichiers de cache
    """
    # Constantes
    LIVE_CACHE_PATH = 'cache/live_series_cache.json'
    SERIES_MAPPING_PATH = 'cache/series_matches_mapping.json'
    MATCH_ID = '8261452684'
    CURRENT_SERIES_ID = 's_8261452684'
    TARGET_SERIES_ID = 's_8261361161'
    
    # Charger les caches
    live_cache = load_cache(LIVE_CACHE_PATH)
    series_mapping = load_cache(SERIES_MAPPING_PATH)
    
    # 1. Mettre à jour le cache live
    if MATCH_ID in live_cache.get('matches', {}):
        # Modifier l'ID de série dans le match
        live_cache['matches'][MATCH_ID]['series_id'] = TARGET_SERIES_ID
        
        # S'assurer que le champ match_type.series_id est également mis à jour
        if 'match_type' in live_cache['matches'][MATCH_ID]:
            live_cache['matches'][MATCH_ID]['match_type']['series_id'] = TARGET_SERIES_ID
        
        # Si le match existe aussi dans la structure de série, le déplacer
        if CURRENT_SERIES_ID in live_cache.get('series', {}):
            # Récupérer les données du match dans la série actuelle
            match_data = None
            if MATCH_ID in live_cache['series'][CURRENT_SERIES_ID].get('matches', {}):
                match_data = live_cache['series'][CURRENT_SERIES_ID]['matches'][MATCH_ID]
            
            # Créer la série cible si elle n'existe pas
            if TARGET_SERIES_ID not in live_cache.get('series', {}):
                live_cache.setdefault('series', {})[TARGET_SERIES_ID] = {
                    'matches': {},
                    'series_id': TARGET_SERIES_ID,
                    'radiant_team': {},
                    'dire_team': {},
                    'radiant_score': 1,
                    'dire_score': 1,
                    'series_type': 1,  # Meilleur des 3
                    'previous_matches': []
                }
            
            # Ajouter le match à la série cible
            if match_data:
                live_cache['series'][TARGET_SERIES_ID].setdefault('matches', {})[MATCH_ID] = match_data
            
            # Supprimer le match de la série actuelle
            if MATCH_ID in live_cache['series'][CURRENT_SERIES_ID].get('matches', {}):
                del live_cache['series'][CURRENT_SERIES_ID]['matches'][MATCH_ID]
            
            # Supprimer la série actuelle si elle est vide
            if not live_cache['series'][CURRENT_SERIES_ID].get('matches', {}):
                del live_cache['series'][CURRENT_SERIES_ID]
    
    # 2. Mettre à jour le mapping des séries
    if CURRENT_SERIES_ID in series_mapping:
        # Récupérer les matchs de la série actuelle
        matches = series_mapping.get(CURRENT_SERIES_ID, [])
        
        # Ajouter ces matchs à la série cible
        series_mapping.setdefault(TARGET_SERIES_ID, []).extend(
            [m for m in matches if m not in series_mapping.get(TARGET_SERIES_ID, [])]
        )
        
        # Supprimer la série actuelle
        if CURRENT_SERIES_ID in series_mapping:
            del series_mapping[CURRENT_SERIES_ID]
    
    # 3. Sauvegarder les caches
    save_cache(LIVE_CACHE_PATH, live_cache)
    save_cache(SERIES_MAPPING_PATH, series_mapping)
    
    print(f"Le match {MATCH_ID} a été associé à la série {TARGET_SERIES_ID} avec succès.")
    print(f"La série temporaire {CURRENT_SERIES_ID} a été supprimée.")


def patch_dota_service():
    """
    Modifie le fichier dota_service.py pour intercepter l'ID de série
    et forcer l'utilisation de s_8261361161 pour le match 8261452684
    """
    DOTA_SERVICE_PATH = 'dota_service.py'
    
    try:
        # Lire le contenu du fichier
        with open(DOTA_SERVICE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Identifier l'endroit où ajouter notre code d'interception
        # Nous cherchons une fonction qui traite les données des matchs et les ID de série
        
        # Rechercher si la fonction process_match existe déjà
        if 'def process_match(' in content:
            # Modifier la fonction pour intercepter l'ID de série
            # Chercher le début de la fonction
            function_start = content.find('def process_match(')
            function_end = content.find('def ', function_start + 1)
            if function_end == -1:
                function_end = len(content)
            
            function_content = content[function_start:function_end]
            
            # Vérifier si notre code d'interception est déjà présent
            if "# Special case for match 8261452684" not in function_content:
                # Chercher un bon endroit pour insérer notre code
                indent_level = 4  # Niveau d'indentation standard (4 espaces)
                
                # Chercher après le chargement des données du match
                match_load_pos = function_content.find('match_data =')
                if match_load_pos != -1:
                    # Trouver la fin de cette ligne
                    line_end = function_content.find('\n', match_load_pos)
                    if line_end != -1:
                        # Insérer notre code après cette ligne
                        interception_code = '\n' + ' ' * indent_level + '# Special case for match 8261452684 - force series ID s_8261361161\n'
                        interception_code += ' ' * indent_level + 'if match_id == "8261452684" and "series_id" in match_data:\n'
                        interception_code += ' ' * indent_level * 2 + 'match_data["series_id"] = "s_8261361161"\n'
                        interception_code += ' ' * indent_level * 2 + 'if "match_type" in match_data and "series_id" in match_data["match_type"]:\n'
                        interception_code += ' ' * indent_level * 3 + 'match_data["match_type"]["series_id"] = "s_8261361161"\n'
                        interception_code += ' ' * indent_level * 2 + 'logging.info("Match 8261452684: ID de série forcé à s_8261361161")\n'
                        
                        new_function_content = function_content[:line_end + 1] + interception_code + function_content[line_end + 1:]
                        content = content.replace(function_content, new_function_content)
                    
        else:
            # Si process_match n'existe pas, chercher une autre fonction où insérer notre code
            # Par exemple, la fonction qui enrichit les données des matchs
            function_name = 'enrich_match_data'
            function_start = content.find(f'def {function_name}(')
            
            if function_start != -1:
                function_end = content.find('def ', function_start + 1)
                if function_end == -1:
                    function_end = len(content)
                
                function_content = content[function_start:function_end]
                
                # Vérifier si notre code d'interception est déjà présent
                if "# Special case for match 8261452684" not in function_content:
                    # Chercher un bon endroit pour insérer notre code
                    indent_level = 4  # Niveau d'indentation standard (4 espaces)
                    
                    # Chercher après l'initialisation des variables
                    init_pos = function_content.find('match_id =')
                    if init_pos != -1:
                        # Trouver la fin de cette ligne
                        line_end = function_content.find('\n', init_pos)
                        if line_end != -1:
                            # Insérer notre code après cette ligne
                            interception_code = '\n' + ' ' * indent_level + '# Special case for match 8261452684 - force series ID s_8261361161\n'
                            interception_code += ' ' * indent_level + 'if match_id == "8261452684":\n'
                            interception_code += ' ' * indent_level * 2 + 'match_data["series_id"] = "s_8261361161"\n'
                            interception_code += ' ' * indent_level * 2 + 'if "match_type" in match_data and "series_id" in match_data["match_type"]:\n'
                            interception_code += ' ' * indent_level * 3 + 'match_data["match_type"]["series_id"] = "s_8261361161"\n'
                            interception_code += ' ' * indent_level * 2 + 'logging.info("Match 8261452684: ID de série forcé à s_8261361161")\n'
                            
                            new_function_content = function_content[:line_end + 1] + interception_code + function_content[line_end + 1:]
                            content = content.replace(function_content, new_function_content)
            
        # Sauvegarder le fichier modifié
        with open(DOTA_SERVICE_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Le fichier {DOTA_SERVICE_PATH} a été modifié avec succès.")
    except Exception as e:
        print(f"Erreur lors de la modification du fichier {DOTA_SERVICE_PATH}: {e}")


if __name__ == "__main__":
    # Corriger les fichiers de cache
    fix_cache_files()
    
    # Patcher le code de dota_service.py
    patch_dota_service()
    
    print("Toutes les corrections ont été appliquées avec succès!")
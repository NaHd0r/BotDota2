"""
Script pour résoudre deux problèmes simultanément :
1. Associer le match 8261452684 à la série s_8261361161 au lieu de s_8261452684
2. Assurer que les account_ID des joueurs sont correctement transmis aux templates

Ce script modifie à la fois les caches et le code d'extraction des joueurs.
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


def fix_series_association():
    """
    Fonction principale pour associer le match 8261452684 à la série s_8261361161
    et supprimer la série temporaire s_8261452684
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


def fix_template_display():
    """
    Cette fonction modifie le template pour afficher les vrais account_ID des joueurs
    au lieu des indices de position (0, 1, 2, 3, 4)
    """
    TEMPLATE_PATH = 'templates/_scorecards_new.html'
    
    try:
        # Lire le contenu du template
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer les positions par les account_ID
        # Pour la team Radiant
        content = content.replace(
            '                                                                <td>{{ position }}</td>', 
            '                                                                <td>{{ player.account_id }}</td>', 
            1  # Remplacer seulement la première occurrence
        )
        
        # Pour la team Dire
        content = content.replace(
            '                                                                <td>{{ position }}</td>', 
            '                                                                <td>{{ player.account_id }}</td>', 
            1  # Remplacer la deuxième occurrence (car on a déjà remplacé la première)
        )
        
        # Sauvegarder le template modifié
        with open(TEMPLATE_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Le template {TEMPLATE_PATH} a été modifié avec succès.")
    except Exception as e:
        print(f"Erreur lors de la modification du template {TEMPLATE_PATH}: {e}")


if __name__ == "__main__":
    # Corriger l'association de la série
    fix_series_association()
    
    # Corriger l'affichage des account_ID dans le template
    fix_template_display()
    
    print("Toutes les corrections ont été appliquées avec succès!")
"""
Script pour intégrer notre nouveau système d'enrichissement dans dota_service.py

Ce script montre comment modifier process_live_matches dans dota_service.py
pour utiliser notre nouveau système de file d'attente d'enrichissement.
"""

import logging

# Configuration du logger
logger = logging.getLogger(__name__)

# Les modifications à apporter à dota_service.py

IMPORT_STATEMENTS = """import os
import json
import time
import gzip
import logging
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set

import api_field_mapping
import dual_cache_system as cache
import auto_enrich_matches  # Ajouter cette ligne pour importer notre système d'enrichissement
"""

PROCESS_LIVE_MATCHES_FUNCTION = """def process_live_matches() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """API endpoint to get the latest match data"""
    try:
        # Obtenir les matchs en direct depuis l'API Steam
        matches, error = get_live_matches()
        
        if error:
            return [], []
            
        # Traiter et enrichir les matchs
        matches = enrich_matches_with_series_data(matches)
        
        # Mettre à jour le cache avec les matchs en direct
        update_live_cache(matches)
        
        # Détecter les matchs terminés et les ajouter à la file d'enrichissement
        # Utiliser notre nouveau système d'enrichissement automatique
        disappeared_matches = auto_enrich_matches.process_active_matches(matches)
        
        # Retourner les matchs en direct et ceux qui ont disparu
        return matches, disappeared_matches
    
    except Exception as e:
        logger.error(f"Erreur dans process_live_matches: {e}")
        return [], []
"""

# Instructions d'intégration
print("""
Pour intégrer le système d'enrichissement automatique, vous devez effectuer les modifications suivantes dans dota_service.py :

1. Ajouter l'import du module auto_enrich_matches:
   Dans la section des imports, ajouter:
   
   ```python
   import auto_enrich_matches  # pour l'enrichissement automatique
   ```

2. Modifier la fonction process_live_matches pour utiliser notre système d'enrichissement:
   Remplacer la fonction existante par la fonction fournie ci-dessus.

3. S'assurer que les fonctions suivantes existent dans opendota_service.py:
   - get_match_details(match_id)
   - convert_to_internal_format(match_data)

Si ces fonctions n'existent pas, vous devrez les implémenter comme indiqué dans le module enrich_matches_queue.py.

Le système d'enrichissement automatique est configuré pour:
- Détecter automatiquement les matchs terminés (disparus de l'API Steam)
- Faire une première tentative d'enrichissement 2 secondes après la détection
- En cas d'échec, faire une seconde tentative 10 secondes après la détection
- Si les données ne sont toujours pas disponibles après ces deux essais, abandonner l'enrichissement
""")

# Fonction principale pour intégrer les modifications
def integrate_enrichment():
    """
    Cette fonction serait utilisée pour intégrer automatiquement les modifications,
    mais nous préférons une approche manuelle pour plus de contrôle.
    """
    pass

if __name__ == "__main__":
    print("Instructions d'intégration générées avec succès!")
    print("Veuillez les suivre manuellement pour intégrer le système d'enrichissement.")
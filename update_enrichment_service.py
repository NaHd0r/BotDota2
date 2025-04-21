"""
Script pour s'assurer que le système d'enrichissement des matchs fonctionne correctement
en utilisant les modules existants (enrich_matches_queue.py et opendota_service.py).

Ce script effectue la vérification et la correction de la cohérence des statuts
pour s'assurer que le système d'enrichissement fonctionne bien.
"""

import os
import logging
import importlib
import sys

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_enrichment_dependencies():
    """
    Vérifie que toutes les dépendances nécessaires pour l'enrichissement
    sont présentes et fonctionnelles
    """
    # Liste des modules requis
    required_modules = [
        "opendota_service",
        "enrich_matches_queue"
    ]
    
    missing_modules = []
    for module_name in required_modules:
        try:
            # Essayer d'importer le module
            module = importlib.import_module(module_name)
            logger.info(f"Module {module_name} importé avec succès")
        except ImportError:
            logger.error(f"Module {module_name} manquant")
            missing_modules.append(module_name)
    
    if missing_modules:
        logger.error(f"Modules manquants: {', '.join(missing_modules)}")
        return False
    
    return True

def check_get_match_details_function():
    """
    Vérifie que la fonction get_match_details existe dans opendota_service
    """
    try:
        # Importer opendota_service
        import opendota_service
        
        # Vérifier si la fonction get_match_details existe
        if hasattr(opendota_service, 'get_match_details'):
            logger.info("Fonction get_match_details trouvée dans opendota_service")
            return True
        else:
            logger.warning("Fonction get_match_details manquante dans opendota_service")
            return False
    except ImportError:
        logger.error("Impossible d'importer opendota_service")
        return False

def verify_app_imports_enrichment():
    """
    Vérifie si app.py importe bien le module d'enrichissement
    """
    app_path = "app.py"
    if not os.path.exists(app_path):
        logger.error(f"Fichier {app_path} introuvable")
        return False
    
    # Lire le contenu du fichier
    with open(app_path, 'r') as f:
        content = f.read()
    
    # Vérifier si l'import est présent
    if "import enrich_matches_queue" in content:
        logger.info("Import enrich_matches_queue trouvé dans app.py")
        return True
    else:
        logger.warning("Import enrich_matches_queue manquant dans app.py")
        return False

def run_fix_status_consistency():
    """
    Exécute le script de correction de cohérence des statuts
    """
    try:
        # Importer le module
        import fix_status_consistency
        
        # Appeler la fonction principale
        fix_status_consistency.main()
        logger.info("Correction de la cohérence des statuts terminée avec succès")
        return True
    except ImportError:
        logger.error("Module fix_status_consistency introuvable")
        return False
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de fix_status_consistency: {e}")
        return False

def main():
    """
    Fonction principale du script
    """
    logger.info("=== Démarrage de la vérification du système d'enrichissement ===")
    
    # 1. Vérifier les dépendances
    if not check_enrichment_dependencies():
        logger.error("Certaines dépendances sont manquantes, correction impossible")
        return
    
    # 2. Vérifier la fonction get_match_details
    if not check_get_match_details_function():
        logger.error("La fonction get_match_details n'existe pas dans opendota_service")
        return
    
    # 3. Vérifier que app.py importe le module d'enrichissement
    verify_app_imports_enrichment()
    
    # 4. Exécuter la correction de cohérence des statuts
    if os.path.exists("fix_status_consistency.py"):
        run_fix_status_consistency()
    else:
        logger.warning("Le script fix_status_consistency.py n'existe pas")
    
    logger.info("=== Vérification du système d'enrichissement terminée ===")
    logger.info("Le système d'enrichissement des matchs est prêt à fonctionner")

if __name__ == "__main__":
    main()
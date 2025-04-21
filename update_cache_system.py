"""
Script pour mettre à jour le système de cache Dota 2 Dashboard

Ce script effectue les actions suivantes:
1. Sauvegarde les anciens fichiers de cache
2. Exécute la migration vers le nouveau système
3. Remplace les fichiers de service par leurs versions actualisées
4. Redémarre l'application pour utiliser le nouveau système
"""

import os
import shutil
import logging
import subprocess
import time

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_backup(filename):
    """Crée une sauvegarde d'un fichier"""
    if os.path.exists(filename):
        backup_dir = "backup_files"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        backup_file = os.path.join(backup_dir, f"{os.path.basename(filename)}.{int(time.time())}.bak")
        shutil.copy2(filename, backup_file)
        logger.info(f"Sauvegarde créée: {backup_file}")
        return True
    return False

def update_files():
    """Met à jour les fichiers du système"""
    # Liste des fichiers à mettre à jour
    files_to_update = [
        ("dota_service.py.new", "dota_service.py"),
        ("app.py.new", "app.py")
    ]
    
    for source, target in files_to_update:
        # Vérifier que le fichier source existe
        if not os.path.exists(source):
            logger.error(f"Fichier source non trouvé: {source}")
            continue
        
        # Sauvegarder le fichier cible s'il existe
        create_backup(target)
        
        # Remplacer le fichier cible
        shutil.copy2(source, target)
        logger.info(f"Fichier mis à jour: {target}")

def run_migration():
    """Exécute le script de migration"""
    try:
        subprocess.run(["python", "migrate_cache.py"], check=True)
        logger.info("Migration réussie")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de la migration: {e}")
        return False

def restart_application():
    """Redémarre l'application Flask"""
    try:
        # Pour un environnement réel, cette commande varie selon la configuration
        logger.info("Redémarrage de l'application...")
        # Exemple: redémarrer le processus gunicorn
        # subprocess.run(["systemctl", "restart", "gunicorn"], check=True)
        return True
    except Exception as e:
        logger.error(f"Erreur lors du redémarrage: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("Démarrage de la mise à jour du système de cache...")
    
    # Exécuter la migration
    logger.info("Exécution de la migration...")
    if not run_migration():
        logger.error("La migration a échoué, arrêt de la mise à jour")
        return False
    
    # Mettre à jour les fichiers
    logger.info("Mise à jour des fichiers...")
    update_files()
    
    # Redémarrer l'application
    logger.info("Redémarrage de l'application...")
    restart_application()
    
    logger.info("Mise à jour terminée avec succès!")
    return True

if __name__ == "__main__":
    main()
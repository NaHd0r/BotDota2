"""
Script pour corriger l'affichage des scores de série dans l'interface utilisateur

Ce script modifie le fichier static/js/main.js pour s'assurer que les scores de série
sont correctement affichés en utilisant les valeurs de l'API Steam.
"""

import os
import re
import logging

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chemin du fichier JavaScript principal
JS_FILE = "static/js/main.js"

def backup_file(file_path):
    """Crée une sauvegarde du fichier"""
    backup_path = f"{file_path}.bak"
    try:
        with open(file_path, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        logger.info(f"Sauvegarde créée: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde: {e}")
        return False

def find_series_score_section(js_content):
    """Trouve la section de code qui gère l'affichage des scores de série"""
    # Pattern pour trouver le début de la section
    pattern = r'// Créer un badge score de série simple et efficace'
    match = re.search(pattern, js_content)
    
    if match:
        section_start = match.start()
        
        # Chercher la fin de la section (prochaine accolade fermante majeure)
        brace_count = 0
        section_end = section_start
        for i in range(section_start, len(js_content)):
            if js_content[i] == '{':
                brace_count += 1
            elif js_content[i] == '}':
                brace_count -= 1
                if brace_count < 0:
                    section_end = i + 1
                    break
        
        return section_start, section_end
    
    return None, None

def fix_series_score_display():
    """Corrige l'affichage des scores de série dans le fichier JS"""
    if not os.path.exists(JS_FILE):
        logger.error(f"Fichier non trouvé: {JS_FILE}")
        return False
    
    # Créer une sauvegarde
    if not backup_file(JS_FILE):
        return False
    
    try:
        # Lire le contenu du fichier
        with open(JS_FILE, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Trouver la section à modifier
        start, end = find_series_score_section(js_content)
        if start is None or end is None:
            logger.error("Section de code pour l'affichage des scores non trouvée")
            return False
        
        # Ancien code
        old_code = js_content[start:end]
        
        # Nouveau code avec une vérification plus robuste
        new_code = """
        // Créer un badge score de série simple et efficace en utilisant le champ score_text du backend
        const seriesScoreBadge = document.createElement('div');
        seriesScoreBadge.className = 'badge bg-warning text-dark fs-4 px-4 py-2 mt-2 mb-2 series-score-badge';
        
        // Récupérer directement les valeurs de l'API Steam
        const radiantSeriesWins = match.radiant_series_wins !== undefined ? match.radiant_series_wins : 0;
        const direSeriesWins = match.dire_series_wins !== undefined ? match.dire_series_wins : 0;
        
        console.log(`SCORES DE SÉRIE BRUTS - API Steam: radiant=${radiantSeriesWins}, dire=${direSeriesWins}`);
        
        // Utiliser window.normalizedTeams pour maintenir la cohérence des équipes
        if (window.normalizedTeams && typeof window.normalizedTeams.leftIsRadiant !== 'undefined') {
            // Si on a normalisé les équipes, on ajuste l'affichage des scores
            const leftScore = window.normalizedTeams.leftIsRadiant ? radiantSeriesWins : direSeriesWins;
            const rightScore = window.normalizedTeams.leftIsRadiant ? direSeriesWins : radiantSeriesWins;
            seriesScoreBadge.innerHTML = `<strong>Score série:</strong> <span class="fs-3">${leftScore}-${rightScore}</span>`;
            console.log(`SCORE SÉRIE NORMALISÉ: ${leftScore}-${rightScore}`);
        } else {
            // Sinon on utilise l'affichage classique
            seriesScoreBadge.innerHTML = `<strong>Score série:</strong> <span class="fs-3">${radiantSeriesWins}-${direSeriesWins}</span>`;
            console.log(`SCORE SÉRIE CLASSIQUE: ${radiantSeriesWins}-${direSeriesWins}`);
        }
        matchHeader.appendChild(seriesScoreBadge);
        """
        
        # Remplacer le code
        new_js_content = js_content[:start] + new_code + js_content[end:]
        
        # Écrire le nouveau contenu
        with open(JS_FILE, 'w', encoding='utf-8') as f:
            f.write(new_js_content)
        
        logger.info("Fichier JavaScript mis à jour avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la modification du fichier: {e}")
        return False

def fix_team_normalization_section():
    """Corrige la section de normalisation des équipes pour utiliser les scores de l'API"""
    if not os.path.exists(JS_FILE):
        logger.error(f"Fichier non trouvé: {JS_FILE}")
        return False
    
    try:
        # Lire le contenu du fichier
        with open(JS_FILE, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Chercher la section de normalisation des équipes (où window.normalizedTeams est défini)
        pattern = r'// Normaliser l\'ordre des équipes.*?window\.normalizedTeams\s*=\s*{.*?};'
        match = re.search(pattern, js_content, re.DOTALL)
        
        if not match:
            logger.error("Section de normalisation des équipes non trouvée")
            return False
        
        # Ancien code
        old_code = match.group(0)
        
        # Modifier le code pour ajouter un log de debug
        new_code = old_code + """
        
        // Debug de la normalisation des équipes
        console.log("NORMALISATION DES ÉQUIPES:", window.normalizedTeams);
        if (window.normalizedTeams) {
            console.log(`- leftIsRadiant: ${window.normalizedTeams.leftIsRadiant}`);
            console.log(`- Team à gauche: ${window.normalizedTeams.leftIsRadiant ? 'Radiant' : 'Dire'}`);
            console.log(`- Team à droite: ${window.normalizedTeams.leftIsRadiant ? 'Dire' : 'Radiant'}`);
            if (match.radiant_series_wins !== undefined && match.dire_series_wins !== undefined) {
                console.log(`- Score si normalisé: ${window.normalizedTeams.leftIsRadiant ? match.radiant_series_wins : match.dire_series_wins}-${window.normalizedTeams.leftIsRadiant ? match.dire_series_wins : match.radiant_series_wins}`);
            }
        }
        """
        
        # Remplacer le code
        new_js_content = js_content.replace(old_code, new_code)
        
        # Écrire le nouveau contenu
        with open(JS_FILE, 'w', encoding='utf-8') as f:
            f.write(new_js_content)
        
        logger.info("Section de normalisation des équipes mise à jour avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la modification du fichier: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("Démarrage de la correction des scores de série...")
    
    # Corriger l'affichage des scores
    if fix_series_score_display():
        logger.info("Affichage des scores de série corrigé avec succès")
    else:
        logger.error("Échec de la correction de l'affichage des scores")
    
    # Corriger la normalisation des équipes
    if fix_team_normalization_section():
        logger.info("Normalisation des équipes améliorée avec succès")
    else:
        logger.warning("Échec de l'amélioration de la normalisation des équipes")
    
    logger.info("Correction terminée")

if __name__ == "__main__":
    main()
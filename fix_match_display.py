#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script simple pour corriger l'affichage des numéros de matchs en fonction des scores.
Corrige la fonction get_match_type dans dota_service.py.
"""

import re

def fix_match_display():
    # Charger le fichier
    with open("dota_service.py", "r") as f:
        content = f.read()
    
    # Trouver la section qui calcule game_number
    pattern = r'(\s+)game_number\s*=\s*radiant_series_wins\s*\+\s*dire_series_wins\s*\+\s*1'
    match = re.search(pattern, content)
    
    if match:
        indentation = match.group(1)
        # Nouvelle logique directe et simple
        new_code = f"""{indentation}# CORRECTION: Game number est simplement la somme wins + 1
{indentation}# - score 0-0 → GAME 1
{indentation}# - score 1-0 ou 0-1 → GAME 2
{indentation}# - score 1-1 → GAME 3
{indentation}# - score 2-0, 0-2, 2-1 ou 1-2 → série terminée
{indentation}game_number = radiant_series_wins + dire_series_wins + 1
{indentation}logger.info(f"CALCUL DIRECT: match_id={{match_id}}, radiant_wins={{radiant_series_wins}}, dire_wins={{dire_series_wins}}, game_number={{game_number}})")"""
        
        # Remplacer la section
        new_content = re.sub(pattern, new_code, content)
        
        # Sauvegarder le fichier
        with open("dota_service.py", "w") as f:
            f.write(new_content)
        
        print("Modification réussie! Logique de Game Number simplifiée.")
        return True
    else:
        print("Section non trouvée dans le fichier.")
        return False

if __name__ == "__main__":
    success = fix_match_display()
    print(f"Résultat: {'OK' if success else 'ÉCHEC'}")
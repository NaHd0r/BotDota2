def find_previous_matches(team1_id, team2_id, max_results=5):
    """
    Cette fonction a été conservée pour la compatibilité mais ne recherche plus
    les matchs précédents entre deux équipes. Utilisez get_matches_by_series_id() à la place.
    
    Args:
        team1_id: ID de la première équipe (ignoré)
        team2_id: ID de la deuxième équipe (ignoré)
        max_results: Nombre maximal de résultats à retourner
        
    Returns:
        Une liste vide de dictionnaires
    """
    logger.info(f"Fonction obsolète: find_previous_matches({team1_id}, {team2_id})")
    return []
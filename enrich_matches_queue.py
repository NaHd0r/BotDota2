"""
Module pour gérer l'enrichissement automatique des matchs terminés
via l'API OpenDota avec une file d'attente et une stratégie de réessai.

Ce module implémente une solution légère pour s'assurer que les données des matchs
sont enrichies après leur disparition de l'API Steam, avec un maximum de 2 tentatives :
- Premier essai : 2 secondes après la détection de fin de match
- Second essai : 10 secondes après la détection de fin de match
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional

# Importer les modules nécessaires
import opendota_service
import dual_cache_system as cache

# Configuration du logger
logger = logging.getLogger(__name__)

# Chemin du fichier de file d'attente
ENRICH_QUEUE_PATH = os.path.join("cache", "enrich_queue.json")

def load_enrich_queue() -> Dict[str, Dict[str, Any]]:
    """
    Charge la file d'attente d'enrichissement depuis le fichier
    
    Returns:
        dict: Dictionnaire avec les IDs de match comme clés et les informations d'enrichissement comme valeurs
    """
    if not os.path.exists(ENRICH_QUEUE_PATH):
        return {}
    
    try:
        with open(ENRICH_QUEUE_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Erreur lors du chargement de la file d'attente: {e}")
        return {}

def save_enrich_queue(queue: Dict[str, Dict[str, Any]]) -> None:
    """
    Sauvegarde la file d'attente d'enrichissement dans le fichier
    
    Args:
        queue (dict): Dictionnaire de la file d'attente à sauvegarder
    """
    try:
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(ENRICH_QUEUE_PATH), exist_ok=True)
        
        with open(ENRICH_QUEUE_PATH, 'w') as f:
            json.dump(queue, f, indent=2)
    except IOError as e:
        logger.error(f"Erreur lors de la sauvegarde de la file d'attente: {e}")

def is_complete_data(match_data: Dict[str, Any]) -> bool:
    """
    Vérifie si les données du match sont complètes
    
    Args:
        match_data (dict): Données du match à vérifier
        
    Returns:
        bool: True si les données sont complètes, False sinon
    """
    # Vérifier les champs essentiels qui indiquent que le match est terminé
    required_fields = [
        "match_id", "duration", "radiant_score", "dire_score",
        "radiant_win", "start_time", "players"
    ]
    
    for field in required_fields:
        if field not in match_data or match_data[field] is None:
            return False
    
    # Vérifier si le champ duration est non nul
    if match_data["duration"] <= 0:
        return False
        
    return True

def update_cache_with_match(match_id: str, match_data: Dict[str, Any]) -> bool:
    """
    Met à jour le cache avec les données enrichies du match
    
    Args:
        match_id (str): ID du match
        match_data (dict): Données enrichies du match
        
    Returns:
        bool: True si la mise à jour a réussi, False sinon
    """
    try:
        # Convertir les données OpenDota en format interne
        internal_data = opendota_service.convert_to_internal_format(match_data)
        
        # Récupérer le match actuel du cache pour conserver certaines informations
        current_match = cache.get_match_from_live_cache(match_id)
        if current_match:
            # Conserver l'ID de série et d'autres informations importantes
            if "series_id" in current_match:
                internal_data["series_id"] = current_match["series_id"]
            
            # Mettre à jour le statut pour indiquer que le match est terminé
            internal_data["status"] = "finished"
            internal_data["status_tag"] = "finished"
            
            # Déterminer le gagnant
            if "radiant_win" in match_data:
                internal_data["winner"] = "radiant" if match_data["radiant_win"] else "dire"
            
            # Mettre à jour le cache
            cache_data = cache.load_live_data()
            cache_data["matches"][match_id] = internal_data
            cache.save_live_data(cache_data)
            
            logger.info(f"Match {match_id} enrichi avec succès via OpenDota")
            return True
        else:
            logger.warning(f"Match {match_id} non trouvé dans le cache, impossible de l'enrichir")
            return False
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du cache pour le match {match_id}: {e}")
        return False

def enrich_match_and_queue(match_id: str, immediate: bool = True) -> bool:
    """
    Enrichit un match terminé avec OpenDota ou l'ajoute à la file d'attente
    
    Args:
        match_id (str): ID du match à enrichir
        immediate (bool): Si True, tente d'enrichir immédiatement avant de mettre en file d'attente
        
    Returns:
        bool: True si l'enrichissement a réussi immédiatement, False sinon
    """
    # Vérifier si le match est déjà dans la file d'attente
    enrich_queue = load_enrich_queue()
    
    if match_id in enrich_queue:
        logger.info(f"Match {match_id} déjà dans la file d'attente d'enrichissement")
        return False
    
    # Si demandé, essayer d'enrichir immédiatement
    if immediate:
        try:
            match_data = opendota_service.get_match_details(match_id)
            
            if match_data and is_complete_data(match_data):
                success = update_cache_with_match(match_id, match_data)
                if success:
                    logger.info(f"Match {match_id} enrichi immédiatement avec succès")
                    return True
        except Exception as e:
            logger.error(f"Erreur lors de l'enrichissement immédiat du match {match_id}: {e}")
    
    # Si l'enrichissement immédiat n'a pas réussi, ajouter à la file d'attente
    current_time = time.time()
    enrich_queue[match_id] = {
        "detected_at": current_time,
        "attempts": 0,
        "next_attempt_at": current_time + 2,  # Premier essai après 2 secondes
        "status": "pending"
    }
    
    save_enrich_queue(enrich_queue)
    logger.info(f"Match {match_id} ajouté à la file d'attente d'enrichissement")
    return False

def process_enrich_queue() -> List[str]:
    """
    Traite la file d'attente d'enrichissement
    
    Returns:
        list: Liste des IDs de match traités avec succès
    """
    enrich_queue = load_enrich_queue()
    current_time = time.time()
    enriched_matches = []
    
    for match_id, info in list(enrich_queue.items()):
        # Vérifier si c'est l'heure de traiter ce match
        if info["next_attempt_at"] <= current_time:
            logger.info(f"Tentative d'enrichissement pour le match {match_id} (essai #{info['attempts'] + 1})")
            
            try:
                # Tenter d'obtenir les données du match
                match_data = opendota_service.get_match_details(match_id)
                
                if match_data and is_complete_data(match_data):
                    # Données complètes trouvées, mettre à jour le cache
                    success = update_cache_with_match(match_id, match_data)
                    
                    if success:
                        logger.info(f"Match {match_id} enrichi avec succès (essai #{info['attempts'] + 1})")
                        # Supprimer le match de la file d'attente
                        del enrich_queue[match_id]
                        enriched_matches.append(match_id)
                        continue
                
                # Si on arrive ici, l'enrichissement n'a pas réussi
                info["attempts"] += 1
                
                # Si on a déjà fait 1 tentative (donc c'était la deuxième), supprimer de la file
                if info["attempts"] >= 1:  # Max 2 tentatives (initiale + 1 réessai)
                    logger.warning(f"Abandon de l'enrichissement du match {match_id} après 2 tentatives")
                    del enrich_queue[match_id]
                else:
                    # Planifier le prochain essai dans 8 secondes (2s + 8s = 10s après détection)
                    info["next_attempt_at"] = current_time + 8
                    info["status"] = "retrying"
                    logger.info(f"Nouvelle tentative planifiée pour le match {match_id} dans 8 secondes")
            
            except Exception as e:
                logger.error(f"Erreur lors du traitement du match {match_id}: {e}")
                # En cas d'erreur, on incrémente quand même le compteur
                info["attempts"] += 1
                
                # Si on a atteint le nombre max de tentatives, supprimer de la file
                if info["attempts"] >= 1:
                    logger.warning(f"Abandon de l'enrichissement du match {match_id} après erreur")
                    del enrich_queue[match_id]
                else:
                    # Sinon, planifier le prochain essai
                    info["next_attempt_at"] = current_time + 8
                    info["status"] = "error"
    
    # Sauvegarder la file d'attente mise à jour
    save_enrich_queue(enrich_queue)
    return enriched_matches

def get_queue_status() -> Dict[str, Any]:
    """
    Obtient le statut actuel de la file d'attente
    
    Returns:
        dict: Informations sur l'état actuel de la file d'attente
    """
    enrich_queue = load_enrich_queue()
    
    return {
        "pending_matches": len(enrich_queue),
        "queue": enrich_queue
    }

# Fonction pour être appelée régulièrement par le processus principal
def check_and_process_queue() -> None:
    """
    Vérifie et traite la file d'attente d'enrichissement
    Cette fonction est conçue pour être appelée régulièrement (chaque seconde)
    """
    try:
        enriched_matches = process_enrich_queue()
        if enriched_matches:
            logger.info(f"{len(enriched_matches)} matchs enrichis avec succès")
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la file d'attente: {e}")
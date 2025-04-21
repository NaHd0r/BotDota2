# Mapping des champs entre les différentes API et caches

## Steam API → Format Interne

| Champ Steam API | Champ Interne | Description |
|----------------|---------------|------------|
| match_id | match_id | ID du match |
| activate_time | start_time | Timestamp du début du match |
| league_id | league_id | ID de la ligue |
| lobby_id | lobby_id | ID du lobby |
| lobby_type | lobby_type | Type de lobby |
| series_type | series_type | Type de série (0=Bo1, 1=Bo3, 2=Bo5) |
| series_id | series_id | ID de la série |
| game_time | duration_seconds | Durée en secondes |
| game_state | - | État du jeu (5 = en cours) |
| **Équipe Radiant** |
| radiant_team.team_id | radiant_team_id | ID de l'équipe Radiant |
| radiant_team.name | radiant_team_name | Nom de l'équipe Radiant |
| radiant_team.score | radiant_score | Score de l'équipe Radiant |
| team_id_radiant | radiant_team_id | ID alternatif |
| team_name_radiant | radiant_team_name | Nom alternatif |
| **Équipe Dire** |
| dire_team.team_id | dire_team_id | ID de l'équipe Dire |
| dire_team.name | dire_team_name | Nom de l'équipe Dire |
| dire_team.score | dire_score | Score de l'équipe Dire |
| team_id_dire | dire_team_id | ID alternatif |
| team_name_dire | dire_team_name | Nom alternatif |
| **Joueur** |
| account_id | account_id | ID du compte du joueur |
| hero_id | hero_id | ID du héros joué |
| net_worth | net_worth | Networth du joueur |
| name | name | Nom du joueur |

## OpenDota API → Format Interne

| Champ OpenDota API | Champ Interne | Description |
|-------------------|---------------|------------|
| match_id | match_id | ID du match |
| start_time | start_time | Timestamp du début du match |
| duration | duration_seconds | Durée en secondes |
| series_id | series_id | ID de la série |
| series_type | series_type | Type de série |
| radiant_win | - | True si l'équipe Radiant a gagné |
| first_blood_time | first_blood_time | Temps du premier sang |
| **Ligue** |
| league.leagueid | league_id | ID de la ligue |
| league.name | league_name | Nom de la ligue |
| **Équipe Radiant** |
| radiant_team.team_id | radiant_team_id | ID de l'équipe Radiant |
| radiant_team.name | radiant_team_name | Nom de l'équipe Radiant |
| **Équipe Dire** |
| dire_team.team_id | dire_team_id | ID de l'équipe Dire |
| dire_team.name | dire_team_name | Nom de l'équipe Dire |
| **Scores** |
| radiant_score | radiant_score | Score de l'équipe Radiant |
| dire_score | dire_score | Score de l'équipe Dire |

## Structure des caches

### Cache des séries en direct (live_series_cache.json)

| Champ | Description |
|-------|------------|
| series_id | ID de la série |
| radiant_team_id ou radiant_id | ID de l'équipe Radiant |
| dire_team_id ou dire_id | ID de l'équipe Dire |
| radiant_team_name | Nom de l'équipe Radiant |
| dire_team_name | Nom de l'équipe Dire |
| radiant_score | Score de l'équipe Radiant dans la série |
| dire_score | Score de l'équipe Dire dans la série |
| matches | Liste des matchs dans la série |
| series_type | Type de série (0=Bo1, 1=Bo3, 2=Bo5) |
| completed | True si la série est terminée |
| league_id | ID de la ligue |

### Cache des séries complétées (completed_series_cache.json)

| Champ | Description |
|-------|------------|
| series_id | ID de la série |
| radiant_team_id ou radiant_id | ID de l'équipe Radiant |
| dire_team_id ou dire_id | ID de l'équipe Dire |
| radiant_team_name | Nom de l'équipe Radiant |
| dire_team_name | Nom de l'équipe Dire |
| radiant_score | Score final de l'équipe Radiant dans la série |
| dire_score | Score final de l'équipe Dire dans la série |
| matches | Liste des matchs dans la série |
| series_type | Type de série |
| completed | True (toujours à true) |
| completion_time | Timestamp de fin de la série |
| league_id | ID de la ligue |

### Cache principal des séries (series_cache.json)

| Champ | Description |
|-------|------------|
| series_id | ID de la série |
| radiant_team_id | ID de l'équipe Radiant |
| dire_team_id | ID de l'équipe Dire |
| radiant_team_name | Nom de l'équipe Radiant |
| dire_team_name | Nom de l'équipe Dire |
| radiant_score | Score actuel de la série |
| dire_score | Score actuel de la série |
| previous_matches | Matchs précédents dans la série |
| series_type | Type de série |

### Structure d'un match (pour les matchs dans live_series_cache et completed_series_cache)

| Champ | Description |
|-------|------------|
| match_id | ID du match |
| league_id | ID de la ligue |
| radiant_team_id | ID de l'équipe Radiant |
| dire_team_id | ID de l'équipe Dire |
| radiant_team_name | Nom de l'équipe Radiant |
| dire_team_name | Nom de l'équipe Dire |
| radiant_score | Score de l'équipe Radiant (kills) |
| dire_score | Score de l'équipe Dire (kills) |
| total_kills | Total des kills |
| duration | Durée en secondes ou formatée |
| duration_formatted | Durée formatée (MM:SS) |
| radiant_networth | Networth total de l'équipe Radiant |
| dire_networth | Networth total de l'équipe Dire |
| networth_difference | Différence de networth |
| match_state / draft_phase | Information sur l'état du match |
| match_outcome | Résultat du match (0 = en cours) |
| game_number | Numéro du match dans la série |
| timestamp | Timestamp du début du match |
| winner | "radiant" ou "dire" pour les matchs terminés |

### Structure d'un match précédent (dans series_cache.json)

| Champ | Description |
|-------|------------|
| match_id | ID du match |
| radiant_team_name | Nom de l'équipe Radiant |
| dire_team_name | Nom de l'équipe Dire |
| radiant_score | Score final de l'équipe Radiant |
| dire_score | Score final de l'équipe Dire |
| duration | Durée formatée (MM:SS) |
| total_kills | Nombre total de kills |
| game_number | Numéro du match dans la série |
| winner | "radiant" ou "dire" |
| timestamp | Timestamp du match |

## Problèmes de nommage identifiés

1. Inconsistance entre `radiant_team_id` et `radiant_id` dans différents caches
2. Champs dupliqués comme `duration` et `duration_formatted` 
3. Utilisation à la fois de `match_state` (objet) et `draft_phase` (booléen)
4. Structures imbriquées vs champs plats (ex: radiant_team.team_id vs radiant_team_id)
5. Différences de structure entre les "previous_matches" et les entrées dans "matches"
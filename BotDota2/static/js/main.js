// Global variables
let lastUpdateTime = null;
let refreshInterval = null;
let currentMatches = [];
let currentHistoryMatches = [];
let isActiveMatches = false;

// League IDs to names mapping
const LEAGUE_NAMES = {
    '17911': 'Mad Dogs League (ID: 17911)',
    '17211': 'Space League (ID: 17211)'
};

// Fonction pour calculer le net worth total d'une équipe
function calculateTeamNetWorth(match, side) {
    let totalNetWorth = 0;
    
    try {
        // Accès direct aux joueurs dans la structure radiant/dire
        const players = match.scoreboard?.[side]?.players || [];
        
        // Parcourir tous les joueurs et additionner leur net worth
        for (let i = 0; i < players.length; i++) {
            if (players[i] && typeof players[i].net_worth === 'number') {
                totalNetWorth += players[i].net_worth;
            }
        }
        
        return totalNetWorth;
    } catch (error) {
        console.error(`Erreur lors du calcul du net worth pour ${side}:`, error);
        return 0;
    }
}

// Initialize the application
function initializeApp() {
    // Set up event handlers
    document.getElementById('refresh-btn').addEventListener('click', fetchMatchData);
    document.getElementById('refresh-history-btn').addEventListener('click', function() {
        const seriesId = document.getElementById('series-id').value;
        if (seriesId) {
            fetchMatchBySeries(seriesId);
        }
    });
    
    // Set up the form submission for series search only
    document.getElementById('series-search-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const seriesId = document.getElementById('series-id').value;
        if (seriesId) {
            fetchMatchBySeries(seriesId);
        }
    });
    
    // Set up the toggle details functionality for dynamically added elements
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('toggle-details') || 
            event.target.parentElement.classList.contains('toggle-details')) {
            const button = event.target.classList.contains('toggle-details') ? 
                event.target : event.target.parentElement;
            const matchCard = button.closest('.match-card');
            const detailsSection = matchCard.querySelector('.team-details');
            
            if (detailsSection.style.display === 'none') {
                detailsSection.style.display = 'block';
                button.innerHTML = '<i class="fas fa-chevron-up me-2"></i> Hide Team Details';
            } else {
                detailsSection.style.display = 'none';
                button.innerHTML = '<i class="fas fa-chevron-down me-2"></i> Show Team Details';
            }
        }
    });
    
    // Fetch initial data
    fetchMatchData();
    
    // Set up initial refresh interval (5 minutes when no matches)
    updateRefreshInterval(false);
}

// Récupérer les données des matchs depuis l'API
function fetchMatchData() {
    showLoadingIndicator();
    
    fetch('/api/matches')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Stocker les matchs et mettre à jour l'interface
                currentMatches = data.matches;
                lastUpdateTime = new Date();
                updateLastUpdatedTime();
                renderMatches(data.matches);
                
                // Ajuster la fréquence de rafraîchissement
                const hasMatches = data.matches.length > 0;
                if (hasMatches !== isActiveMatches) {
                    isActiveMatches = hasMatches;
                    updateRefreshInterval(hasMatches);
                    
                    if (hasMatches) {
                        console.log("Active matches detected - refresh rate set to 8-11 seconds");
                    } else {
                        console.log("No active matches - refresh rate set to 5 minutes");
                    }
                }
            } else {
                showError("Échec de récupération des données : " + data.error);
            }
        })
        .catch(error => {
            console.error("Erreur lors de la récupération des données :", error);
            showError("Erreur de connexion au serveur. Veuillez réessayer plus tard.");
        })
        .finally(() => {
            hideLoadingIndicator();
        });
}

// Update the "Last Updated" timestamp
function updateLastUpdatedTime() {
    const lastUpdatedElement = document.getElementById('last-updated');
    if (lastUpdateTime) {
        const timeString = lastUpdateTime.toLocaleTimeString();
        lastUpdatedElement.textContent = `Last updated: ${timeString}`;
    }
}

// Show loading indicator
function showLoadingIndicator() {
    document.getElementById('loading-indicator').style.display = 'block';
    document.getElementById('matches-container').style.display = 'none';
    document.getElementById('no-matches').style.display = 'none';
}

// Hide loading indicator
function hideLoadingIndicator() {
    document.getElementById('loading-indicator').style.display = 'none';
    document.getElementById('matches-container').style.display = 'block';
}

// Show error message
function showError(message) {
    const container = document.getElementById('matches-container');
    container.innerHTML = `
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-circle me-2"></i>
            ${message}
        </div>
    `;
    container.style.display = 'block';
    document.getElementById('loading-indicator').style.display = 'none';
    document.getElementById('no-matches').style.display = 'none';
}

// Mettre à jour l'intervalle de rafraîchissement en fonction de la présence de matchs
function updateRefreshInterval(hasMatches) {
    // Effacer l'intervalle existant
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    // Si l'état des matchs a changé, mettre à jour la fréquence de rafraîchissement
    if (hasMatches) {
        // Matchs actifs - rafraîchir toutes les 8-11 secondes
        const refreshTime = Math.floor(Math.random() * 4) + 8; // 8-11 secondes
        refreshInterval = setInterval(fetchMatchData, refreshTime * 1000);
        console.log(`Matchs actifs détectés - fréquence de rafraîchissement définie à ${refreshTime} secondes`);
    } else {
        // Pas de matchs - rafraîchir toutes les 5 minutes
        refreshInterval = setInterval(fetchMatchData, 5 * 60 * 1000);
        console.log('Aucun match actif - fréquence de rafraîchissement définie à 5 minutes');
    }
}

// Afficher les matchs dans l'interface utilisateur
function renderMatches(matches) {
    const container = document.getElementById('matches-container');
    const noMatchesElement = document.getElementById('no-matches');
    
    // Effacer le contenu précédent
    container.innerHTML = '';
    
    // Vérifier s'il y a des matchs à afficher
    if (!matches || matches.length === 0) {
        noMatchesElement.style.display = 'block';
        return;
    }
    
    // Des matchs sont disponibles, masquer le message "Pas de matchs"
    noMatchesElement.style.display = 'none';
    
    // Créer et ajouter les cartes de match
    matches.forEach(match => {
        const matchElement = createMatchElement(match);
        container.appendChild(matchElement);
    });
}

// Créer un élément de match à partir du template
function createMatchElement(match) {
    // Cloner le template
    const template = document.getElementById('match-template');
    const matchElement = template.content.cloneNode(true);
    const matchCard = matchElement.querySelector('.match-card');
    
    // Informations de base du match
    matchCard.querySelector('.match-id').textContent = `Match ID: ${match.match_id}`;
    
    // Afficher la durée et l'état du match avec une mise en forme améliorée
    const duration = match.duration || '0:00';
    
    // Utiliser la propriété is_draft fournie par l'API pour déterminer l'état du match
    const isDraft = match.is_draft === true;
    const matchState = isDraft ? ' (Draft)' : ' (En cours)';
    
    // Afficher la durée centralement et avec une taille plus grande
    matchCard.querySelector('.match-duration').textContent = `${duration}${matchState}`;
    
    // Nom de la ligue
    const leagueName = LEAGUE_NAMES[match.league_id] || `League ${match.league_id}`;
    matchCard.querySelector('.league-name').textContent = leagueName;
    
    // Information sur la série (BO3, BO5)
    if (match.match_type && match.match_type.description) {
        const seriesInfo = matchCard.querySelector('.series-info');
        if (seriesInfo) {
            // Ajout de l'état de la série si disponible (par exemple "0-1")
            let seriesText = match.match_type.description;
            if (match.match_type.series_current_value !== undefined && 
                match.match_type.series_max_value !== undefined) {
                seriesText += ` (${match.match_type.series_current_value}-${match.match_type.series_max_value})`;
            }
            seriesInfo.textContent = seriesText;
            seriesInfo.style.display = 'inline-block';
            
            // Ajout de l'indicateur "Game X sur Y" si c'est une série
            if (match.match_type.series_id && match.match_type.series_type > 0) {
                // Calcul du numéro de match actuel dans la série
                const currentGameNum = match.match_type.series_current_value + 1; // +1 car on commence à 0
                const totalGames = match.match_type.series_type == 1 ? 3 : 5; // 1 = Bo3, 2 = Bo5
                
                // Ajouter l'indicateur de map
                const mapIndicator = document.createElement('div');
                mapIndicator.className = 'map-indicator badge bg-danger my-3 p-3';
                mapIndicator.innerHTML = `<span class="fs-2 fw-bold">GAME ${currentGameNum} SUR ${totalGames}</span>`;
                
                // Insérer dans le conteneur prévu à cet effet
                const gameIndicatorContainer = matchCard.querySelector('.game-indicator-container');
                if (gameIndicatorContainer) {
                    gameIndicatorContainer.appendChild(mapIndicator);
                }
            }
        }
    }
    
    // Équipes (directement depuis l'API)
    const radiantTeam = match.radiant_team || {};
    const direTeam = match.dire_team || {};
    
    // Noms d'équipes (ou IDs si noms non disponibles)
    const radiantName = radiantTeam.team_name || `Team ${radiantTeam.team_id}`;
    const direName = direTeam.team_name || `Team ${direTeam.team_id}`;
    
    // Titre du match avec IDs des équipes
    const radiantTeamId = radiantTeam.team_id ? ` (ID: ${radiantTeam.team_id})` : '';
    const direTeamId = direTeam.team_id ? ` (ID: ${direTeam.team_id})` : '';
    matchCard.querySelector('.match-teams').textContent = `${radiantName}${radiantTeamId} vs ${direName}${direTeamId}`;
    
    // Scores des équipes
    matchCard.querySelector('.radiant-name').textContent = radiantName;
    matchCard.querySelector('.dire-name').textContent = direName;
    matchCard.querySelector('.radiant-score').textContent = match.radiant_score || 0;
    matchCard.querySelector('.dire-score').textContent = match.dire_score || 0;
    matchCard.querySelector('.total-kills').textContent = `Total: ${match.total_kills || 0} kills`;
    
    // Calculer et afficher le networth
    const radiantNetWorth = calculateTeamNetWorth(match, 'radiant');
    const direNetWorth = calculateTeamNetWorth(match, 'dire');
    
    if (radiantNetWorth > 0 || direNetWorth > 0) {
        // Enlever le style display:none de la section net-worth
        const netWorthSection = matchCard.querySelector('.net-worth-section');
        if (netWorthSection) {
            netWorthSection.style.display = 'block';
        }
        
        // Mettre à jour les valeurs de net worth
        const radiantNetWorthElem = matchCard.querySelector('.radiant-networth');
        const direNetWorthElem = matchCard.querySelector('.dire-networth');
        const radiantNameNwElem = matchCard.querySelector('.radiant-name-nw');
        const direNameNwElem = matchCard.querySelector('.dire-name-nw');
        
        if (radiantNetWorthElem) radiantNetWorthElem.textContent = `${radiantNetWorth} or`;
        if (direNetWorthElem) direNetWorthElem.textContent = `${direNetWorth} or`;
        if (radiantNameNwElem) radiantNameNwElem.textContent = radiantName;
        if (direNameNwElem) direNameNwElem.textContent = direName;
        
        // Calculer la différence de net worth
        const netWorthDiff = radiantNetWorth - direNetWorth;
        const netWorthDiffElement = matchCard.querySelector('.net-worth-diff');
        const progressBar = matchCard.querySelector('.nw-progress');
        
        if (netWorthDiffElement) {
            if (netWorthDiff > 0) {
                netWorthDiffElement.textContent = `Avantage ${radiantName}: ${Math.abs(netWorthDiff)} or`;
                if (progressBar) {
                    progressBar.className = 'progress-bar bg-success';
                    const percentage = Math.min(70, 50 + (netWorthDiff / (radiantNetWorth + direNetWorth)) * 100);
                    progressBar.style.width = percentage + '%';
                }
            } else if (netWorthDiff < 0) {
                netWorthDiffElement.textContent = `Avantage ${direName}: ${Math.abs(netWorthDiff)} or`;
                if (progressBar) {
                    progressBar.className = 'progress-bar bg-danger';
                    const percentage = Math.max(30, 50 - (Math.abs(netWorthDiff) / (radiantNetWorth + direNetWorth)) * 100);
                    progressBar.style.width = percentage + '%';
                }
            } else {
                netWorthDiffElement.textContent = "Avantage: Aucun";
                if (progressBar) {
                    progressBar.className = 'progress-bar bg-secondary';
                    progressBar.style.width = '50%';
                }
            }
        }
    } else {
        // Masquer la section si pas de données de net worth
        hideElement(matchCard.querySelector('.net-worth-section'));
        
        const netWorthDiffElement = matchCard.querySelector('.net-worth-diff');
        const progressBar = matchCard.querySelector('.nw-progress');
        
        if (netWorthDiffElement) {
            netWorthDiffElement.textContent = "Données indisponibles";
        }
        
        if (progressBar) {
            progressBar.className = 'progress-bar bg-secondary';
            progressBar.style.width = '50%';
        }
    }
    
    // Données de paris (simplifiées pour l'instant)
    matchCard.querySelector('.betting-link').style.display = 'none';
    matchCard.querySelector('.kill-threshold').textContent = 'N/A';
    matchCard.querySelector('.no-betting-data').style.display = 'block';
    
    // Masquer toutes les alertes
    hideElement(matchCard.querySelector('.alerts-section'));
    hideElement(matchCard.querySelector('.special-match'));
    matchCard.querySelector('.no-alerts').style.display = 'block';
    
    // Détails des équipes
    matchCard.querySelector('.radiant-name-details').textContent = radiantName;
    matchCard.querySelector('.dire-name-details').textContent = direName;
    
    // Style des en-têtes d'équipe
    matchCard.querySelector('.radiant-header').classList.add('bg-success', 'text-white');
    matchCard.querySelector('.dire-header').classList.add('bg-danger', 'text-white');
    
    // Simplifier l'affichage des joueurs
    const radiantPlayersElement = matchCard.querySelector('.radiant-players');
    const direPlayersElement = matchCard.querySelector('.dire-players');
    
    radiantPlayersElement.innerHTML = '';
    direPlayersElement.innerHTML = '';
    
    addSimplifiedPlayerInfo(radiantPlayersElement, 'Joueurs de l\'équipe Radiant');
    addSimplifiedPlayerInfo(direPlayersElement, 'Joueurs de l\'équipe Dire');
    
    // Horodatage de mise à jour
    matchCard.querySelector('.match-timestamp').textContent = match.timestamp || new Date().toLocaleTimeString();
    
    return matchElement;
}

// Fonction utilitaire pour masquer un élément
function hideElement(element) {
    if (element) {
        element.style.display = 'none';
    }
}

// Fonction utilitaire pour ajouter une info joueur simplifiée
function addSimplifiedPlayerInfo(container, text) {
    const item = document.createElement('li');
    item.className = 'list-group-item';
    item.textContent = text;
    container.appendChild(item);
}

// Fonction supprimée car nous n'utilisons plus la recherche par équipes

// Récupérer l'historique des matchs par ID de série
function fetchMatchBySeries(seriesId) {
    // Afficher l'indicateur de chargement
    document.getElementById('history-loading').style.display = 'block';
    document.getElementById('history-container').innerHTML = '';
    document.getElementById('no-history').style.display = 'none';
    
    // Mise à jour du message pour refléter la méthode de recherche
    document.getElementById('no-history').innerHTML = `
        <i class="fas fa-info-circle me-2"></i> 
        Recherche de l'historique par ID de série: ${seriesId}...
    `;
    
    // URL de l'API pour récupérer l'historique par ID de série
    const url = `/api/match-history?series_id=${seriesId}`;
    
    fetchHistoryData(url);
}

// Fonction commune pour récupérer les données d'historique de match
function fetchHistoryData(url) {
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('history-loading').style.display = 'none';
            
            if (data.success && data.matches && data.matches.length > 0) {
                currentHistoryMatches = data.matches;
                renderMatchHistory(data.matches);
            } else {
                // Aucun match trouvé
                document.getElementById('history-container').innerHTML = `
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        Aucun match historique trouvé avec ces critères.
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error("Erreur lors de la récupération de l'historique:", error);
            document.getElementById('history-loading').style.display = 'none';
            document.getElementById('history-container').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Erreur lors de la récupération de l'historique: ${error.message || 'Une erreur est survenue'} ${error.message}
                </div>
            `;
        });
}

// Afficher l'historique des matchs
function renderMatchHistory(matches) {
    const container = document.getElementById('history-container');
    container.innerHTML = '';
    
    // Trier les matchs par date (du plus récent au plus ancien)
    matches.sort((a, b) => new Date(b.date) - new Date(a.date));
    
    // Créer et ajouter les éléments de match
    matches.forEach(match => {
        const matchElement = createHistoryMatchElement(match);
        container.appendChild(matchElement);
    });
}

// Créer un élément de match historique
function createHistoryMatchElement(match) {
    // Cloner le template
    const template = document.getElementById('history-match-template');
    const matchElement = template.content.cloneNode(true);
    const matchCard = matchElement.querySelector('.history-match-card');
    
    // Informations de base du match
    matchCard.querySelector('.match-id').textContent = `Match ID: ${match.match_id}`;
    matchCard.querySelector('.match-date').textContent = new Date(match.date).toLocaleDateString();
    
    // Lien vers Dotabuff
    const dotabuffLink = matchCard.querySelector('.view-dotabuff');
    dotabuffLink.href = `https://www.dotabuff.com/matches/${match.match_id}`;
    
    // Afficher la durée
    matchCard.querySelector('.match-duration').textContent = match.duration;
    
    // Afficher les informations de série si disponibles
    if (match.match_type) {
        const historySeriesInfo = matchCard.querySelector('.history-series-info');
        if (historySeriesInfo) {
            historySeriesInfo.textContent = match.match_type;
            historySeriesInfo.style.display = 'inline-block';
        }
        
        // Si le match appartient à une série, ajouter l'indicateur de map si disponible
        if (match.series_id && match.game_number) {
            // Ajouter l'indicateur de map
            const mapIndicator = document.createElement('div');
            mapIndicator.className = 'map-indicator badge bg-danger my-3 p-3';
            mapIndicator.innerHTML = `<span class="fs-2 fw-bold">GAME ${match.game_number}</span>`;
            
            // Insérer dans le conteneur prévu à cet effet
            const gameIndicatorContainer = matchCard.querySelector('.game-indicator-container');
            if (gameIndicatorContainer) {
                gameIndicatorContainer.appendChild(mapIndicator);
            }
        }
    }
    
    // Équipes et scores
    const radiantName = match.radiant_team.name;
    const direName = match.dire_team.name;
    
    matchCard.querySelector('.match-teams').textContent = `${radiantName} vs ${direName}`;
    matchCard.querySelector('.radiant-name').textContent = radiantName;
    matchCard.querySelector('.dire-name').textContent = direName;
    matchCard.querySelector('.radiant-score').textContent = match.radiant_score;
    matchCard.querySelector('.dire-score').textContent = match.dire_score;
    matchCard.querySelector('.total-kills').textContent = `Total: ${match.total_kills} kills`;
    
    // Résultat du match
    const radiantResult = matchCard.querySelector('.radiant-result');
    const direResult = matchCard.querySelector('.dire-result');
    
    if (match.winner === 'radiant') {
        radiantResult.textContent = 'Victoire';
        radiantResult.classList.add('bg-success');
        direResult.textContent = 'Défaite';
        direResult.classList.add('bg-danger');
    } else {
        radiantResult.textContent = 'Défaite';
        radiantResult.classList.add('bg-danger');
        direResult.textContent = 'Victoire';
        direResult.classList.add('bg-success');
    }
    
    // Insights
    // 1. Rythme du match (kills/minute)
    const durationInMinutes = parseFloat(match.duration.split(':')[0]) + parseFloat(match.duration.split(':')[1])/60;
    const killRate = match.total_kills / durationInMinutes;
    matchCard.querySelector('.kill-rate').textContent = `${killRate.toFixed(1)} kills/min`;
    
    if (killRate > 1.3) {
        matchCard.querySelector('.pace-comment').textContent = "Rythme très agressif";
    } else if (killRate > 1.0) {
        matchCard.querySelector('.pace-comment').textContent = "Rythme standard";
    } else {
        matchCard.querySelector('.pace-comment').textContent = "Rythme lent, match défensif";
    }
    
    // 2. Différence de score
    const scoreDiff = Math.abs(match.radiant_score - match.dire_score);
    matchCard.querySelector('.kill-difference').textContent = `${scoreDiff} kills d'écart`;
    
    if (scoreDiff < 5) {
        matchCard.querySelector('.balance-comment').textContent = "Match très serré";
    } else if (scoreDiff < 15) {
        matchCard.querySelector('.balance-comment').textContent = "Avantage clair";
    } else {
        matchCard.querySelector('.balance-comment').textContent = "Victoire écrasante";
    }
    
    // 3. Durée du match
    if (durationInMinutes < 30) {
        matchCard.querySelector('.duration-category').textContent = "Match court";
        matchCard.querySelector('.duration-comment').textContent = "Fin rapide, possiblement dominée par une équipe";
    } else if (durationInMinutes < 45) {
        matchCard.querySelector('.duration-category').textContent = "Durée standard";
        matchCard.querySelector('.duration-comment').textContent = "Match typique avec phases de jeu équilibrées";
    } else {
        matchCard.querySelector('.duration-category').textContent = "Match long";
        matchCard.querySelector('.duration-comment').textContent = "Match défensif ou équilibré avec plusieurs retournements";
    }
    
    return matchElement;
}

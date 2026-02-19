// ============================================================================
// College Basketball Journal — Preact + HTM Application
// ============================================================================
import { h, render } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect, useRef, useMemo, useCallback } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';
const html = htm.bind(h);

// ============================================================================
// UTILITIES
// ============================================================================

const DEFUNCT_TEAM_CONFERENCES = { 'St. Francis (NY)': 'NEC' };

const STAT_THRESHOLDS = {
    ppg: { excellent: 20, good: 15, average: 10 },
    rpg: { excellent: 10, good: 7, average: 5 },
    apg: { excellent: 7, good: 5, average: 3 },
    fgPct: { excellent: 0.50, good: 0.45, average: 0.40 },
    threePct: { excellent: 0.40, good: 0.35, average: 0.30 },
};

function getTeamConference(teamName) {
    if (!teamName) return '';
    if (DEFUNCT_TEAM_CONFERENCES[teamName]) return DEFUNCT_TEAM_CONFERENCES[teamName];
    const checklist = DATA.conferenceChecklist || {};
    for (const [confName, confData] of Object.entries(checklist)) {
        if (confData.teams && confData.teams.some(t => t.team === teamName || t.name === teamName)) {
            return confName;
        }
    }
    const teams = DATA.teams || [];
    for (const team of teams) {
        if (team.Team === teamName && team.Conference) return team.Conference;
    }
    return '';
}

function getGameConference(game, teamType) {
    if (!game) return '';
    if (teamType === 'away' && game.AwayConf) return game.AwayConf;
    if (teamType === 'home' && game.HomeConf) return game.HomeConf;
    const teamName = teamType === 'away' ? game['Away Team'] : game['Home Team'];
    return getTeamConference(teamName);
}

function getSportsRefUrl(game) {
    if (game.SportsRefURL) return game.SportsRefURL;
    const dateSort = game.DateSort || '';
    const slug = game.HomeTeamSlug || '';
    if (dateSort && slug) {
        const formattedDate = dateSort.slice(0, 4) + '-' + dateSort.slice(4, 6) + '-' + dateSort.slice(6, 8);
        return `https://www.sports-reference.com/cbb/boxscores/${formattedDate}-${slug}.html`;
    }
    return '#';
}

function getPlayerSportsRefUrl(playerId) {
    if (!playerId) return '#';
    return `https://www.sports-reference.com/cbb/players/${playerId}.html`;
}

function getPlayerSportsRefLink(player) {
    const playerId = player['Player ID'] || player.player_id;
    if (!playerId) return '';
    if (player.HasSportsRefPage === false) {
        if (player.RealGM_URL) return { url: player.RealGM_URL, title: 'View on RealGM' };
        return '';
    }
    return { url: getPlayerSportsRefUrl(playerId), title: 'View on Sports Reference' };
}

function formatMinutes(mp) {
    if (mp == null || mp === '' || mp === '-') return '-';
    const num = parseFloat(mp);
    if (isNaN(num)) return '-';
    return Math.round(num);
}

function ordinal(n) {
    const s = ['th', 'st', 'nd', 'rd'];
    const v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

function getStatClass(value, thresholds) {
    if (!thresholds) return '';
    if (value >= thresholds.excellent) return 'stat-excellent';
    if (value >= thresholds.good) return 'stat-good';
    if (value >= thresholds.average) return 'stat-average';
    return '';
}

function parseDate(dateStr) {
    if (!dateStr) return null;
    return new Date(dateStr);
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    // Handle "Month Day, Year" format
    const parts = dateStr.split(' ');
    if (parts.length >= 3) {
        return `${parts[0].slice(0,3)} ${parts[1]} ${parts[2]}`;
    }
    return dateStr;
}

function downloadCSV(headers, rows, filename) {
    let csv = headers.join(',') + '\n';
    rows.forEach(row => {
        const values = headers.map(h => {
            let val = row[h] || '';
            if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
                val = `"${val.replace(/"/g, '""')}"`;
            }
            return val;
        });
        csv += values.join(',') + '\n';
    });
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

function getEspnLogoUrl(espnId) {
    if (!espnId) return null;
    return `https://a.espncdn.com/i/teamlogos/ncaa/500/${espnId}.png`;
}

// Normalize short/abbreviated team names to full checklist names
const TEAM_NAME_MAP = {
    'App State': 'Appalachian State',
    'Coastal': 'Coastal Carolina',
    'NC Central': 'North Carolina Central',
    'SC State': 'South Carolina State',
    'Arizona St': 'Arizona State',
    'Florida St': 'Florida State',
    'Boise St': 'Boise State',
    'Michigan St': 'Michigan State',
    'Kansas St': 'Kansas State',
    'Fresno St': 'Fresno State',
    'San Diego St': 'San Diego State',
    'Alabama St': 'Alabama State',
    'Wichita St': 'Wichita State',
    'Cleveland St': 'Cleveland State',
    'Long Beach St': 'Long Beach State',
    'Oklahoma St': 'Oklahoma State',
    'Oregon St': 'Oregon State',
    'Washington St': 'Washington State',
    'Colorado St': 'Colorado State',
    'Arkansas St': 'Arkansas State',
    'Illinois St': 'Illinois State',
    'Indiana St': 'Indiana State',
    'Idaho St': 'Idaho State',
    'Montana St': 'Montana State',
    'Portland St': 'Portland State',
    'Sacramento St': 'Sacramento State',
    'Kennesaw St': 'Kennesaw State',
    'Mississippi St': 'Mississippi State',
    'Missouri St': 'Missouri State',
    'Morehead St': 'Morehead State',
    'Morgan St': 'Morgan State',
    'Murray St': 'Murray State',
    'N Dakota St': 'North Dakota State',
    'S Dakota St': 'South Dakota State',
    'Tarleton St': 'Tarleton State',
    'Tennessee St': 'Tennessee State',
    'Texas St': 'Texas State',
    'Weber St': 'Weber State',
    'Youngstown St': 'Youngstown State',
    'Wright St': 'Wright State',
    'Norfolk St': 'Norfolk State',
    'Coppin St': 'Coppin State',
    'Delaware St': 'Delaware State',
    'New Mexico St': 'New Mexico State',
    'Jackson St': 'Jackson State',
    'Alcorn St': 'Alcorn State',
    'Jax State': 'Jacksonville State',
    'Georgia St': 'Georgia State',
    'Abilene Chrstn': 'Abilene Christian',
    'AR-Pine Bluff': 'Arkansas-Pine Bluff',
    'Bakersfield': 'Cal State Bakersfield',
    'Fullerton': 'Cal State Fullerton',
    'CSU Northridge': 'Cal State Northridge',
    'CA Baptist': 'California Baptist',
    'C Arkansas': 'Central Arkansas',
    'C Connecticut': 'Central Connecticut',
    'C Michigan': 'Central Michigan',
    'Charleston So': 'Charleston Southern',
    'Chicago St': 'Chicago State',
    'E Illinois': 'Eastern Illinois',
    'E Kentucky': 'Eastern Kentucky',
    'E Michigan': 'Eastern Michigan',
    'E Texas A&M': 'East Texas A&M',
    'E Washington': 'Eastern Washington',
    'ETSU': 'East Tennessee State',
    'FAU': 'Florida Atlantic',
    'FDU': 'Fairleigh Dickinson',
    'FGCU': 'Florida Gulf Coast',
    'G Washington': 'George Washington',
    'GA Southern': 'Georgia Southern',
    'Grambling': 'Grambling State',
    "Hawai'i": 'Hawaii',
    'Hou Christian': 'Houston Christian',
    'IU Indy': 'IU Indianapolis',
    'LMU': 'Loyola Marymount',
    'Long Island': 'LIU',
    'Loyola MD': 'Loyola (MD)',
    'MD Eastern': 'Maryland-Eastern Shore',
    'MTSU': 'Middle Tennessee',
    'Miami': 'Miami (FL)',
    'Miami OH': 'Miami (OH)',
    'Miss Valley St': 'Mississippi Valley State',
    'Mount St Marys': "Mount St. Mary's",
    'N Arizona': 'Northern Arizona',
    'N Colorado': 'Northern Colorado',
    'N Illinois': 'Northern Illinois',
    'N Kentucky': 'Northern Kentucky',
    "N'Western St": 'Northwestern State',
    'NC A&T': 'North Carolina A&T',
    'Pitt': 'Pittsburgh',
    'Prairie View': 'Prairie View A&M',
    'Purdue FW': 'Purdue Fort Wayne',
    'S Illinois': 'Southern Illinois',
    'SC Upstate': 'USC Upstate',
    'SE Louisiana': 'Southeastern Louisiana',
    'SE Missouri': 'Southeast Missouri State',
    'SF Austin': "Stephen F. Austin",
    'SIUE': 'SIU Edwardsville',
    'Saint Francis': 'St. Francis (PA)',
    "Saint Mary's": "Saint Mary's (CA)",
    "St John's": "St. John's",
    'St Bonaventure': 'St. Bonaventure',
    'St Thomas (MN)': 'St. Thomas',
    'San José St': 'San Jose State',
    'Santa Barbara': 'UC Santa Barbara',
    'Seattle U': 'Seattle',
    'So Indiana': 'Southern Indiana',
    'Boston U': 'Boston University',
    'Texas A&M-CC': 'Texas A&M-Corpus Christi',
    'UAlbany': 'Albany',
    'UL Monroe': 'Louisiana-Monroe',
    'UNC Wilmington': 'UNCW',
    'UT Rio Grande': 'UTRGV',
    'W Carolina': 'Western Carolina',
    'W Illinois': 'Western Illinois',
    'W Michigan': 'Western Michigan',
    'Western KY': 'Western Kentucky',
};

function normalizeTeamName(name) {
    return TEAM_NAME_MAP[name] || name;
}

function getTeamLogoUrl(teamName) {
    const normalized = normalizeTeamName(teamName);
    if (CUSTOM_LOGOS[normalized]) return CUSTOM_LOGOS[normalized];
    if (CUSTOM_LOGOS[teamName]) return CUSTOM_LOGOS[teamName];
    const checklist = DATA.conferenceChecklist || {};
    for (const confData of Object.values(checklist)) {
        const team = (confData.teams || []).find(t => t.team === normalized || t.team === teamName);
        if (team && team.espnId) return getEspnLogoUrl(team.espnId);
    }
    return null;
}

// Format game date/time from ISO to local time (for upcoming games)
function formatGameDateTime(isoDate, timeDetail) {
    try {
        if (timeDetail && timeDetail.includes(' - ')) {
            const parts = timeDetail.split(' - ');
            const datePart = parts[0];
            const timePart = parts[1];
            const dateMatch = datePart.match(/^(\d{1,2})\/(\d{1,2})$/);
            const timeMatch = timePart.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)\s*(EST|EDT|CST|CDT|MST|MDT|PST|PDT)?$/i);
            if (dateMatch && timeMatch) {
                const gameMonth = parseInt(dateMatch[1]) - 1;
                const gameDay = parseInt(dateMatch[2]);
                let hours = parseInt(timeMatch[1]);
                const minutes = parseInt(timeMatch[2]);
                const ampm = timeMatch[3].toUpperCase();
                const tz = (timeMatch[4] || 'EST').toUpperCase();
                if (ampm === 'PM' && hours !== 12) hours += 12;
                if (ampm === 'AM' && hours === 12) hours = 0;
                const baseDt = new Date(isoDate);
                let year = baseDt.getUTCFullYear();
                if (baseDt.getUTCMonth() === 11 && gameMonth === 0) year++;
                const tzOffsets = { 'EST': -5, 'EDT': -4, 'CST': -6, 'CDT': -5, 'MST': -7, 'MDT': -6, 'PST': -8, 'PDT': -7 };
                const offset = tzOffsets[tz] || -5;
                const utcMs = Date.UTC(year, gameMonth, gameDay, hours - offset, minutes);
                const localDt = new Date(utcMs);
                const dayOfWeek = localDt.toLocaleDateString('en-US', { weekday: 'short' });
                const monthStr = localDt.toLocaleDateString('en-US', { month: 'short' });
                const dayNum = localDt.getDate();
                const timeStr = localDt.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
                return `${dayOfWeek}, ${monthStr} ${dayNum} ${timeStr}`;
            }
        }
        const dt = new Date(isoDate);
        const hasTime = dt.getUTCHours() !== 0 || dt.getUTCMinutes() !== 0;
        const options = { weekday: 'short', month: 'short', day: 'numeric' };
        const dateStr = dt.toLocaleDateString('en-US', options);
        if (hasTime) {
            const timeStr = dt.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
            return `${dateStr} ${timeStr}`;
        }
        return dateStr;
    } catch (e) { return isoDate; }
}

function getActualGameDate(isoDate, timeDetail) {
    if (timeDetail && timeDetail.includes(' - ')) {
        const parts = timeDetail.split(' - ');
        const dateMatch = parts[0].match(/^(\d{1,2})\/(\d{1,2})$/);
        if (dateMatch) {
            const gameMonth = parseInt(dateMatch[1]) - 1;
            const gameDay = parseInt(dateMatch[2]);
            const baseDt = new Date(isoDate);
            let year = baseDt.getUTCFullYear();
            if (baseDt.getUTCMonth() === 11 && gameMonth === 0) year++;
            return new Date(year, gameMonth, gameDay);
        }
    }
    return new Date(isoDate);
}

function formatMatchupWithRanks(game) {
    const awayRank = game.awayRank ? `#${game.awayRank} ` : '';
    const homeRank = game.homeRank ? `#${game.homeRank} ` : '';
    return `${awayRank}${game.awayTeam || game.away || ''} @ ${homeRank}${game.homeTeam || game.home || ''}`;
}

function haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 3959;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon/2) * Math.sin(dLon/2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// ============================================================================
// ROUTE LEGACY MAP + PARSING
// ============================================================================

const LEGACY_ROUTES = {
    'games': 'games',
    'players': 'people',
    'milestones': 'people/achievements',
    'future-pros': 'people/future-pros',
    'teams': 'games/teams',
    'matchups': 'games/matchups',
    'venues': 'places',
    'calendar': 'games/calendar',
    'conferences': 'places/conferences',
    'map': 'places/map',
    'upcoming': 'places/upcoming',
    'leaders': 'people/leaders',
    'compare': 'people',
    'records': 'games/records',
};

function parseRoute() {
    const hash = window.location.hash.slice(1) || 'home';
    const [path, queryString] = hash.split('?');
    const params = {};
    if (queryString) {
        queryString.split('&').forEach(pair => {
            const [key, value] = pair.split('=');
            params[key] = decodeURIComponent(value || '');
        });
    }
    // Handle legacy routes
    const segments = path.split('/');
    if (LEGACY_ROUTES[segments[0]] && !['home','games','people','places'].includes(segments[0])) {
        const newPath = LEGACY_ROUTES[segments[0]];
        // Handle legacy sub params
        if (params.sub) {
            return { section: newPath.split('/')[0], sub: params.sub, params };
        }
        const parts = newPath.split('/');
        return { section: parts[0], sub: parts[1] || '', params };
    }
    return { section: segments[0] || 'home', sub: segments[1] || '', params };
}

function updateRoute(section, sub = '', params = {}) {
    let hash = section;
    if (sub) hash += '/' + sub;
    const paramPairs = Object.entries(params).filter(([k, v]) => v);
    if (paramPairs.length > 0) {
        hash += '?' + paramPairs.map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&');
    }
    history.pushState(null, '', '#' + hash);
}

// ============================================================================
// COMPUTE GAME MILESTONES (port verbatim from original)
// ============================================================================

const MILESTONE_COUNTS = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 75, 100, 150, 200];
let gameMilestones = {};

function computeGameMilestones() {
    const allGames = (DATA.games || []).slice().sort((a, b) => {
        const dateA = a.DateSort || '';
        const dateB = b.DateSort || '';
        const dateCompare = dateA.localeCompare(dateB);
        if (dateCompare !== 0) return dateCompare;
        const timeA = a.TimeSort || '';
        const timeB = b.TimeSort || '';
        if (timeA && timeB && timeA !== timeB) return timeA.localeCompare(timeB);
        const genderA = a.Gender || 'M';
        const genderB = b.Gender || 'M';
        if (genderA !== genderB) return genderA === 'W' ? -1 : 1;
        return (a.GameID || '').localeCompare(b.GameID || '');
    });

    const teamCounts = {};
    const teamRecords = {};
    const venueCounts = {};
    const matchupsSeen = {};
    const confMatchupCounts = {};
    const confTeamCounts = {};
    const playerTeams = {};
    let venueOrder = [];
    const confTeamsSeen = {};
    const confVenuesSeen = {};
    const confCompleted = {};
    const statesSeen = new Set();
    let stateOrder = [];

    let currentStreak = 0;
    let lastGameDate = null;
    let maxStreak = 0;
    const streakHistory = [];

    gameMilestones = {};

    const conferenceTeamCounts = {};
    const checklist = DATA.conferenceChecklist || {};
    for (const [confName, confData] of Object.entries(checklist)) {
        if (confName === 'All D1' || confName === 'Historical/Other') continue;
        conferenceTeamCounts[confName] = confData.totalTeams || 0;
    }

    const GAME_MILESTONES = [1, 10, 25, 50, 75, 100, 150, 200, 250, 500];
    let gameCount = 0;

    const D1_MILESTONES = [1, 10, 25, 50, 75, 100, 150, 200, 250, 500];
    let d1GameCount = 0;
    let d1VenueCount = 0;
    const d1VenuesSeen = new Set();

    const D1_TEAM_MILESTONES = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100];
    const d1TeamsSeen = { M: new Set(), W: new Set() };

    const actualD1Teams = new Set();
    const teamAliases = DATA.teamAliases || {};
    const reverseAliases = {};
    for (const [alias, canonical] of Object.entries(teamAliases)) {
        if (!reverseAliases[canonical]) reverseAliases[canonical] = new Set();
        reverseAliases[canonical].add(alias);
        reverseAliases[canonical].add(canonical);
    }

    for (const [confName, confData] of Object.entries(checklist)) {
        if (confName === 'All D1' || confName === 'Historical/Other') continue;
        (confData.teams || []).forEach(t => {
            if (t.team) {
                actualD1Teams.add(t.team);
                const canonical = teamAliases[t.team];
                if (canonical) actualD1Teams.add(canonical);
                const aliases = reverseAliases[t.team];
                if (aliases) aliases.forEach(a => actualD1Teams.add(a));
            }
        });
    }

    allGames.forEach((game, index) => {
        const gameId = game.GameID || `game-${index}`;
        const awayTeam = game['Away Team'] || '';
        const homeTeam = game['Home Team'] || '';
        const venue = game.Venue || '';
        const city = game.City || '';
        const state = game.State || '';
        const gender = game.Gender || 'M';
        const division = game.Division || 'D1';
        const dateSort = game.DateSort || '';
        const awayConf = getGameConference(game, 'away');
        const homeConf = getGameConference(game, 'home');

        gameMilestones[gameId] = { badges: [], gameNumber: index + 1 };

        // Game count milestone
        gameCount++;
        if (GAME_MILESTONES.includes(gameCount)) {
            gameMilestones[gameId].badges.push({
                type: 'game-count',
                text: `Game #${gameCount}`,
                title: `${ordinal(gameCount)} game attended`
            });
        }

        // D1 game count
        if (division === 'D1') {
            d1GameCount++;
            if (D1_MILESTONES.includes(d1GameCount)) {
                gameMilestones[gameId].badges.push({
                    type: 'd1-game',
                    text: `D1 #${d1GameCount}`,
                    title: `${ordinal(d1GameCount)} D1 game attended`
                });
            }
        }

        // Streak tracking
        if (lastGameDate && dateSort) {
            const lastDate = new Date(lastGameDate.slice(0,4) + '-' + lastGameDate.slice(4,6) + '-' + lastGameDate.slice(6,8));
            const thisDate = new Date(dateSort.slice(0,4) + '-' + dateSort.slice(4,6) + '-' + dateSort.slice(6,8));
            const diffDays = Math.round((thisDate - lastDate) / (1000 * 60 * 60 * 24));
            if (diffDays === 0) {
                // Same day, streak continues
            } else if (diffDays === 1) {
                currentStreak++;
            } else {
                if (currentStreak >= 2) streakHistory.push(currentStreak);
                maxStreak = Math.max(maxStreak, currentStreak);
                currentStreak = 1;
            }
        } else {
            currentStreak = 1;
        }
        if (dateSort) lastGameDate = dateSort;

        if (currentStreak >= 2) {
            gameMilestones[gameId].badges.push({
                type: 'streak',
                text: `${currentStreak}-Day Streak`,
                title: `${currentStreak} consecutive days attending games`
            });
        }

        // State tracking
        if (state && !statesSeen.has(state)) {
            statesSeen.add(state);
            stateOrder.push(state);
            gameMilestones[gameId].badges.push({
                type: 'new-state',
                text: `New State: ${state}`,
                title: `${ordinal(statesSeen.size)} state visited`
            });
        }

        // Venue milestones
        if (venue) {
            if (!venueCounts[venue]) {
                venueCounts[venue] = 0;
                venueOrder.push(venue);
                const venueNum = venueOrder.length;
                if (MILESTONE_COUNTS.includes(venueNum)) {
                    gameMilestones[gameId].badges.push({
                        type: 'venue-count',
                        text: `${ordinal(venueNum)} Venue`,
                        title: `${ordinal(venueNum)} unique venue visited: ${venue}`
                    });
                }
                // D1 venue tracking
                if (division === 'D1' && !d1VenuesSeen.has(venue)) {
                    d1VenuesSeen.add(venue);
                    d1VenueCount++;
                }
            }
            venueCounts[venue]++;
            if (venueCounts[venue] > 1 && MILESTONE_COUNTS.includes(venueCounts[venue])) {
                gameMilestones[gameId].badges.push({
                    type: 'venue-visit',
                    text: `${venue} #${venueCounts[venue]}`,
                    title: `${ordinal(venueCounts[venue])} game at ${venue}`
                });
            }
        }

        // Team milestones
        [awayTeam, homeTeam].forEach(team => {
            if (!team) return;
            const teamKey = `${team}|${gender}`;
            if (!teamCounts[teamKey]) {
                teamCounts[teamKey] = 0;
                // First time seeing this team
                gameMilestones[gameId].badges.push({
                    type: 'new-team',
                    text: `New: ${team}${gender === 'W' ? ' (W)' : ''}`,
                    title: `First time seeing ${team}${gender === 'W' ? ' (Women)' : ''}`
                });

                // D1 team tracking
                if (actualD1Teams.has(team)) {
                    d1TeamsSeen[gender].add(team);
                    const count = d1TeamsSeen[gender].size;
                    if (D1_TEAM_MILESTONES.includes(count)) {
                        gameMilestones[gameId].badges.push({
                            type: 'd1-team',
                            text: `${count} D1 Teams${gender === 'W' ? ' (W)' : ''}`,
                            title: `Seen ${count} unique D1 ${gender === 'W' ? "women's" : "men's"} teams`
                        });
                    }
                }
            }
            teamCounts[teamKey]++;
            if (teamCounts[teamKey] > 1 && MILESTONE_COUNTS.includes(teamCounts[teamKey])) {
                gameMilestones[gameId].badges.push({
                    type: 'team-visit',
                    text: `${team} #${teamCounts[teamKey]}${gender === 'W' ? ' (W)' : ''}`,
                    title: `${ordinal(teamCounts[teamKey])} time seeing ${team}`
                });
            }

            // Track W-L record
            if (!teamRecords[teamKey]) teamRecords[teamKey] = { wins: 0, losses: 0 };
            const awayScore = game['Away Score'] || 0;
            const homeScore = game['Home Score'] || 0;
            const isWinner = (team === awayTeam && awayScore > homeScore) || (team === homeTeam && homeScore > awayScore);
            if (isWinner) teamRecords[teamKey].wins++;
            else teamRecords[teamKey].losses++;
        });

        // Conference tracking
        [{ conf: awayConf, team: awayTeam }, { conf: homeConf, team: homeTeam }].forEach(({ conf, team }) => {
            if (!conf || conf === 'Historical/Other') return;
            const confGenderKey = `${conf}|${gender}`;
            if (!confTeamsSeen[confGenderKey]) confTeamsSeen[confGenderKey] = new Set();
            const wasNew = !confTeamsSeen[confGenderKey].has(team);
            confTeamsSeen[confGenderKey].add(team);

            if (!confTeamCounts[conf]) {
                confTeamCounts[conf] = 0;
                gameMilestones[gameId].badges.push({
                    type: 'new-conf',
                    text: `New conf: ${conf}`,
                    title: `First ${conf} team seen`
                });
            }
            if (wasNew) confTeamCounts[conf]++;

            // Check conference completion
            const totalTeams = conferenceTeamCounts[conf] || 0;
            if (totalTeams > 0 && confTeamsSeen[confGenderKey].size >= totalTeams && !confCompleted[confGenderKey]) {
                confCompleted[confGenderKey] = true;
                gameMilestones[gameId].badges.push({
                    type: 'conf-complete',
                    text: `${conf} Complete${gender === 'W' ? ' (W)' : ''}!`,
                    title: `Seen all ${totalTeams} ${conf} teams${gender === 'W' ? " (Women's)" : ''}`
                });
            }
        });

        // Matchup tracking
        if (awayTeam && homeTeam) {
            const matchupKey = [awayTeam, homeTeam].sort().join('|') + `|${gender}`;
            if (!matchupsSeen[matchupKey]) {
                matchupsSeen[matchupKey] = true;
                gameMilestones[gameId].badges.push({
                    type: 'new-matchup',
                    text: `New matchup`,
                    title: `First time seeing ${awayTeam} vs ${homeTeam}${gender === 'W' ? ' (W)' : ''}`
                });
            }
        }

        // Conference matchup tracking
        if (awayConf && homeConf && awayConf !== homeConf) {
            const confKey = [awayConf, homeConf].sort().join('|');
            if (!confMatchupCounts[confKey]) {
                confMatchupCounts[confKey] = 0;
                gameMilestones[gameId].badges.push({
                    type: 'conf-matchup',
                    text: `${awayConf} vs ${homeConf}`,
                    title: `First ${awayConf} vs ${homeConf} game`
                });
            }
            confMatchupCounts[confKey]++;
        }

        // Conference venue tracking
        if (venue && homeConf && homeConf !== 'Historical/Other') {
            const confVenueKey = `${homeConf}|${venue}`;
            if (!confVenuesSeen[confVenueKey]) {
                confVenuesSeen[confVenueKey] = true;
            }
        }

        // Track players on new teams (transfers)
        const gamePlayers = (DATA.playerGames || []).filter(pg => pg.game_id === gameId);
        gamePlayers.forEach(pg => {
            const playerId = pg.player_id || pg.player;
            const playerName = pg.player;
            const playerTeam = pg.team;
            const realgmPrevSchools = pg.realgm_previous_schools || [];
            if (!playerId || !playerTeam) return;

            if (!playerTeams[playerId]) {
                playerTeams[playerId] = { name: playerName, teams: new Set() };
                if (realgmPrevSchools.length > 0) {
                    const currentDateSort = game.DateSort || '';
                    realgmPrevSchools.forEach(prevSchool => {
                        const hasPlayerAtSchoolBefore = (DATA.playerGames || []).some(pg2 => {
                            const idMatch = playerId && pg2.player_id === playerId;
                            const nameMatch = !playerId && pg2.player && pg2.player.toLowerCase() === playerName.toLowerCase();
                            return (idMatch || nameMatch) &&
                                pg2.team === prevSchool &&
                                (pg2.date_yyyymmdd || '') < currentDateSort;
                        });
                        if (hasPlayerAtSchoolBefore) playerTeams[playerId].teams.add(prevSchool);
                    });
                }
            }

            if (playerTeams[playerId].teams.size > 0 && !playerTeams[playerId].teams.has(playerTeam)) {
                const prevTeams = [...playerTeams[playerId].teams].join(', ');
                gameMilestones[gameId].badges.push({
                    type: 'transfer',
                    text: `${playerName} (${prevTeams} → ${playerTeam})`,
                    title: `First time seeing ${playerName} with ${playerTeam} (previously: ${prevTeams})`
                });
            }
            playerTeams[playerId].teams.add(playerTeam);
        });
    });

    // Finalize streak tracking
    if (currentStreak >= 2) streakHistory.push(currentStreak);
    maxStreak = Math.max(maxStreak, currentStreak);

    window.badgeTrackingData = {
        confTeamsSeen, confCompleted, conferenceTeamCounts, venueOrder,
        teamCounts, matchupsSeen, statesSeen, stateOrder, maxStreak,
        streakHistory, d1TeamsSeen
    };
}

// Run milestone computation
try { computeGameMilestones(); } catch(e) { console.error('computeGameMilestones:', e); }

// ============================================================================
// SHARED COMPONENTS
// ============================================================================

function Toast({ message, onDone }) {
    useEffect(() => {
        if (message) {
            const timer = setTimeout(onDone, 3000);
            return () => clearTimeout(timer);
        }
    }, [message]);
    if (!message) return null;
    return html`<div class="toast show">${message}</div>`;
}

function StatBox({ label, value, icon }) {
    return html`
        <div class="stat-box">
            ${icon && html`<div class="stat-icon">${icon}</div>`}
            <div class="stat-number">${value}</div>
            <div class="stat-label">${label}</div>
        </div>
    `;
}

function Card({ children, className = '', onClick }) {
    return html`
        <div class="card ${className}" onClick=${onClick}>
            ${children}
        </div>
    `;
}

function Badge({ type, text, title }) {
    // Shorten badge text for cleaner display
    const BADGE_ICONS = {
        'game-count': '#',
        'd1-game': '#',
        'streak': '🔥',
        'new-state': '📍',
        'venue-count': '🏟',
        'venue-visit': '🏟',
        'new-team': '👀',
        'team-visit': '👀',
        'd1-team': '🏀',
        'new-conf': '🏅',
        'conf-complete': '✅',
        'new-matchup': '⚔️',
        'conf-matchup': '🤝',
        'transfer': '🔄',
        'upset': '🚨',
    };
    const icon = BADGE_ICONS[type] || '';
    return html`<span class="milestone-badge badge-${type}" title=${title}>${icon ? icon + ' ' : ''}${text}</span>`;
}

function EmptyState({ icon = '🏀', title = 'No data found', message = 'Try adjusting your filters' }) {
    return html`
        <div class="empty-state">
            <div class="empty-state-icon">${icon}</div>
            <h3>${title}</h3>
            <p>${message}</p>
        </div>
    `;
}

function Pagination({ page, pageSize, total, onPageChange }) {
    const totalPages = Math.ceil(total / pageSize);
    if (totalPages <= 1) return null;
    const pages = [];
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= page - 2 && i <= page + 2)) {
            pages.push(i);
        } else if (pages[pages.length - 1] !== '...') {
            pages.push('...');
        }
    }
    return html`
        <div class="pagination">
            <button disabled=${page === 1} onClick=${() => onPageChange(page - 1)}>Prev</button>
            ${pages.map(p => p === '...'
                ? html`<span class="pagination-ellipsis">...</span>`
                : html`<button class=${p === page ? 'active' : ''} onClick=${() => onPageChange(p)}>${p}</button>`
            )}
            <button disabled=${page === totalPages} onClick=${() => onPageChange(page + 1)}>Next</button>
            <span class="pagination-info">${total} items</span>
        </div>
    `;
}

function ViewToggle({ view, onToggle }) {
    return html`
        <div class="view-toggle">
            <button class=${view === 'card' ? 'active' : ''} onClick=${() => onToggle('card')} title="Card View">▦</button>
            <button class=${view === 'table' ? 'active' : ''} onClick=${() => onToggle('table')} title="Table View">☰</button>
        </div>
    `;
}

function SubNav({ items, active, onSelect }) {
    return html`
        <div class="sub-nav">
            ${items.map(item => html`
                <button
                    class=${'sub-tab' + (active === item.id ? ' active' : '')}
                    onClick=${() => onSelect(item.id)}
                >${item.label}</button>
            `)}
        </div>
    `;
}

function ScoreCard({ game, onClick }) {
    const awayScore = game['Away Score'] || 0;
    const homeScore = game['Home Score'] || 0;
    const awayWon = awayScore > homeScore;
    const linescore = game.Linescore || {};
    const otPeriods = linescore.away?.OT?.length || 0;
    const otText = otPeriods > 0 ? ` (${otPeriods > 1 ? otPeriods + 'OT' : 'OT'})` : '';
    const milestones = gameMilestones[game.GameID] || { badges: [] };
    const genderTag = game.Gender === 'W' ? ' (W)' : '';

    return html`
        <div class="score-card" onClick=${onClick}>
            <div class="score-card-date">${formatDate(game.Date)}${genderTag}</div>
            <div class="score-card-teams">
                <div class=${'score-card-team' + (awayWon ? ' winner' : '')}>
                    ${game.AwayRank ? html`<span class="ap-rank">#${game.AwayRank}</span>` : null}
                    <span class="team-name">${game['Away Team']}</span>
                    <span class="team-score">${awayScore}</span>
                </div>
                <div class=${'score-card-team' + (!awayWon ? ' winner' : '')}>
                    ${game.HomeRank ? html`<span class="ap-rank">#${game.HomeRank}</span>` : null}
                    <span class="team-name">${game['Home Team']}</span>
                    <span class="team-score">${homeScore}</span>
                </div>
            </div>
            <div class="score-card-venue">${game.Venue}${otText}</div>
            ${milestones.badges.length > 0 ? html`
                <div class="score-card-badges">
                    ${milestones.badges.slice(0, 3).map(b => html`<${Badge} ...${b} />`)}
                    ${milestones.badges.length > 3 ? html`<span class="badge-more">+${milestones.badges.length - 3}</span>` : null}
                </div>
            ` : null}
        </div>
    `;
}

function FilterBar({ children }) {
    return html`<div class="filter-bar">${children}</div>`;
}

function QuickFilters({ filters, active, onSelect }) {
    return html`
        <div class="quick-filters">
            ${filters.map(f => html`
                <button
                    class=${'quick-filter' + (active === f.id ? ' active' : '')}
                    onClick=${() => onSelect(f.id)}
                >${f.label}${f.count != null ? html` <span class="filter-count">${f.count}</span>` : null}</button>
            `)}
        </div>
    `;
}

function Modal({ id, active, onClose, title, children }) {
    const overlayRef = useRef();
    useEffect(() => {
        if (active) {
            document.body.style.overflow = 'hidden';
            const handleKey = (e) => { if (e.key === 'Escape') onClose(); };
            document.addEventListener('keydown', handleKey);
            return () => {
                document.body.style.overflow = '';
                document.removeEventListener('keydown', handleKey);
            };
        }
    }, [active]);

    if (!active) return null;
    return html`
        <div class="modal-overlay active" ref=${overlayRef} onClick=${(e) => { if (e.target === overlayRef.current) onClose(); }}>
            <div class="modal" role="dialog" aria-modal="true" aria-labelledby="${id}-title">
                <div class="modal-header">
                    <h3 id="${id}-title">${title}</h3>
                    <button class="modal-close" onClick=${onClose} aria-label="Close">×</button>
                </div>
                <div class="modal-body">
                    ${children}
                </div>
            </div>
        </div>
    `;
}

// ============================================================================
// HEADER & NAV
// ============================================================================

function Header({ onSearch, toast, setToast }) {
    const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState(null);
    const searchRef = useRef();
    const searchTimeout = useRef();

    useEffect(() => {
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }, [theme]);

    const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark');

    const handleSearch = useCallback((e) => {
        const query = e.target.value;
        setSearchQuery(query);
        if (searchTimeout.current) clearTimeout(searchTimeout.current);
        if (query.trim().length < 2) { setSearchResults(null); return; }
        searchTimeout.current = setTimeout(() => {
            const q = query.trim().toLowerCase();
            const results = { games: [], players: [], teams: [], venues: [] };
            const max = 5;
            (DATA.games || []).forEach(game => {
                if (results.games.length >= max) return;
                const str = `${game['Away Team']} ${game['Home Team']} ${game.Date} ${game.Venue}`.toLowerCase();
                if (str.includes(q)) results.games.push(game);
            });
            (DATA.players || []).forEach(player => {
                if (results.players.length >= max) return;
                const str = `${player.Player || ''} ${player.Team || ''}`.toLowerCase();
                if (str.includes(q)) results.players.push(player);
            });
            (DATA.teams || []).forEach(team => {
                if (results.teams.length >= max) return;
                if ((team.Team || '').toLowerCase().includes(q)) results.teams.push(team);
            });
            const venuesSeen = new Set();
            (DATA.games || []).forEach(game => {
                if (results.venues.length >= max) return;
                const v = game.Venue;
                if (v && !venuesSeen.has(v) && v.toLowerCase().includes(q)) {
                    venuesSeen.add(v);
                    results.venues.push({ Venue: v, City: game.City, State: game.State });
                }
            });
            const total = results.games.length + results.players.length + results.teams.length + results.venues.length;
            setSearchResults(total > 0 ? results : { empty: true });
        }, 150);
    }, []);

    const selectResult = (type, id) => {
        setSearchResults(null);
        setSearchQuery('');
        onSearch(type, id);
    };

    useEffect(() => {
        const handleClick = (e) => {
            if (searchRef.current && !searchRef.current.contains(e.target)) setSearchResults(null);
        };
        document.addEventListener('click', handleClick);
        return () => document.removeEventListener('click', handleClick);
    }, []);

    const shareView = () => {
        navigator.clipboard.writeText(window.location.href)
            .then(() => setToast('Link copied to clipboard!'))
            .catch(() => setToast('Could not copy link'));
    };

    return html`
        <header class="header">
            <div class="header-inner">
                <div class="header-brand">
                    <h1 class="header-title" onClick=${() => { window.location.hash = '#home'; }}>College Basketball Journal</h1>
                </div>
                <div class="global-search-container" ref=${searchRef}>
                    <input
                        type="text"
                        class="global-search"
                        placeholder="Search games, players, teams..."
                        value=${searchQuery}
                        onInput=${handleSearch}
                        onKeyDown=${(e) => {
                            if (e.key === 'Escape') { setSearchResults(null); e.target.blur(); }
                            if (e.key === 'Enter') {
                                const first = document.querySelector('.search-result-item');
                                if (first) first.click();
                            }
                        }}
                        onFocus=${() => { if (searchQuery.length >= 2) handleSearch({ target: { value: searchQuery } }); }}
                    />
                    ${searchResults && html`
                        <div class="search-results" style="display:block">
                            ${searchResults.empty ? html`<div class="search-no-results">No results found</div>` : html`
                                ${searchResults.games?.length > 0 && html`
                                    <div class="search-result-section">
                                        <div class="search-result-header">Games</div>
                                        ${searchResults.games.map(g => html`
                                            <div class="search-result-item" onClick=${() => selectResult('game', g.GameID)}>
                                                <span class="search-result-icon">🏀</span>
                                                <div class="search-result-text">
                                                    <div class="search-result-title">${g['Away Team']} @ ${g['Home Team']}</div>
                                                    <div class="search-result-subtitle">${g.Date} - ${g['Away Score']}-${g['Home Score']}</div>
                                                </div>
                                            </div>
                                        `)}
                                    </div>
                                `}
                                ${searchResults.players?.length > 0 && html`
                                    <div class="search-result-section">
                                        <div class="search-result-header">Players</div>
                                        ${searchResults.players.map(p => html`
                                            <div class="search-result-item" onClick=${() => selectResult('player', p['Player ID'] || p.Player)}>
                                                <span class="search-result-icon">👤</span>
                                                <div class="search-result-text">
                                                    <div class="search-result-title">${p.Player}</div>
                                                    <div class="search-result-subtitle">${p.Team} - ${(p.PPG || 0).toFixed(1)} PPG</div>
                                                </div>
                                            </div>
                                        `)}
                                    </div>
                                `}
                                ${searchResults.teams?.length > 0 && html`
                                    <div class="search-result-section">
                                        <div class="search-result-header">Teams</div>
                                        ${searchResults.teams.map(t => html`
                                            <div class="search-result-item" onClick=${() => selectResult('team', t.Team)}>
                                                <span class="search-result-icon">🏆</span>
                                                <div class="search-result-text">
                                                    <div class="search-result-title">${t.Team}</div>
                                                    <div class="search-result-subtitle">${t.Conference || ''} - ${t.Wins || 0}W ${t.Losses || 0}L</div>
                                                </div>
                                            </div>
                                        `)}
                                    </div>
                                `}
                                ${searchResults.venues?.length > 0 && html`
                                    <div class="search-result-section">
                                        <div class="search-result-header">Venues</div>
                                        ${searchResults.venues.map(v => html`
                                            <div class="search-result-item" onClick=${() => selectResult('venue', v.Venue)}>
                                                <span class="search-result-icon">🏟️</span>
                                                <div class="search-result-text">
                                                    <div class="search-result-title">${v.Venue}</div>
                                                    <div class="search-result-subtitle">${v.City || ''}, ${v.State || ''}</div>
                                                </div>
                                            </div>
                                        `)}
                                    </div>
                                `}
                            `}
                        </div>
                    `}
                </div>
                <div class="header-actions">
                    <button class="header-btn" onClick=${shareView} title="Share this view">↗</button>
                    <button class="header-btn theme-toggle" onClick=${toggleTheme} title="Toggle theme">
                        ${theme === 'dark' ? '☀' : '🌙'}
                    </button>
                </div>
            </div>
        </header>
    `;
}

function Nav({ section, onChange }) {
    const items = [
        { id: 'home', label: 'Home', icon: '⌂' },
        { id: 'games', label: 'Games', icon: '🏀' },
        { id: 'people', label: 'People', icon: '👥' },
        { id: 'places', label: 'Places', icon: '📍' },
    ];
    return html`
        <nav class="nav" role="tablist">
            <div class="nav-inner">
                ${items.map(item => html`
                    <button
                        class=${'nav-item' + (section === item.id ? ' active' : '')}
                        onClick=${() => onChange(item.id)}
                        role="tab"
                        aria-selected=${section === item.id}
                    >
                        <span class="nav-icon">${item.icon}</span>
                        <span class="nav-label">${item.label}</span>
                    </button>
                `)}
            </div>
        </nav>
        <nav class="bottom-nav">
            ${items.map(item => html`
                <button
                    class=${'bottom-nav-item' + (section === item.id ? ' active' : '')}
                    onClick=${() => onChange(item.id)}
                >
                    <span class="bottom-nav-icon">${item.icon}</span>
                    <span class="bottom-nav-label">${item.label}</span>
                </button>
            `)}
        </nav>
    `;
}

// ============================================================================
// HOME SECTION
// ============================================================================

function HomeSection({ onNavigate, showGameDetail, showPlayerDetail }) {
    const summary = DATA.summary || {};
    const games = DATA.games || [];
    const recentGames = useMemo(() =>
        [...games].sort((a, b) => (b.DateSort || '').localeCompare(a.DateSort || '')).slice(0, 5),
        [games]
    );

    // On This Day
    const onThisDay = useMemo(() => {
        const today = new Date();
        const month = today.getMonth();
        const day = today.getDate();
        return games.filter(g => {
            const d = new Date(g.Date);
            return d.getMonth() === month && d.getDate() === day;
        });
    }, [games]);

    // Future Pros Spotlight (top 5 by pro games)
    const futureProsSpotlight = useMemo(() => {
        const fp = (DATA.players || []).filter(p => p.NBA || p.WNBA || p.International);
        return [...fp]
            .map(p => ({ ...p, proGames: p.Proballers_Games || (p.NBA_Games || 0) + (p.WNBA_Games || 0) }))
            .sort((a, b) => b.proGames - a.proGames)
            .slice(0, 5);
    }, []);

    return html`
        <section class="home-section">
            <div class="hero-stats">
                <${StatBox} label="Games" value=${summary.totalGames || 0} icon="🏀" />
                <${StatBox} label="Players" value=${summary.totalPlayers || 0} icon="👥" />
                <${StatBox} label="Teams" value=${summary.totalTeams || 0} icon="🏆" />
                <${StatBox} label="Venues" value=${summary.totalVenues || 0} icon="🏟️" />
                <${StatBox} label="Points" value=${(summary.totalPoints || 0).toLocaleString()} icon="📊" />
                <${StatBox} label="Ranked Matchups" value=${summary.rankedMatchups || 0} icon="⭐" />
                <${StatBox} label="Upsets" value=${summary.upsets || 0} icon="🔥" />
                <${StatBox} label="Future Pros" value=${summary.futurePros || 0} icon="🌟" />
            </div>

            <div class="home-grid">
                <div class="home-column">
                    <h2 class="section-title">Recent Games</h2>
                    <div class="recent-games">
                        ${recentGames.map(g => html`
                            <${ScoreCard} game=${g} onClick=${() => showGameDetail(g.GameID)} />
                        `)}
                    </div>
                    ${recentGames.length > 0 && html`
                        <button class="link-btn" onClick=${() => onNavigate('games')}>View all games →</button>
                    `}
                </div>

                <div class="home-column">
                    ${onThisDay.length > 0 && html`
                        <h2 class="section-title">On This Day</h2>
                        <div class="on-this-day">
                            ${onThisDay.map(g => html`
                                <${ScoreCard} game=${g} onClick=${() => showGameDetail(g.GameID)} />
                            `)}
                        </div>
                    `}

                    ${futureProsSpotlight.length > 0 && html`
                        <h2 class="section-title">Future Pros Spotlight</h2>
                        <div class="future-pros-spotlight">
                            ${futureProsSpotlight.map(p => html`
                                <div class="spotlight-card" onClick=${() => showPlayerDetail(p['Player ID'] || p.Player)}>
                                    <div class="spotlight-name">${p.Player}</div>
                                    <div class="spotlight-info">
                                        ${p.Team} · ${p.proGames} pro games
                                        ${p.NBA ? html` <span class="badge badge-nba">NBA</span>` : null}
                                        ${p.WNBA ? html` <span class="badge badge-wnba">WNBA</span>` : null}
                                        ${p.Intl_Pro ? html` <span class="badge badge-intl">INTL</span>` : null}
                                    </div>
                                </div>
                            `)}
                            <button class="link-btn" onClick=${() => onNavigate('people', 'future-pros')}>View all future pros →</button>
                        </div>
                    `}

                    <h2 class="section-title">Quick Links</h2>
                    <div class="quick-links">
                        <button class="quick-link-btn" onClick=${() => onNavigate('games', 'records')}>Game Records</button>
                        <button class="quick-link-btn" onClick=${() => onNavigate('games', 'scorigami')}>Scorigami</button>
                        <button class="quick-link-btn" onClick=${() => onNavigate('people', 'leaders')}>Stat Leaders</button>
                        <button class="quick-link-btn" onClick=${() => onNavigate('people', 'achievements')}>Achievements</button>
                        <button class="quick-link-btn" onClick=${() => onNavigate('places', 'map')}>School Map</button>
                        <button class="quick-link-btn" onClick=${() => onNavigate('places', 'conferences')}>Conference Progress</button>
                    </div>
                </div>
            </div>
        </section>
    `;
}

// ============================================================================
// SECTION PLACEHOLDERS (to be filled in subsequent phases)
// ============================================================================

function GamesSection({ sub, onSubChange, showGameDetail }) {
    const subItems = [
        { id: '', label: 'Game Log' },
        { id: 'records', label: 'Records' },
        { id: 'seasons', label: 'Seasons' },
        { id: 'scorigami', label: 'Scorigami' },
        { id: 'calendar', label: 'Calendar' },
        { id: 'matchups', label: 'Matchups' },
        { id: 'teams', label: 'Teams' },
    ];

    return html`
        <section class="section-content">
            <${SubNav} items=${subItems} active=${sub} onSelect=${onSubChange} />
            <div class="sub-content">
                ${sub === '' && html`<${GameLog} showGameDetail=${showGameDetail} />`}
                ${sub === 'records' && html`<${GameRecords} showGameDetail=${showGameDetail} />`}
                ${sub === 'scorigami' && html`<${ScorigamiView} showGameDetail=${showGameDetail} />`}
                ${sub === 'calendar' && html`<${CalendarView} showGameDetail=${showGameDetail} />`}
                ${sub === 'teams' && html`<${TeamsView} />`}
                ${sub === 'matchups' && html`<${MatchupsView} />`}
                ${sub === 'seasons' && html`<${SeasonsView} />`}
            </div>
        </section>
    `;
}

function PeopleSection({ sub, onSubChange, showPlayerDetail, showGameDetail }) {
    const subItems = [
        { id: '', label: 'Stats' },
        { id: 'leaders', label: 'Leaders' },
        { id: 'highs', label: 'Highs' },
        { id: 'logs', label: 'Game Logs' },
        { id: 'records', label: 'Records' },
        { id: 'future-pros', label: 'Future Pros' },
        { id: 'achievements', label: 'Achievements' },
    ];

    return html`
        <section class="section-content">
            <${SubNav} items=${subItems} active=${sub} onSelect=${onSubChange} />
            <div class="sub-content">
                ${sub === '' && html`<${PlayerStats} showPlayerDetail=${showPlayerDetail} />`}
                ${sub === 'leaders' && html`<${StatLeaders} showPlayerDetail=${showPlayerDetail} />`}
                ${sub === 'highs' && html`<${CareerHighs} showPlayerDetail=${showPlayerDetail} />`}
                ${sub === 'logs' && html`<${PlayerGameLogs} showPlayerDetail=${showPlayerDetail} showGameDetail=${showGameDetail} />`}
                ${sub === 'records' && html`<${PlayerRecords} showPlayerDetail=${showPlayerDetail} />`}
                ${sub === 'future-pros' && html`<${FuturePros} showPlayerDetail=${showPlayerDetail} />`}
                ${sub === 'achievements' && html`<${Achievements} showGameDetail=${showGameDetail} />`}
            </div>
        </section>
    `;
}

function PlacesSection({ sub, onSubChange, showVenueDetail, showGameDetail }) {
    const subItems = [
        { id: '', label: 'Venues' },
        { id: 'map', label: 'School Map' },
        { id: 'conferences', label: 'Conferences' },
        { id: 'upcoming', label: 'Upcoming' },
    ];

    return html`
        <section class="section-content">
            <${SubNav} items=${subItems} active=${sub} onSelect=${onSubChange} />
            <div class="sub-content">
                ${sub === '' && html`<${VenuesView} showVenueDetail=${showVenueDetail} />`}
                ${sub === 'map' && html`<${SchoolMapView} />`}
                ${sub === 'conferences' && html`<${ConferenceProgress} />`}
                ${sub === 'upcoming' && html`<${UpcomingView} showGameDetail=${showGameDetail} />`}
            </div>
        </section>
    `;
}

// ============================================================================
// STUB COMPONENTS (to be implemented in subsequent phases)
// ============================================================================

function GameLog({ showGameDetail }) {
    const [page, setPage] = useState(1);
    const [quickFilter, setQuickFilter] = useState('all');
    const [genderFilter, setGenderFilter] = useState('');
    const pageSize = 50;

    const games = DATA.games || [];
    const filtered = useMemo(() => {
        let result = [...games];
        if (genderFilter) result = result.filter(g => g.Gender === genderFilter);
        if (quickFilter === 'ranked') result = result.filter(g => g.AwayRank || g.HomeRank);
        if (quickFilter === 'upsets') result = result.filter(g => {
            const awayWon = (g['Away Score'] || 0) > (g['Home Score'] || 0);
            const awayRank = g.AwayRank || 999;
            const homeRank = g.HomeRank || 999;
            return (awayWon && homeRank < awayRank) || (!awayWon && awayRank < homeRank);
        });
        if (quickFilter === 'overtime') result = result.filter(g => (g.Linescore?.away?.OT?.length || 0) > 0);
        if (quickFilter === 'blowouts') result = result.filter(g => Math.abs((g['Away Score']||0) - (g['Home Score']||0)) >= 20);
        if (quickFilter === 'close') result = result.filter(g => Math.abs((g['Away Score']||0) - (g['Home Score']||0)) <= 5);
        if (quickFilter === 'neutral') result = result.filter(g => g.NeutralSite || NEUTRAL_SITES.has(g.Venue));
        result.sort((a, b) => (b.DateSort || '').localeCompare(a.DateSort || ''));
        return result;
    }, [games, quickFilter, genderFilter]);

    const pageData = filtered.slice((page - 1) * pageSize, page * pageSize);

    const quickFilters = [
        { id: 'all', label: 'All', count: games.length },
        { id: 'ranked', label: 'Ranked' },
        { id: 'upsets', label: 'Upsets' },
        { id: 'overtime', label: 'OT' },
        { id: 'blowouts', label: 'Blowouts' },
        { id: 'close', label: 'Close' },
        { id: 'neutral', label: 'Neutral' },
    ];

    const genderFilters = [
        { id: '', label: 'All' },
        { id: 'M', label: "Men's" },
        { id: 'W', label: "Women's" },
    ];

    return html`
        <div>
            <${FilterBar}>
                <${QuickFilters} filters=${quickFilters} active=${quickFilter} onSelect=${(f) => { setQuickFilter(f); setPage(1); }} />
                <div class="gender-toggle">
                    ${genderFilters.map(gf => html`
                        <button class=${'quick-filter-btn' + (genderFilter === gf.id ? ' active' : '')} onClick=${() => { setGenderFilter(gf.id); setPage(1); }}>${gf.label}</button>
                    `)}
                </div>
            <//>
            ${pageData.length === 0
                ? html`<${EmptyState} />`
                : html`
                    <div class="game-log-list">
                                ${pageData.map(game => {
                                    const milestones = gameMilestones[game.GameID] || { badges: [] };
                                    const awayWon = (game['Away Score']||0) > (game['Home Score']||0);
                                    const awayRank = game.AwayRank;
                                    const homeRank = game.HomeRank;
                                    let isUpset = false;
                                    if (awayWon && (homeRank||999) < (awayRank||999)) isUpset = true;
                                    if (!awayWon && (awayRank||999) < (homeRank||999)) isUpset = true;
                                    const linescore = game.Linescore || {};
                                    const otPeriods = linescore.away?.OT?.length || 0;
                                    const otText = otPeriods > 0 ? ` (${otPeriods > 1 ? otPeriods + 'OT' : 'OT'})` : '';
                                    const genderTag = game.Gender === 'W' ? ' (W)' : '';
                                    const allBadges = [
                                        ...(isUpset ? [{ type: 'upset', text: 'UPSET', title: 'Upset' }] : []),
                                        ...milestones.badges
                                    ];
                                    const location = [game.City, game.State].filter(Boolean).join(', ');
                                    const awayLogo = getTeamLogoUrl(game['Away Team']);
                                    const homeLogo = getTeamLogoUrl(game['Home Team']);

                                    return html`
                                        <div class="game-log-card" onClick=${() => showGameDetail(game.GameID)}>
                                            <div class="gl-date">
                                                ${game.Date || ''}
                                                ${(game.Division === 'D1' || !game.Division) && html`
                                                    ${' '}<a href=${getSportsRefUrl(game)} target="_blank" class="external-link" title="Sports Reference" onClick=${(e) => e.stopPropagation()}>↗</a>
                                                `}
                                                ${game.Gender === 'W' ? html` <span class="badge badge-women">W</span>` : null}
                                            </div>
                                            <div class="gl-matchup">
                                                <div class="gl-team gl-away ${awayWon ? 'gl-winner' : ''}">
                                                    ${awayLogo ? html`<img src=${awayLogo} class="gl-logo" alt="" />` : null}
                                                    ${awayRank ? html`<span class="ap-rank">#${awayRank}</span> ` : null}
                                                    <span class="gl-team-name">${game['Away Team']}</span>
                                                </div>
                                                <div class="gl-score">
                                                    <span class=${awayWon ? 'gl-winner-score' : ''}>${game['Away Score']||0}</span>
                                                    <span class="gl-score-sep">-</span>
                                                    <span class=${!awayWon ? 'gl-winner-score' : ''}>${game['Home Score']||0}</span>
                                                    ${otText ? html`<span class="gl-ot">${otText}</span>` : null}
                                                </div>
                                                <div class="gl-team gl-home ${!awayWon ? 'gl-winner' : ''}">
                                                    ${homeLogo ? html`<img src=${homeLogo} class="gl-logo" alt="" />` : null}
                                                    ${homeRank ? html`<span class="ap-rank">#${homeRank}</span> ` : null}
                                                    <span class="gl-team-name">${game['Home Team']}</span>
                                                </div>
                                            </div>
                                            <div class="gl-venue">
                                                ${game.Venue || ''}${game.NeutralSite ? html` <span class="neutral-badge">N</span>` : null}
                                                ${location ? html` · ${location}` : null}
                                            </div>
                                            ${allBadges.length > 0 ? html`
                                                <div class="gl-badges">
                                                    ${allBadges.map(b => html`<${Badge} ...${b} />`)}
                                                </div>
                                            ` : null}
                                        </div>
                                    `;
                                })}
                    </div>
                    <${Pagination} page=${page} pageSize=${pageSize} total=${filtered.length} onPageChange=${setPage} />
                `
            }
        </div>
    `;
}

function GameRecords({ showGameDetail }) {
    const games = DATA.games || [];
    const gamesWithMargin = useMemo(() => games.map(g => {
        const awayScore = parseInt(g['Away Score']) || 0;
        const homeScore = parseInt(g['Home Score']) || 0;
        const margin = Math.abs(homeScore - awayScore);
        const total = homeScore + awayScore;
        const winner = homeScore > awayScore ? g['Home Team'] : g['Away Team'];
        const loser = homeScore > awayScore ? g['Away Team'] : g['Home Team'];
        const winnerScore = Math.max(homeScore, awayScore);
        const loserScore = Math.min(homeScore, awayScore);
        return { ...g, margin, total, winner, loser, winnerScore, loserScore };
    }), [games]);

    const records = useMemo(() => {
        const blowouts = [...gamesWithMargin].sort((a, b) => b.margin - a.margin).slice(0, 10);
        const closest = [...gamesWithMargin].sort((a, b) => a.margin - b.margin).slice(0, 10);
        const highest = [...gamesWithMargin].sort((a, b) => b.total - a.total).slice(0, 10);
        const lowest = [...gamesWithMargin].sort((a, b) => a.total - b.total).slice(0, 10);
        return { blowouts, closest, highest, lowest };
    }, [gamesWithMargin]);

    const RecordList = ({ items, showMargin, showTotal }) => html`
        ${items.map((g, i) => {
            const wTag = g.Gender === 'W' ? ' (W)' : '';
            return html`
                <div class="record-item" onClick=${() => showGameDetail(g.GameID)}>
                    <span class="rank">${i + 1}.</span>
                    <span class="teams">${g.winner}${wTag} def. ${g.loser}${wTag}</span>
                    <span class="score">${g.winnerScore}-${g.loserScore}</span>
                    ${showMargin && html`<span class="margin">+${g.margin}</span>`}
                    ${showTotal && html`<span class="total">${g.total} pts</span>`}
                </div>
            `;
        })}
    `;

    return html`
        <div class="records-grid">
            <${Card} className="record-card">
                <h3>Biggest Blowouts</h3>
                <${RecordList} items=${records.blowouts} showMargin=${true} />
            <//>
            <${Card} className="record-card">
                <h3>Closest Games</h3>
                <${RecordList} items=${records.closest} showMargin=${true} />
            <//>
            <${Card} className="record-card">
                <h3>Highest Scoring</h3>
                <${RecordList} items=${records.highest} showTotal=${true} />
            <//>
            <${Card} className="record-card">
                <h3>Lowest Scoring</h3>
                <${RecordList} items=${records.lowest} showTotal=${true} />
            <//>
        </div>
    `;
}

function ScorigamiView({ showGameDetail }) {
    const allGames = DATA.games || [];
    const [gender, setGender] = useState('');
    const [hover, setHover] = useState(null);
    const tooltipRef = useRef(null);

    const { scoreMap, minWin, maxWin, minLose, maxLose, uniqueCount, totalGames, mostCommon } = useMemo(() => {
        const games = allGames.filter(g => {
            if (gender && g.Gender !== gender) return false;
            return g['Away Score'] && g['Home Score'];
        });
        const map = {};
        let mnW = Infinity, mxW = 0, mnL = Infinity, mxL = 0;
        games.forEach(g => {
            const away = parseInt(g['Away Score']) || 0;
            const home = parseInt(g['Home Score']) || 0;
            const win = Math.max(away, home);
            const lose = Math.min(away, home);
            const key = `${win}-${lose}`;
            if (!map[key]) map[key] = [];
            map[key].push(g);
            mnW = Math.min(mnW, win); mxW = Math.max(mxW, win);
            mnL = Math.min(mnL, lose); mxL = Math.max(mxL, lose);
        });
        let best = null, bestCount = 0;
        for (const [k, v] of Object.entries(map)) {
            if (v.length > bestCount) { bestCount = v.length; best = k; }
        }
        return {
            scoreMap: map, minWin: mnW, maxWin: mxW, minLose: mnL, maxLose: mxL,
            uniqueCount: Object.keys(map).length, totalGames: games.length,
            mostCommon: best ? `${best} (${bestCount}×)` : '-'
        };
    }, [allGames, gender]);

    const showTooltip = useCallback((e, win, lose) => {
        const key = `${win}-${lose}`;
        const games = scoreMap[key] || [];
        if (!games.length) return;
        setHover({ win, lose, games });
        if (tooltipRef.current) {
            const rect = e.target.getBoundingClientRect();
            tooltipRef.current.style.left = Math.min(rect.right + 10, window.innerWidth - 320) + 'px';
            tooltipRef.current.style.top = Math.max(10, rect.top - 50) + 'px';
        }
    }, [scoreMap]);

    const cellClass = (count) => {
        if (count >= 6) return 'has-game count-6';
        if (count >= 5) return 'has-game count-5';
        if (count >= 4) return 'has-game count-4';
        if (count >= 3) return 'has-game count-3';
        if (count >= 2) return 'has-game count-2';
        return 'has-game';
    };

    if (totalGames === 0) return html`<${EmptyState} title="No games" message="No games to display for scorigami" />`;

    return html`
        <div>
            <div class="scorigami-controls">
                <div class="filter-group">
                    <label>Gender</label>
                    <div class="gender-toggle">
                        ${[{id:'',label:'All'},{id:'M',label:"Men's"},{id:'W',label:"Women's"}].map(gf => html`
                            <button class=${'quick-filter-btn' + (gender === gf.id ? ' active' : '')} onClick=${() => setGender(gf.id)}>${gf.label}</button>
                        `)}
                    </div>
                </div>
                <div class="scorigami-stats">
                    <span>${uniqueCount}</span> unique scores from <span>${totalGames}</span> games
                    <span style="margin-left: 1.5rem">Most common: <span>${mostCommon}</span></span>
                </div>
            </div>

            <div class="scorigami-wrapper">
                <div class="scorigami-y-label">Loser's Score</div>
                <div class="scorigami-main">
                    <div class="scorigami-container">
                        <table class="scorigami-grid">
                            <thead>
                                <tr>
                                    <th></th>
                                    ${Array.from({ length: maxWin - minWin + 1 }, (_, i) => html`<th>${minWin + i}</th>`)}
                                </tr>
                            </thead>
                            <tbody>
                                ${Array.from({ length: maxLose - minLose + 1 }, (_, li) => {
                                    const lose = minLose + li;
                                    return html`
                                        <tr>
                                            <th>${lose}</th>
                                            ${Array.from({ length: maxWin - minWin + 1 }, (_, wi) => {
                                                const win = minWin + wi;
                                                if (lose >= win) return html`<td class="impossible"></td>`;
                                                const key = `${win}-${lose}`;
                                                const games = scoreMap[key];
                                                if (!games) return html`<td class="empty"></td>`;
                                                return html`<td
                                                    class=${cellClass(games.length)}
                                                    onMouseEnter=${(e) => showTooltip(e, win, lose)}
                                                    onMouseLeave=${() => setHover(null)}
                                                    onClick=${() => games.length === 1 ? showGameDetail(games[0].GameID) : setHover({ win, lose, games, pinned: true })}
                                                >${games.length}</td>`;
                                            })}
                                        </tr>
                                    `;
                                })}
                            </tbody>
                        </table>
                    </div>
                    <div class="scorigami-x-label">Winner's Score</div>
                </div>
            </div>

            <div class="scorigami-legend">
                <div class="scorigami-legend-item"><div class="scorigami-legend-color" style="background: #1c1917"></div><span>Impossible</span></div>
                <div class="scorigami-legend-item"><div class="scorigami-legend-color" style="background: #e2e8f0"></div><span>Not seen</span></div>
                <div class="scorigami-legend-item"><div class="scorigami-legend-color" style="background: #86efac"></div><span>1 game</span></div>
                <div class="scorigami-legend-item"><div class="scorigami-legend-color" style="background: #22c55e"></div><span>2-3 games</span></div>
                <div class="scorigami-legend-item"><div class="scorigami-legend-color" style="background: #166534"></div><span>4+ games</span></div>
            </div>

            <div ref=${tooltipRef} class=${'scorigami-tooltip' + (hover ? ' visible' : '')}>
                ${hover && html`
                    <h4>${hover.win}-${hover.lose}</h4>
                    ${hover.games.slice(0, 5).map(g => {
                        const wTag = g.Gender === 'W' ? ' (W)' : '';
                        return html`
                            <div class="game-item" onClick=${() => showGameDetail(g.GameID)}>
                                ${g['Away Team']}${wTag} ${g['Away Score']} @ ${g['Home Team']}${wTag} ${g['Home Score']}
                                <br /><small>${g.Date || ''}</small>
                            </div>
                        `;
                    })}
                    ${hover.games.length > 5 && html`<div style="color: var(--text-secondary); font-size: 0.8rem; margin-top: 0.5rem">+${hover.games.length - 5} more</div>`}
                `}
            </div>
        </div>
    `;
}

function CalendarView({ showGameDetail }) {
    const games = DATA.games || [];

    // Group games by month+day (year-agnostic), keyed by "MMDD"
    const gamesByMMDD = useMemo(() => {
        const map = {};
        games.forEach(g => {
            const ds = g.DateSort || '';
            if (!ds) return;
            const mmdd = ds.slice(4, 8); // "MMDD"
            if (!map[mmdd]) map[mmdd] = [];
            map[mmdd].push(g);
        });
        return map;
    }, [games]);

    // Determine which months of the basketball season have games
    const seasonMonths = useMemo(() => {
        const monthSet = new Set();
        games.forEach(g => {
            const ds = g.DateSort || '';
            if (ds) monthSet.add(parseInt(ds.slice(4, 6)));
        });
        // Basketball season order: Oct(10), Nov(11), Dec(12), Jan(1), Feb(2), Mar(3), Apr(4), May(5)
        const order = [10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9];
        return order.filter(m => monthSet.has(m));
    }, [games]);

    // Count unique game days
    const gameDays = useMemo(() => Object.keys(gamesByMMDD).length, [gamesByMMDD]);

    // On This Day
    const today = new Date();
    const todayMMDD = String(today.getMonth() + 1).padStart(2, '0') + String(today.getDate()).padStart(2, '0');
    const onThisDay = gamesByMMDD[todayMMDD] || [];

    const [selectedDay, setSelectedDay] = useState(null);

    const monthNames = ['', 'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];

    const renderMonth = (monthNum) => {
        // Use a reference year (2024 is a leap year so Feb has 29 days)
        const refYear = 2024;
        const monthIdx = monthNum - 1;
        const firstDay = new Date(refYear, monthIdx, 1).getDay();
        const daysInMonth = new Date(refYear, monthIdx + 1, 0).getDate();
        const mm = String(monthNum).padStart(2, '0');

        const cells = [];
        for (let i = 0; i < firstDay; i++) cells.push(null);
        for (let d = 1; d <= daysInMonth; d++) {
            const dd = String(d).padStart(2, '0');
            const mmdd = mm + dd;
            cells.push({ day: d, mmdd, games: gamesByMMDD[mmdd] || [] });
        }

        return html`
            <div class="calendar-month">
                <h4 class="calendar-month-title">${monthNames[monthNum]}</h4>
                <div class="calendar-grid">
                    ${['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map(d => html`<div class="calendar-header-cell">${d}</div>`)}
                    ${cells.map(cell => {
                        if (!cell) return html`<div class="calendar-cell empty"></div>`;
                        const hasGames = cell.games.length > 0;
                        const isToday = cell.mmdd === todayMMDD;
                        return html`
                            <div
                                class=${'calendar-cell' + (hasGames ? ' has-games' : '') + (isToday ? ' today' : '')}
                                onClick=${hasGames ? () => setSelectedDay(cell) : null}
                                title=${hasGames ? `${cell.games.length} game${cell.games.length > 1 ? 's' : ''}` : ''}
                            >
                                <span class="calendar-day">${cell.day}</span>
                                ${hasGames && html`<span class="calendar-dot">${cell.games.length > 1 ? cell.games.length : ''}</span>`}
                            </div>
                        `;
                    })}
                </div>
            </div>
        `;
    };

    return html`
        <div>
            <div class="calendar-stats">
                <${StatBox} label="Game Days" value=${gameDays} />
                <${StatBox} label="Total Games" value=${games.length} />
                <${StatBox} label="Season Months" value=${seasonMonths.length} />
            </div>

            ${onThisDay.length > 0 && html`
                <div class="on-this-day-section">
                    <h3 class="section-title">On This Day</h3>
                    ${onThisDay.map(g => html`<${ScoreCard} game=${g} onClick=${() => showGameDetail(g.GameID)} />`)}
                </div>
            `}

            <div class="calendar-months">
                ${seasonMonths.map(m => renderMonth(m))}
            </div>

            ${selectedDay && html`
                <${Modal} id="day-modal" active=${true} onClose=${() => setSelectedDay(null)} title="${monthNames[parseInt(selectedDay.mmdd.slice(0,2))]} ${parseInt(selectedDay.mmdd.slice(2))}">
                    <div class="day-games">
                        ${selectedDay.games.map(g => html`<${ScoreCard} game=${g} onClick=${() => { setSelectedDay(null); showGameDetail(g.GameID); }} />`)}
                    </div>
                <//>
            `}
        </div>
    `;
}

function TeamsView() {
    const [genderFilter, setGenderFilter] = useState('');
    const [search, setSearch] = useState('');
    const [teamTab, setTeamTab] = useState('records');
    const teamTabs = [
        { id: 'records', label: 'Records' },
        { id: 'streaks', label: 'Streaks' },
        { id: 'splits', label: 'Home/Away' },
        { id: 'standings', label: 'Standings' },
        { id: 'starters', label: 'Starters vs Bench' },
    ];

    const genderFilters = [{id:'',label:'All'},{id:'M',label:"Men's"},{id:'W',label:"Women's"}];

    const filterBySearch = (data) => {
        if (!search) return data;
        const q = search.toLowerCase();
        return data.filter(t => ((t.Team || '') + ' ' + (t.Conference || '')).toLowerCase().includes(q));
    };

    // Records
    const teams = useMemo(() => {
        let data = DATA.teams || [];
        if (genderFilter) data = data.filter(t => t.Gender === genderFilter);
        return filterBySearch(data);
    }, [genderFilter, search]);

    // Streaks
    const streaks = useMemo(() => {
        let data = DATA.teamStreaks || [];
        if (genderFilter) data = data.filter(t => t.Gender === genderFilter);
        return filterBySearch(data);
    }, [genderFilter, search]);

    // Home/Away Splits
    const splits = useMemo(() => {
        let data = DATA.homeAwaySplits || [];
        if (genderFilter) data = data.filter(t => t.Gender === genderFilter);
        return filterBySearch(data);
    }, [genderFilter, search]);

    // Conference Standings
    const standings = useMemo(() => {
        let data = DATA.conferenceStandings || [];
        if (genderFilter) data = data.filter(t => t.Gender === genderFilter);
        return filterBySearch(data);
    }, [genderFilter, search]);

    // Starters vs Bench
    const starters = useMemo(() => {
        let data = DATA.startersBench || [];
        if (Array.isArray(data)) {
            if (genderFilter) data = data.filter(t => t.Gender === genderFilter);
            return filterBySearch(data);
        }
        const arr = Object.values(data);
        if (genderFilter) return filterBySearch(arr.filter(t => t.Gender === genderFilter));
        return filterBySearch(arr);
    }, [genderFilter, search]);

    return html`
        <div>
            <${FilterBar}>
                <input type="text" class="filter-input" placeholder="Search teams..." value=${search} onInput=${(e) => setSearch(e.target.value)} />
                <div class="gender-toggle">
                    ${genderFilters.map(gf => html`
                        <button class=${'quick-filter-btn' + (genderFilter === gf.id ? ' active' : '')} onClick=${() => setGenderFilter(gf.id)}>${gf.label}</button>
                    `)}
                </div>
            <//>
            <${SubNav} items=${teamTabs} active=${teamTab} onSelect=${setTeamTab} />

            ${teamTab === 'records' && html`
                <div class="team-cards-grid">
                    ${teams.map(t => {
                        const winPct = (t['Win%'] || 0) * 100;
                        return html`
                            <div class="team-record-card">
                                <div class="team-record-header">
                                    <span class="team-record-name">${t.Team}${t.Gender === 'W' ? ' (W)' : ''}</span>
                                    <span class="team-record-gp">${t.Games || 0} GP</span>
                                </div>
                                <div class="team-record-wl">
                                    <span class="team-wins">${t.Wins || 0}W</span>
                                    <span class="team-record-dash">-</span>
                                    <span class="team-losses">${t.Losses || 0}L</span>
                                </div>
                                <div class="team-winpct-bar">
                                    <div class="team-winpct-fill" style=${'width:' + winPct + '%'}></div>
                                </div>
                                <div class="team-winpct-label">${winPct.toFixed(1)}%</div>
                                <div class="team-record-scoring">
                                    <div class="team-scoring-item">
                                        <span class="team-scoring-label">PPG</span>
                                        <span class="team-scoring-value">${(t.PPG || 0).toFixed(1)}</span>
                                    </div>
                                    <div class="team-scoring-item">
                                        <span class="team-scoring-label">PAPG</span>
                                        <span class="team-scoring-value">${(t.PAPG || 0).toFixed(1)}</span>
                                    </div>
                                    <div class="team-scoring-item">
                                        <span class="team-scoring-label">Diff</span>
                                        <span class=${'team-scoring-value ' + ((t.PPG || 0) - (t.PAPG || 0) >= 0 ? 'stat-good' : 'stat-poor')}>
                                            ${((t.PPG || 0) - (t.PAPG || 0) >= 0 ? '+' : '') + ((t.PPG || 0) - (t.PAPG || 0)).toFixed(1)}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        `;
                    })}
                </div>
            `}

            ${teamTab === 'streaks' && html`
                <div class="team-cards-grid">
                    ${streaks.map(t => {
                        const current = t['Current Streak'] || '-';
                        const isWin = current.startsWith('W');
                        const isLoss = current.startsWith('L');
                        // Parse Last 5/10 into dots
                        const parseLast = (str) => {
                            if (!str) return [];
                            return str.split('-').map(Number);
                        };
                        const last5 = parseLast(t['Last 5']);
                        const last10 = parseLast(t['Last 10']);
                        return html`
                            <div class="team-record-card">
                                <div class="team-record-header">
                                    <span class="team-record-name">${t.Team}${t.Gender === 'W' ? ' (W)' : ''}</span>
                                </div>
                                <div class=${'streak-current ' + (isWin ? 'streak-win' : isLoss ? 'streak-loss' : '')}>
                                    ${current}
                                </div>
                                <div class="streak-details">
                                    <div class="streak-detail-item">
                                        <span class="team-scoring-label">Best Win Streak</span>
                                        <span class="team-scoring-value stat-good">${t['Longest Win Streak'] || 0}</span>
                                    </div>
                                    <div class="streak-detail-item">
                                        <span class="team-scoring-label">Worst Loss Streak</span>
                                        <span class="team-scoring-value stat-poor">${t['Longest Loss Streak'] || 0}</span>
                                    </div>
                                </div>
                                <div class="streak-recent">
                                    ${last5.length >= 2 ? html`
                                        <div class="streak-recent-row">
                                            <span class="team-scoring-label">Last 5</span>
                                            <span class="team-scoring-value">${last5[0]}-${last5[1]}</span>
                                        </div>
                                    ` : null}
                                    ${last10.length >= 2 ? html`
                                        <div class="streak-recent-row">
                                            <span class="team-scoring-label">Last 10</span>
                                            <span class="team-scoring-value">${last10[0]}-${last10[1]}</span>
                                        </div>
                                    ` : null}
                                </div>
                            </div>
                        `;
                    })}
                </div>
            `}

            ${teamTab === 'splits' && html`
                <div class="team-cards-grid">
                    ${splits.map(t => {
                        const homePct = (t['Home Win%'] || 0) * 100;
                        const awayPct = (t['Away Win%'] || 0) * 100;
                        const totalW = t['Total W'] || 0;
                        const totalL = t['Total L'] || 0;
                        return html`
                            <div class="team-record-card">
                                <div class="team-record-header">
                                    <span class="team-record-name">${t.Team}${t.Gender === 'W' ? ' (W)' : ''}</span>
                                    <span class="team-record-gp">${totalW}-${totalL}</span>
                                </div>
                                <div class="splits-bars">
                                    <div class="split-row">
                                        <span class="split-label">Home</span>
                                        <div class="split-bar-track">
                                            <div class="split-bar-fill split-home" style=${'width:' + homePct + '%'}></div>
                                        </div>
                                        <span class="split-record">${t['Home W']}-${t['Home L']}</span>
                                    </div>
                                    <div class="split-row">
                                        <span class="split-label">Away</span>
                                        <div class="split-bar-track">
                                            <div class="split-bar-fill split-away" style=${'width:' + awayPct + '%'}></div>
                                        </div>
                                        <span class="split-record">${t['Away W']}-${t['Away L']}</span>
                                    </div>
                                    ${(t['Neutral W'] || t['Neutral L']) ? html`
                                        <div class="split-row">
                                            <span class="split-label">Neutral</span>
                                            <div class="split-bar-track">
                                                <div class="split-bar-fill split-neutral" style=${'width:' + ((t['Neutral W'] || 0) / Math.max(1, (t['Neutral W'] || 0) + (t['Neutral L'] || 0)) * 100) + '%'}></div>
                                            </div>
                                            <span class="split-record">${t['Neutral W'] || 0}-${t['Neutral L'] || 0}</span>
                                        </div>
                                    ` : null}
                                </div>
                            </div>
                        `;
                    })}
                </div>
            `}

            ${teamTab === 'standings' && html`
                <div class="table-container">
                    <table class="data-table">
                        <thead><tr><th>Conference</th><th>Team</th><th>Conf W-L</th><th>Conf%</th><th>Overall W-L</th><th>Overall%</th></tr></thead>
                        <tbody>
                            ${standings.map(t => html`
                                <tr>
                                    <td>${t.Conference}</td>
                                    <td>${t.Team}${t.Gender === 'W' ? ' (W)' : ''}</td>
                                    <td>${t['Conf W']}-${t['Conf L']}</td>
                                    <td>${((t['Conf Win%'] || 0) * 100).toFixed(0)}%</td>
                                    <td>${t['Overall W']}-${t['Overall L']}</td>
                                    <td>${((t['Overall Win%'] || 0) * 100).toFixed(0)}%</td>
                                </tr>
                            `)}
                        </tbody>
                    </table>
                </div>
            `}

            ${teamTab === 'starters' && html`
                <div class="team-cards-grid">
                    ${(() => {
                        // Group starters by team
                        const byTeam = {};
                        starters.forEach(t => {
                            const key = t.Team + (t.Gender === 'W' ? ' (W)' : '');
                            if (!byTeam[key]) byTeam[key] = {};
                            byTeam[key][t.Type] = t;
                            byTeam[key].team = key;
                        });
                        return Object.values(byTeam).map(pair => {
                            const s = pair.Starters || {};
                            const b = pair.Bench || {};
                            return html`
                                <div class="team-record-card starters-card">
                                    <div class="team-record-header">
                                        <span class="team-record-name">${pair.team}</span>
                                    </div>
                                    <div class="starters-comparison">
                                        <div class="starters-col">
                                            <div class="starters-col-header"><span class="badge badge-starter">Starters</span></div>
                                            <div class="starters-stat"><span class="team-scoring-label">PPG</span><span class="team-scoring-value">${(s.PPG || 0).toFixed(1)}</span></div>
                                            <div class="starters-stat"><span class="team-scoring-label">RPG</span><span class="team-scoring-value">${(s.RPG || 0).toFixed(1)}</span></div>
                                            <div class="starters-stat"><span class="team-scoring-label">APG</span><span class="team-scoring-value">${(s.APG || 0).toFixed(1)}</span></div>
                                            <div class="starters-stat"><span class="team-scoring-label">MPG</span><span class="team-scoring-value">${(s.MPG || 0).toFixed(1)}</span></div>
                                        </div>
                                        <div class="starters-divider"></div>
                                        <div class="starters-col">
                                            <div class="starters-col-header"><span class="badge badge-bench">Bench</span></div>
                                            <div class="starters-stat"><span class="team-scoring-label">PPG</span><span class="team-scoring-value">${(b.PPG || 0).toFixed(1)}</span></div>
                                            <div class="starters-stat"><span class="team-scoring-label">RPG</span><span class="team-scoring-value">${(b.RPG || 0).toFixed(1)}</span></div>
                                            <div class="starters-stat"><span class="team-scoring-label">APG</span><span class="team-scoring-value">${(b.APG || 0).toFixed(1)}</span></div>
                                            <div class="starters-stat"><span class="team-scoring-label">MPG</span><span class="team-scoring-value">${(b.MPG || 0).toFixed(1)}</span></div>
                                        </div>
                                    </div>
                                </div>
                            `;
                        });
                    })()}
                </div>
            `}
        </div>
    `;
}

function MatchupsView() {
    const games = DATA.games || [];
    const [confFilter, setConfFilter] = useState('');

    // Get all conferences
    const allConfs = useMemo(() => {
        const set = new Set();
        games.forEach(g => {
            const ac = getGameConference(g, 'away');
            const hc = getGameConference(g, 'home');
            if (ac) set.add(ac);
            if (hc) set.add(hc);
        });
        return [...set].sort();
    }, [games]);

    // Conference-vs-conference matrix
    const { confList, confMatrix } = useMemo(() => {
        const confSet = new Set();
        const data = {};
        games.forEach(g => {
            const ac = getGameConference(g, 'away');
            const hc = getGameConference(g, 'home');
            if (!ac || !hc) return;
            confSet.add(ac);
            confSet.add(hc);
            if (ac === hc) {
                // Intra-conference
                if (!data[ac]) data[ac] = {};
                if (!data[ac][ac]) data[ac][ac] = 0;
                data[ac][ac]++;
            } else {
                // Inter-conference
                if (!data[ac]) data[ac] = {};
                if (!data[hc]) data[hc] = {};
                if (!data[ac][hc]) data[ac][hc] = 0;
                if (!data[hc][ac]) data[hc][ac] = 0;
                data[ac][hc]++;
                data[hc][ac]++;
            }
        });
        const confs = [...confSet].sort();
        return { confList: confs, confMatrix: data };
    }, [games]);

    // Team matrix (when conference is selected)
    const { teamList, matchupData } = useMemo(() => {
        if (!confFilter) return { teamList: [], matchupData: {} };
        // Build team set from game data so non-D1 teams are included
        const teamSet = new Set();
        games.forEach(g => {
            const ac = getGameConference(g, 'away');
            const hc = getGameConference(g, 'home');
            if (ac === confFilter) teamSet.add(g['Away Team']);
            if (hc === confFilter) teamSet.add(g['Home Team']);
        });
        const teams = [...teamSet].sort();

        const data = {};
        teams.forEach(t => { data[t] = {}; });
        games.forEach(g => {
            const away = g['Away Team'];
            const home = g['Home Team'];
            if (!data[away] || !data[home]) return;
            if (!data[away][home]) data[away][home] = { wins: 0, losses: 0, diff: 0, total: 0 };
            if (!data[home][away]) data[home][away] = { wins: 0, losses: 0, diff: 0, total: 0 };
            const as = g['Away Score'] || 0, hs = g['Home Score'] || 0;
            data[away][home].total++;
            data[home][away].total++;
            if (as > hs) {
                data[away][home].wins++; data[away][home].diff += (as - hs);
                data[home][away].losses++; data[home][away].diff += (hs - as);
            } else {
                data[home][away].wins++; data[home][away].diff += (hs - as);
                data[away][home].losses++; data[away][home].diff += (as - hs);
            }
        });

        return { teamList: teams, matchupData: data };
    }, [games, confFilter]);

    const abbrev = (name) => name.length > 10 ? name.slice(0, 9) + '..' : name;
    const maxConfGames = useMemo(() => {
        let max = 0;
        confList.forEach(c1 => confList.forEach(c2 => {
            if (c1 !== c2) max = Math.max(max, confMatrix[c1]?.[c2] || 0);
        }));
        return max;
    }, [confList, confMatrix]);

    return html`
        <div>
            <${FilterBar}>
                <select class="filter-select" value=${confFilter} onChange=${(e) => setConfFilter(e.target.value)}>
                    <option value="">Conference Crossovers</option>
                    ${allConfs.map(c => html`<option value=${c}>${c}</option>`)}
                </select>
            <//>

            ${!confFilter && html`
                <div class="matrix-scroll">
                    <table class="matchup-matrix conf-matrix">
                        <thead>
                            <tr>
                                <th class="matrix-corner"></th>
                                ${confList.map(c => html`<th class="matrix-col-header" title=${c}>${abbrev(c)}</th>`)}
                            </tr>
                        </thead>
                        <tbody>
                            ${confList.map(row => html`
                                <tr>
                                    <th class="matrix-row-header">${row}</th>
                                    ${confList.map(col => {
                                        const count = confMatrix[row]?.[col] || 0;
                                        if (row === col) {
                                            return html`<td class="matrix-diagonal conf-intra"
                                                style="cursor:pointer"
                                                onClick=${() => setConfFilter(row)}
                                                title="View ${row} matchups">${count || ''}</td>`;
                                        }
                                        if (count === 0) return html`<td class="matrix-empty"></td>`;
                                        // Color intensity based on count
                                        const intensity = Math.min(1, count / Math.max(1, maxConfGames));
                                        const alpha = 0.15 + intensity * 0.6;
                                        return html`
                                            <td class="matrix-cell conf-cross"
                                                style=${'background: rgba(37, 99, 235, ' + alpha + ')'}
                                                title="${row} vs ${col}: ${count} game${count !== 1 ? 's' : ''}">
                                                <div class="matrix-record">${count}</div>
                                            </td>
                                        `;
                                    })}
                                </tr>
                            `)}
                        </tbody>
                    </table>
                </div>
            `}

            ${confFilter && html`
                ${teamList.length === 0
                    ? html`<${EmptyState} title="No teams found" />`
                    : html`
                        <div class="matrix-scroll">
                            <table class="matchup-matrix">
                                <thead>
                                    <tr>
                                        <th class="matrix-corner">Team</th>
                                        ${teamList.map(t => html`<th class="matrix-col-header" title=${t}>${abbrev(t)}</th>`)}
                                    </tr>
                                </thead>
                                <tbody>
                                    ${teamList.map(row => html`
                                        <tr>
                                            <th class="matrix-row-header">${row}</th>
                                            ${teamList.map(col => {
                                                if (row === col) return html`<td class="matrix-diagonal">-</td>`;
                                                const r = matchupData[row]?.[col];
                                                if (!r || r.total === 0) return html`<td class="matrix-empty">-</td>`;
                                                const cls = r.wins > r.losses ? 'matrix-win' : r.losses > r.wins ? 'matrix-loss' : 'matrix-even';
                                                const diffStr = r.diff >= 0 ? '+' + r.diff : '' + r.diff;
                                                return html`
                                                    <td class=${'matrix-cell ' + cls}
                                                        title="${row} vs ${col}: ${r.wins}-${r.losses} (${diffStr})">
                                                        <div class="matrix-record">${r.wins}-${r.losses}</div>
                                                        <div class="matrix-diff">${diffStr}</div>
                                                    </td>
                                                `;
                                            })}
                                        </tr>
                                    `)}
                                </tbody>
                            </table>
                        </div>
                    `
                }
            `}
        </div>
    `;
}

function SeasonsView() {
    const games = DATA.games || [];
    const chartRef = useRef(null);
    const chartInstance = useRef(null);

    // Group games by season (Nov-Apr = one season)
    const seasons = useMemo(() => {
        const map = {};
        games.forEach(g => {
            const ds = g.DateSort || '';
            if (!ds) return;
            const year = parseInt(ds.slice(0,4));
            const month = parseInt(ds.slice(4,6));
            // Season: Nov 2024 - Apr 2025 = "2024-25"
            const seasonYear = month >= 8 ? year : year - 1;
            const seasonKey = `${seasonYear}-${String(seasonYear + 1).slice(2)}`;
            if (!map[seasonKey]) map[seasonKey] = { games: [], totalPts: 0, gamesCount: 0 };
            map[seasonKey].games.push(g);
            map[seasonKey].totalPts += (g['Away Score']||0) + (g['Home Score']||0);
            map[seasonKey].gamesCount++;
        });
        return Object.entries(map)
            .sort((a, b) => a[0].localeCompare(b[0]))
            .map(([key, data]) => ({
                season: key,
                games: data.gamesCount,
                totalPts: data.totalPts,
                avgPts: data.totalPts / (data.gamesCount || 1),
                venues: new Set(data.games.map(g => g.Venue)).size,
                teams: new Set(data.games.flatMap(g => [g['Away Team'], g['Home Team']])).size,
            }));
    }, [games]);

    // Chart
    useEffect(() => {
        if (!chartRef.current || seasons.length < 2) return;
        if (chartInstance.current) chartInstance.current.destroy();
        const isDark = document.body.getAttribute('data-theme') === 'dark';
        chartInstance.current = new Chart(chartRef.current, {
            type: 'bar',
            data: {
                labels: seasons.map(s => s.season),
                datasets: [{
                    label: 'Games',
                    data: seasons.map(s => s.games),
                    backgroundColor: getComputedStyle(document.body).getPropertyValue('--accent').trim() || '#c2410c',
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' } }
                }
            }
        });
        return () => { if (chartInstance.current) chartInstance.current.destroy(); };
    }, [seasons]);

    return html`
        <div>
            <h3>Season Comparison</h3>
            ${seasons.length > 1 && html`
                <div class="chart-container" style="height:250px; margin-bottom: var(--space-4)">
                    <canvas ref=${chartRef}></canvas>
                </div>
            `}
            <div class="table-container">
                <table class="data-table">
                    <thead><tr><th>Season</th><th>Games</th><th>Total Pts</th><th>Avg Combined</th><th>Venues</th><th>Teams</th></tr></thead>
                    <tbody>
                        ${seasons.map(s => html`
                            <tr>
                                <td><strong>${s.season}</strong></td>
                                <td>${s.games}</td>
                                <td>${s.totalPts.toLocaleString()}</td>
                                <td>${s.avgPts.toFixed(1)}</td>
                                <td>${s.venues}</td>
                                <td>${s.teams}</td>
                            </tr>
                        `)}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function HeadToHeadView({ showGameDetail }) {
    const [team1, setTeam1] = useState(window._h2hTeam1 || '');
    const [team2, setTeam2] = useState(window._h2hTeam2 || '');
    // Clear the global after picking it up
    useEffect(() => { window._h2hTeam1 = null; window._h2hTeam2 = null; }, []);
    const games = DATA.games || [];

    const allTeams = useMemo(() => {
        const set = new Set();
        games.forEach(g => { set.add(g['Away Team']); set.add(g['Home Team']); });
        return [...set].sort();
    }, [games]);

    const h2hGames = useMemo(() => {
        if (!team1 || !team2) return [];
        return games.filter(g =>
            (g['Away Team'] === team1 && g['Home Team'] === team2) ||
            (g['Away Team'] === team2 && g['Home Team'] === team1)
        ).sort((a, b) => (b.DateSort || '').localeCompare(a.DateSort || ''));
    }, [team1, team2, games]);

    const record = useMemo(() => {
        let t1Wins = 0, t2Wins = 0;
        h2hGames.forEach(g => {
            const winner = (g['Away Score']||0) > (g['Home Score']||0) ? g['Away Team'] : g['Home Team'];
            if (winner === team1) t1Wins++;
            else t2Wins++;
        });
        return { t1Wins, t2Wins };
    }, [h2hGames, team1, team2]);

    return html`
        <div>
            <h3>Head to Head</h3>
            <${FilterBar}>
                <select class="filter-select" value=${team1} onChange=${(e) => setTeam1(e.target.value)}>
                    <option value="">Select Team 1</option>
                    ${allTeams.map(t => html`<option value=${t}>${t}</option>`)}
                </select>
                <span style="color: var(--text-muted); font-weight: 600">vs</span>
                <select class="filter-select" value=${team2} onChange=${(e) => setTeam2(e.target.value)}>
                    <option value="">Select Team 2</option>
                    ${allTeams.map(t => html`<option value=${t}>${t}</option>`)}
                </select>
            <//>

            ${team1 && team2 && html`
                ${h2hGames.length === 0
                    ? html`<${EmptyState} title="No matchups found" message="${team1} and ${team2} haven't played in your game log" />`
                    : html`
                        <div class="h2h-summary" style="text-align:center; margin: var(--space-4) 0">
                            <div style="font-size: 1.5rem; font-weight: 700">
                                ${team1}: ${record.t1Wins} — ${record.t2Wins} :${team2}
                            </div>
                            <div style="color: var(--text-secondary); font-size: 0.875rem">${h2hGames.length} game${h2hGames.length !== 1 ? 's' : ''}</div>
                        </div>
                        <div class="table-container">
                            <table class="data-table">
                                <thead><tr><th>Date</th><th>Away</th><th>Score</th><th>Home</th><th>Venue</th></tr></thead>
                                <tbody>
                                    ${h2hGames.map(g => html`
                                        <tr class="clickable-row" onClick=${() => showGameDetail(g.GameID)}>
                                            <td>${g.Date}</td>
                                            <td>${g['Away Team']}</td>
                                            <td><span class="game-link">${g['Away Score']}-${g['Home Score']}</span></td>
                                            <td>${g['Home Team']}</td>
                                            <td>${g.Venue}</td>
                                        </tr>
                                    `)}
                                </tbody>
                            </table>
                        </div>
                    `
                }
            `}

            ${(!team1 || !team2) && html`<${EmptyState} icon="⚔️" title="Select two teams" message="Choose teams above to compare their head-to-head record" />`}
        </div>
    `;
}

function PlayerStats({ showPlayerDetail }) {
    const [page, setPage] = useState(1);
    const [genderFilter, setGenderFilter] = useState('');
    const [search, setSearch] = useState('');
    const [sortCol, setSortCol] = useState('PPG');
    const [sortAsc, setSortAsc] = useState(false);
    const pageSize = 100;

    const columns = [
        { key: 'Games', label: 'GP', fmt: v => v || 0 },
        { key: 'PPG', label: 'PPG', fmt: v => (v || 0).toFixed(1), threshold: STAT_THRESHOLDS.ppg },
        { key: 'RPG', label: 'RPG', fmt: v => (v || 0).toFixed(1), threshold: STAT_THRESHOLDS.rpg },
        { key: 'APG', label: 'APG', fmt: v => (v || 0).toFixed(1), threshold: STAT_THRESHOLDS.apg },
        { key: 'SPG', label: 'SPG', fmt: v => (v || 0).toFixed(1) },
        { key: 'BPG', label: 'BPG', fmt: v => (v || 0).toFixed(1) },
        { key: 'FG%', label: 'FG%', fmt: v => ((v || 0) * 100).toFixed(1) + '%', threshold: STAT_THRESHOLDS.fgPct },
        { key: '3P%', label: '3P%', fmt: v => ((v || 0) * 100).toFixed(1) + '%', threshold: STAT_THRESHOLDS.threePct },
        { key: 'FT%', label: 'FT%', fmt: v => ((v || 0) * 100).toFixed(1) + '%' },
        { key: 'Total PTS', label: 'PTS', fmt: v => v || 0 },
        { key: 'Total REB', label: 'REB', fmt: v => v || 0 },
        { key: 'Total AST', label: 'AST', fmt: v => v || 0 },
    ];

    const handleSort = (col) => {
        if (sortCol === col) setSortAsc(!sortAsc);
        else { setSortCol(col); setSortAsc(false); }
        setPage(1);
    };

    const filtered = useMemo(() => {
        let data = DATA.players || [];
        if (genderFilter) data = data.filter(p => p.Gender === genderFilter);
        if (search) {
            const q = search.toLowerCase();
            data = data.filter(p => (p.Player||'').toLowerCase().includes(q) || (p.Team||'').toLowerCase().includes(q));
        }
        return [...data].sort((a, b) => {
            const va = a[sortCol] || 0;
            const vb = b[sortCol] || 0;
            return sortAsc ? va - vb : vb - va;
        });
    }, [genderFilter, search, sortCol, sortAsc]);

    const pageData = filtered.slice((page - 1) * pageSize, page * pageSize);
    const genderFilters = [{ id: '', label: 'All' }, { id: 'M', label: "Men's" }, { id: 'W', label: "Women's" }];

    return html`
        <div>
            <${FilterBar}>
                <input type="text" class="filter-input" placeholder="Search players..." value=${search} onInput=${(e) => { setSearch(e.target.value); setPage(1); }} />
                <div class="gender-toggle">
                    ${genderFilters.map(gf => html`
                        <button class=${'quick-filter-btn' + (genderFilter === gf.id ? ' active' : '')} onClick=${() => { setGenderFilter(gf.id); setPage(1); }}>${gf.label}</button>
                    `)}
                </div>
                <span class="filter-count">${filtered.length} players</span>
            <//>
            <div class="table-container">
                <table class="data-table players-table">
                    <thead>
                        <tr>
                            <th class="sticky-col">Player</th>
                            <th>Team</th>
                            ${columns.map(c => html`
                                <th class="sortable-th" onClick=${() => handleSort(c.key)}>
                                    ${c.label} ${sortCol === c.key ? (sortAsc ? '▲' : '▼') : ''}
                                </th>
                            `)}
                        </tr>
                    </thead>
                    <tbody>
                        ${pageData.map(p => html`
                            <tr>
                                <td class="sticky-col">
                                    <span class="player-link" onClick=${() => showPlayerDetail(p['Player ID'] || p.Player)}>${p.Player}</span>
                                    ${p.Gender === 'W' ? html` <span class="gender-tag">(W)</span>` : null}
                                    ${p.NBA ? html` <span class="badge badge-nba">NBA</span>` : null}
                                    ${p.WNBA ? html` <span class="badge badge-wnba">WNBA</span>` : null}
                                </td>
                                <td>${p.Team}</td>
                                ${columns.map(c => html`
                                    <td class=${c.threshold ? getStatClass(p[c.key] || 0, c.threshold) : ''}>${c.fmt(p[c.key])}</td>
                                `)}
                            </tr>
                        `)}
                    </tbody>
                </table>
            </div>
            <${Pagination} page=${page} pageSize=${pageSize} total=${filtered.length} onPageChange=${setPage} />
        </div>
    `;
}

function StatLeaders({ showPlayerDetail }) {
    const [genderFilter, setGenderFilter] = useState('');
    const [minGames, setMinGames] = useState(2);

    const categories = [
        { key: 'PPG', label: 'Points Per Game', format: v => v.toFixed(1) },
        { key: 'RPG', label: 'Rebounds Per Game', format: v => v.toFixed(1) },
        { key: 'APG', label: 'Assists Per Game', format: v => v.toFixed(1) },
        { key: 'SPG', label: 'Steals Per Game', format: v => v.toFixed(1) },
        { key: 'BPG', label: 'Blocks Per Game', format: v => v.toFixed(1) },
        { key: 'FG%', label: 'Field Goal %', format: v => (v * 100).toFixed(1) + '%' },
        { key: '3P%', label: 'Three-Point %', format: v => (v * 100).toFixed(1) + '%' },
        { key: 'FT%', label: 'Free Throw %', format: v => (v * 100).toFixed(1) + '%' },
        { key: 'Total PTS', label: 'Total Points', format: v => v.toLocaleString() },
        { key: 'Total REB', label: 'Total Rebounds', format: v => v.toLocaleString() },
        { key: 'Total AST', label: 'Total Assists', format: v => v.toLocaleString() },
        { key: 'Best Game Score', label: 'Best Game Score', format: v => v.toFixed(1) },
    ];

    const players = useMemo(() => {
        let data = DATA.players || [];
        if (genderFilter) data = data.filter(p => p.Gender === genderFilter);
        return data.filter(p => (p.Games || 0) >= minGames);
    }, [genderFilter, minGames]);

    return html`
        <div>
            <${FilterBar}>
                <div class="gender-toggle">
                    ${[{id:'',label:'All'},{id:'M',label:"Men's"},{id:'W',label:"Women's"}].map(gf => html`
                        <button class=${'quick-filter-btn' + (genderFilter === gf.id ? ' active' : '')} onClick=${() => setGenderFilter(gf.id)}>${gf.label}</button>
                    `)}
                </div>
                <label>Min Games: <input type="number" class="filter-input" style="width:60px" value=${minGames} min="1" onChange=${(e) => setMinGames(parseInt(e.target.value) || 1)} /></label>
            <//>
            <div class="leaders-grid">
                ${categories.map(cat => {
                    const sorted = [...players]
                        .filter(p => p[cat.key] != null && !isNaN(p[cat.key]))
                        .sort((a, b) => b[cat.key] - a[cat.key])
                        .slice(0, 5);
                    if (!sorted.length) return null;
                    return html`
                        <div class="leader-card">
                            <h4>${cat.label}</h4>
                            <ul class="leader-list">
                                ${sorted.map((p, i) => html`
                                    <li class="leader-item" onClick=${() => showPlayerDetail(p['Player ID'] || p.Player)}>
                                        <span class="leader-rank">${i + 1}</span>
                                        <span class="leader-name">${p.Player}</span>
                                        <span class="leader-team">${p.Team}</span>
                                        <span class="leader-value">${cat.format(p[cat.key])}</span>
                                    </li>
                                `)}
                            </ul>
                        </div>
                    `;
                })}
            </div>
        </div>
    `;
}

function CareerHighs({ showPlayerDetail }) {
    const seasonHighs = DATA.seasonHighs || [];
    const [sortCol, setSortCol] = useState('High PTS');
    const [sortAsc, setSortAsc] = useState(false);
    const [search, setSearch] = useState('');

    const filtered = useMemo(() => {
        let data = [...seasonHighs];
        if (search) {
            const q = search.toLowerCase();
            data = data.filter(h => (h.Player || '').toLowerCase().includes(q) || (h.Team || '').toLowerCase().includes(q));
        }
        return data.sort((a, b) => {
            const va = a[sortCol] || 0;
            const vb = b[sortCol] || 0;
            return sortAsc ? va - vb : vb - va;
        });
    }, [seasonHighs, sortCol, sortAsc, search]);

    const handleSort = (col) => {
        if (sortCol === col) setSortAsc(!sortAsc);
        else { setSortCol(col); setSortAsc(false); }
    };

    const SortTh = ({ col, label }) => html`
        <th onClick=${() => handleSort(col)} style="cursor:pointer">
            ${label} ${sortCol === col ? (sortAsc ? '▲' : '▼') : ''}
        </th>
    `;

    if (!seasonHighs.length) return html`<${EmptyState} title="No season highs data" />`;

    return html`
        <div>
            <h3>Career Highs</h3>
            <${FilterBar}>
                <input type="text" class="filter-input" placeholder="Search players..." value=${search} onInput=${(e) => setSearch(e.target.value)} />
                <span class="filter-count">${filtered.length} players</span>
            <//>
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Player</th>
                            <th>Team</th>
                            <${SortTh} col="High PTS" label="PTS" />
                            <th>Game</th>
                            <${SortTh} col="High REB" label="REB" />
                            <th>Game</th>
                            <${SortTh} col="High AST" label="AST" />
                            <th>Game</th>
                            <${SortTh} col="High 3PM" label="3PM" />
                            <${SortTh} col="Best Game Score" label="GmSc" />
                        </tr>
                    </thead>
                    <tbody>
                        ${filtered.map(h => html`
                            <tr>
                                <td><span class="player-link" onClick=${() => showPlayerDetail(h['Player ID'] || h.Player)}>${h.Player}</span></td>
                                <td>${h.Team || ''}</td>
                                <td class=${(h['High PTS'] || 0) >= 20 ? 'stat-excellent' : (h['High PTS'] || 0) >= 15 ? 'stat-good' : ''}>${h['High PTS'] || 0}</td>
                                <td class="text-muted">${h['PTS Opponent'] ? `vs ${h['PTS Opponent']}` : ''}</td>
                                <td class=${(h['High REB'] || 0) >= 10 ? 'stat-excellent' : (h['High REB'] || 0) >= 7 ? 'stat-good' : ''}>${h['High REB'] || 0}</td>
                                <td class="text-muted">${h['REB Opponent'] ? `vs ${h['REB Opponent']}` : ''}</td>
                                <td class=${(h['High AST'] || 0) >= 7 ? 'stat-excellent' : (h['High AST'] || 0) >= 5 ? 'stat-good' : ''}>${h['High AST'] || 0}</td>
                                <td class="text-muted">${h['AST Opponent'] ? `vs ${h['AST Opponent']}` : ''}</td>
                                <td>${h['High 3PM'] || 0}</td>
                                <td>${h['Best Game Score'] != null ? h['Best Game Score'].toFixed(1) : '-'}</td>
                            </tr>
                        `)}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function PlayerGameLogs({ showPlayerDetail, showGameDetail }) {
    const [search, setSearch] = useState('');
    const [selectedPlayer, setSelectedPlayer] = useState(null);
    const allPlayers = DATA.players || [];

    const suggestions = useMemo(() => {
        if (search.length < 2) return [];
        const q = search.toLowerCase();
        return allPlayers.filter(p => (p.Player || '').toLowerCase().includes(q)).slice(0, 10);
    }, [search, allPlayers]);

    const gameLogs = useMemo(() => {
        if (!selectedPlayer) return [];
        const playerId = selectedPlayer['Player ID'] || selectedPlayer.Player;
        return (DATA.playerGames || [])
            .filter(g => (g.player_id || g.player) === playerId)
            .sort((a, b) => (b.date_yyyymmdd || b.date || '').localeCompare(a.date_yyyymmdd || a.date || ''));
    }, [selectedPlayer]);

    return html`
        <div>
            <${FilterBar}>
                <div class="global-search-container" style="position:relative; max-width:300px;">
                    <input type="text" class="filter-input" placeholder="Search for a player..."
                        value=${search}
                        onInput=${(e) => { setSearch(e.target.value); if (!e.target.value) setSelectedPlayer(null); }}
                    />
                    ${suggestions.length > 0 && !selectedPlayer && html`
                        <div class="search-results" style="display:block; top:100%; left:0; right:0;">
                            ${suggestions.map(p => html`
                                <div class="search-result-item" onClick=${() => { setSelectedPlayer(p); setSearch(p.Player); }}>
                                    <span class="search-result-icon">👤</span>
                                    <div class="search-result-text">
                                        <div class="search-result-title">${p.Player}</div>
                                        <div class="search-result-subtitle">${p.Team} - ${(p.PPG||0).toFixed(1)} PPG</div>
                                    </div>
                                </div>
                            `)}
                        </div>
                    `}
                </div>
            <//>

            ${selectedPlayer && html`
                <h3 style="margin: var(--space-3) 0">${selectedPlayer.Player} — ${selectedPlayer.Team}${selectedPlayer.Gender === 'W' ? ' (W)' : ''}</h3>
                ${gameLogs.length === 0
                    ? html`<${EmptyState} title="No game logs found" />`
                    : html`
                        <div class="table-container">
                            <table class="data-table">
                                <thead><tr><th>Date</th><th>Opp</th><th>Result</th><th>MIN</th><th>PTS</th><th>REB</th><th>AST</th><th>STL</th><th>BLK</th><th>FG</th><th>3P</th><th>FT</th><th>GmSc</th></tr></thead>
                                <tbody>
                                    ${gameLogs.map(g => html`
                                        <tr class="clickable-row" onClick=${() => showGameDetail(g.game_id)}>
                                            <td><span class="game-link">${g.date}</span></td>
                                            <td>${g.opponent}</td>
                                            <td>${g.result} ${g.score || ''}</td>
                                            <td>${formatMinutes(g.mp)}</td>
                                            <td class=${(g.pts||0) >= 20 ? 'stat-excellent' : ''}>${g.pts || 0}</td>
                                            <td>${g.trb || 0}</td>
                                            <td>${g.ast || 0}</td>
                                            <td>${g.stl || 0}</td>
                                            <td>${g.blk || 0}</td>
                                            <td>${g.fg || 0}-${g.fga || 0}</td>
                                            <td>${g.fg3 || 0}-${g.fg3a || 0}</td>
                                            <td>${g.ft || 0}-${g.fta || 0}</td>
                                            <td>${g.game_score != null ? g.game_score.toFixed(1) : '-'}</td>
                                        </tr>
                                    `)}
                                </tbody>
                            </table>
                        </div>
                    `
                }
            `}

            ${!selectedPlayer && html`<${EmptyState} icon="🔍" title="Search for a player" message="Type a player name to view their game log" />`}
        </div>
    `;
}

function PlayerRecords({ showPlayerDetail }) {
    const playerGames = DATA.playerGames || [];
    const records = useMemo(() => {
        // Build per-game records
        const byPts = [...playerGames].sort((a, b) => (b.pts||0) - (a.pts||0)).slice(0, 10);
        const byReb = [...playerGames].sort((a, b) => (b.trb||0) - (a.trb||0)).slice(0, 10);
        const byAst = [...playerGames].sort((a, b) => (b.ast||0) - (a.ast||0)).slice(0, 10);
        const byStl = [...playerGames].sort((a, b) => (b.stl||0) - (a.stl||0)).slice(0, 10);
        const byBlk = [...playerGames].sort((a, b) => (b.blk||0) - (a.blk||0)).slice(0, 10);
        const byGmSc = [...playerGames].filter(p => p.game_score != null).sort((a, b) => (b.game_score||0) - (a.game_score||0)).slice(0, 10);
        return { byPts, byReb, byAst, byStl, byBlk, byGmSc };
    }, [playerGames]);

    const RecordList = ({ items, statKey, label, format }) => html`
        <${Card} className="record-card">
            <h3>${label}</h3>
            ${items.map((p, i) => html`
                <div class="record-item" onClick=${() => showPlayerDetail(p.player_id || p.player)}>
                    <span class="rank">${i + 1}.</span>
                    <span class="teams">
                        <span class="player-link">${p.player}</span>
                        <span style="color: var(--text-muted); font-size: 0.8125rem"> (${p.team}) vs ${p.opponent}, ${p.date}</span>
                    </span>
                    <span class="score">${format ? format(p[statKey]) : p[statKey] || 0}</span>
                </div>
            `)}
        <//>
    `;

    return html`
        <div class="records-grid">
            <${RecordList} items=${records.byPts} statKey="pts" label="Most Points" />
            <${RecordList} items=${records.byReb} statKey="trb" label="Most Rebounds" />
            <${RecordList} items=${records.byAst} statKey="ast" label="Most Assists" />
            <${RecordList} items=${records.byStl} statKey="stl" label="Most Steals" />
            <${RecordList} items=${records.byBlk} statKey="blk" label="Most Blocks" />
            <${RecordList} items=${records.byGmSc} statKey="game_score" label="Best Game Score" format=${v => v != null ? v.toFixed(1) : '-'} />
        </div>
    `;
}

function FuturePros({ showPlayerDetail }) {
    const [search, setSearch] = useState('');
    const [quickFilter, setQuickFilter] = useState('all');

    const allPros = useMemo(() => (DATA.players || []).filter(p => p.NBA || p.WNBA || p.International), []);
    const filtered = useMemo(() => {
        let data = [...allPros];
        if (search) {
            const q = search.toLowerCase();
            data = data.filter(p => (p.Player||'').toLowerCase().includes(q) || (p.Team||'').toLowerCase().includes(q));
        }
        if (quickFilter === 'nba') data = data.filter(p => p.NBA);
        if (quickFilter === 'wnba') data = data.filter(p => p.WNBA);
        if (quickFilter === 'intl') data = data.filter(p => p.Intl_Pro);
        if (quickFilter === 'active') data = data.filter(p => p.NBA_Active || p.WNBA_Active);
        if (quickFilter === 'drafted') data = data.filter(p => p.Draft_Round);
        return data;
    }, [allPros, search, quickFilter]);

    const quickFilters = [
        { id: 'all', label: 'All', count: allPros.length },
        { id: 'nba', label: 'NBA' },
        { id: 'wnba', label: 'WNBA' },
        { id: 'intl', label: 'International' },
        { id: 'active', label: 'Active' },
        { id: 'drafted', label: 'Drafted' },
    ];

    return html`
        <div>
            <${FilterBar}>
                <input type="text" class="filter-input" placeholder="Search future pros..." value=${search} onInput=${(e) => setSearch(e.target.value)} />
                <${QuickFilters} filters=${quickFilters} active=${quickFilter} onSelect=${setQuickFilter} />
            <//>
            <p class="filter-count">${filtered.length} of ${allPros.length} future pros</p>
            <div class="future-pros-grid">
                ${filtered.map(p => {
                    let league = '';
                    if (p.NBA) league = 'NBA';
                    else if (p.WNBA) league = 'WNBA';
                    else if (p.Intl_Pro) league = 'Intl';
                    let draft = '';
                    if (p.Draft_Round) draft = `R${p.Draft_Round} P${p.Draft_Pick} (${p.Draft_Year || ''})`;
                    else if (p.Undrafted) draft = 'UDFA';
                    const proGames = p.Proballers_Games || (p.NBA_Games || 0) + (p.WNBA_Games || 0);
                    const logoUrl = getTeamLogoUrl(p.Team);
                    return html`
                        <div class="future-pro-card" onClick=${() => showPlayerDetail(p['Player ID'] || p.Player)}>
                            <div class="fp-card-top">
                                ${logoUrl ? html`<img src=${logoUrl} class="fp-team-logo" alt="" />` : null}
                                <div class="fp-badges">
                                    ${p.NBA ? html`<span class="badge badge-nba">NBA</span>` : null}
                                    ${p.WNBA ? html`<span class="badge badge-wnba">WNBA</span>` : null}
                                    ${p.Intl_Pro ? html`<span class="badge badge-intl">INTL</span>` : null}
                                    ${(p.NBA_Active || p.WNBA_Active) ? html`<span class="badge badge-active-pro">Active</span>` : null}
                                </div>
                            </div>
                            <div class="fp-name">${p.Player}</div>
                            <div class="fp-team">${p.Team}</div>
                            ${draft ? html`<div class="fp-draft">${draft}</div>` : null}
                            <div class="fp-stats-row">
                                <div class="fp-stat">
                                    <span class="fp-stat-value">${proGames || '-'}</span>
                                    <span class="fp-stat-label">Pro Games</span>
                                </div>
                                <div class="fp-stat">
                                    <span class="fp-stat-value">${p.Games || 0}</span>
                                    <span class="fp-stat-label">Seen</span>
                                </div>
                                <div class="fp-stat">
                                    <span class="fp-stat-value">${(p.PPG || 0).toFixed(1)}</span>
                                    <span class="fp-stat-label">PPG</span>
                                </div>
                            </div>
                        </div>
                    `;
                })}
            </div>
        </div>
    `;
}

function Achievements({ showGameDetail }) {
    const milestones = DATA.milestones || {};
    const summary = DATA.summary?.milestones || {};
    const [activeType, setActiveType] = useState(null);

    const milestoneTypes = [
        { key: 'double_doubles', label: 'Double-Doubles', icon: '✌️' },
        { key: 'triple_doubles', label: 'Triple-Doubles', icon: '🔥' },
        { key: 'twenty_point_games', label: '20+ Points', icon: '🎯' },
        { key: 'thirty_point_games', label: '30+ Points', icon: '💥' },
        { key: 'forty_point_games', label: '40+ Points', icon: '🌟' },
        { key: 'ten_rebound_games', label: '10+ Rebounds', icon: '🏀' },
        { key: 'fifteen_rebound_games', label: '15+ Rebounds', icon: '💪' },
        { key: 'ten_assist_games', label: '10+ Assists', icon: '🤝' },
        { key: 'five_block_games', label: '5+ Blocks', icon: '🚫' },
        { key: 'five_steal_games', label: '5+ Steals', icon: '🔒' },
        { key: 'five_three_games', label: '5+ Threes', icon: '🎯' },
        { key: 'hot_shooting_games', label: 'Hot Shooting', icon: '🔥' },
        { key: 'perfect_ft_games', label: 'Perfect FT', icon: '✅' },
        { key: 'twenty_ten_games', label: '20-10 Games', icon: '⭐' },
    ];

    const activeEntries = useMemo(() => {
        if (!activeType) return [];
        const entries = [...(milestones[activeType] || [])];
        entries.sort((a, b) => (b.GameID || '').localeCompare(a.GameID || ''));
        return entries;
    }, [activeType, milestones]);

    // Badge tracking data from computeGameMilestones
    const tracking = window.badgeTrackingData || {};

    return html`
        <div>
            <h3>Achievement Summary</h3>
            <div class="badge-grid">
                ${milestoneTypes.map(mt => {
                    const count = summary[mt.key] || 0;
                    if (count === 0) return null;
                    return html`
                        <div class=${'badge-card' + (activeType === mt.key ? ' active' : '')}
                            onClick=${() => setActiveType(activeType === mt.key ? null : mt.key)}>
                            <div class="badge-icon">${mt.icon}</div>
                            <div class="badge-count">${count}</div>
                            <div class="badge-label">${mt.label}</div>
                        </div>
                    `;
                })}
            </div>

            ${tracking.statesSeen && html`
                <div class="achievement-extras" style="margin-top: var(--space-4)">
                    <div class="badge-grid">
                        <div class="badge-card">
                            <div class="badge-icon">🗺️</div>
                            <div class="badge-count">${tracking.statesSeen.size || 0}</div>
                            <div class="badge-label">States</div>
                        </div>
                        <div class="badge-card">
                            <div class="badge-icon">🏟️</div>
                            <div class="badge-count">${tracking.venueOrder?.length || 0}</div>
                            <div class="badge-label">Venues</div>
                        </div>
                        <div class="badge-card">
                            <div class="badge-icon">🔥</div>
                            <div class="badge-count">${tracking.maxStreak || 0}</div>
                            <div class="badge-label">Max Streak</div>
                        </div>
                    </div>
                </div>
            `}

            ${activeType && html`
                <div style="margin-top: var(--space-4)">
                    <h3>${milestoneTypes.find(m => m.key === activeType)?.label || activeType} (${activeEntries.length})</h3>
                    ${activeEntries.length === 0
                        ? html`<${EmptyState} title="No entries" />`
                        : html`
                            <div class="table-container">
                                <table class="data-table">
                                    <thead><tr><th>Date</th><th>Player</th><th>Team</th><th>Opponent</th><th>Detail</th></tr></thead>
                                    <tbody>
                                        ${activeEntries.map(e => html`
                                            <tr class="clickable-row" onClick=${() => e.GameID && showGameDetail(e.GameID)}>
                                                <td>${e.Date}</td>
                                                <td>${e.Player}${e.Gender === 'W' ? ' (W)' : ''}</td>
                                                <td>${e.Team}</td>
                                                <td>${e.Opponent || ''}</td>
                                                <td>${e.Detail || ''}</td>
                                            </tr>
                                        `)}
                                    </tbody>
                                </table>
                            </div>
                        `
                    }
                </div>
            `}
        </div>
    `;
}

function VenuesView({ showVenueDetail }) {
    const venues = DATA.venues || [];
    const unvisited = DATA.unvisitedHomeArenas || [];
    const mapRef = useRef(null);
    const mapInstance = useRef(null);
    const markersRef = useRef({ visited: [], unvisited: [] });
    const [quickFilter, setQuickFilter] = useState('all');
    const [search, setSearch] = useState('');
    const [showUnvisited, setShowUnvisited] = useState(false);

    const filtered = useMemo(() => {
        let result = [...venues];
        if (search) {
            const q = search.toLowerCase();
            result = result.filter(v => `${v.Venue} ${v.City} ${v.State}`.toLowerCase().includes(q));
        }
        if (quickFilter === 'd1') result = result.filter(v => (v.Division || 'D1') === 'D1');
        if (quickFilter === 'neutral') result = result.filter(v => NEUTRAL_SITES.has(v.Venue));
        if (quickFilter === 'home') result = result.filter(v => !NEUTRAL_SITES.has(v.Venue));
        if (quickFilter === 'historic') result = result.filter(v => v.Status === 'Historic');
        return result;
    }, [venues, search, quickFilter]);

    // Venue stats
    const stats = useMemo(() => {
        const statesSet = new Set();
        let homeCount = 0, neutralCount = 0, historicCount = 0;
        filtered.forEach(v => {
            if (v.State) statesSet.add(v.State);
            if (NEUTRAL_SITES.has(v.Venue)) neutralCount++;
            else homeCount++;
            if (v.Status === 'Historic') historicCount++;
        });
        return { total: filtered.length, home: homeCount, neutral: neutralCount, states: statesSet.size, historic: historicCount };
    }, [filtered]);

    // Create custom icon helper
    const createTeamIcon = (teamName, espnId, color) => {
        const logoUrl = espnId ? getEspnLogoUrl(espnId) : getTeamLogoUrl(teamName);
        if (logoUrl) {
            return L.divIcon({
                className: 'venue-marker-icon',
                html: `<div style="width:32px;height:32px;border-radius:50%;border:3px solid ${color};background:#fff;overflow:hidden;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.3);">
                    <img src="${logoUrl}" style="width:24px;height:24px;object-fit:contain;" onerror="this.style.display='none'" />
                </div>`,
                iconSize: [32, 32],
                iconAnchor: [16, 16],
                popupAnchor: [0, -16]
            });
        }
        return L.divIcon({
            className: 'venue-marker-icon',
            html: `<div style="width:14px;height:14px;border-radius:50%;border:2px solid #fff;background:${color};box-shadow:0 2px 4px rgba(0,0,0,0.3);"></div>`,
            iconSize: [14, 14],
            iconAnchor: [7, 7],
            popupAnchor: [0, -7]
        });
    };

    // Init map
    useEffect(() => {
        if (mapInstance.current || !mapRef.current) return;
        const timer = requestAnimationFrame(() => {
            if (!mapRef.current) return;
            const map = L.map(mapRef.current).setView([39.8283, -98.5795], 4);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 18,
                attribution: '&copy; OpenStreetMap contributors'
            }).addTo(map);
            mapInstance.current = map;

            // Visited venue markers (green)
            venues.forEach(venue => {
                const coords = VENUE_COORDS[venue.Venue];
                let markerCoords = coords;
                if (!coords) {
                    const stateAbbr = STATE_ABBREV[venue.State];
                    const cityKey = stateAbbr ? `${venue.City}, ${stateAbbr}` : venue.City;
                    markerCoords = CITY_COORDS[cityKey];
                    if (!markerCoords) return;
                }
                const isNeutral = NEUTRAL_SITES.has(venue.Venue);
                const isHistoric = venue.Status === 'Historic';
                const color = isHistoric ? '#a855f7' : isNeutral ? '#f59e0b' : '#16a34a';
                const icon = createTeamIcon(venue['Home Team'], null, color);
                const marker = L.marker(markerCoords, { icon }).bindPopup(
                    `<strong>${venue.Venue}</strong>${isNeutral ? ' (Neutral)' : ''}${isHistoric ? ' (Historic)' : ''}<br>${venue.City}, ${venue.State}<br>${venue.Games || 0} games`
                ).addTo(map);
                markersRef.current.visited.push(marker);
            });

            // Unvisited venue markers (gray) — hidden by default
            unvisited.forEach(uv => {
                const coords = VENUE_COORDS[uv.venue] || SCHOOL_COORDS[uv.team];
                if (!coords) return;
                const icon = createTeamIcon(uv.team, uv.espnId, '#9ca3af');
                const marker = L.marker(coords, { icon }).bindPopup(
                    `<strong>${uv.venue}</strong> (Not visited)<br>${uv.city}, ${uv.state}<br>${uv.team} — ${uv.conference}`
                );
                markersRef.current.unvisited.push(marker);
            });

            setTimeout(() => map.invalidateSize(), 100);
        });
        return () => cancelAnimationFrame(timer);
    }, []);

    // Toggle unvisited markers (hide visited when showing unvisited)
    useEffect(() => {
        const map = mapInstance.current;
        if (!map) return;
        markersRef.current.unvisited.forEach(m => {
            if (showUnvisited) m.addTo(map);
            else map.removeLayer(m);
        });
        markersRef.current.visited.forEach(m => {
            if (showUnvisited) map.removeLayer(m);
            else m.addTo(map);
        });
    }, [showUnvisited]);

    const quickFilters = [
        { id: 'all', label: 'All', count: venues.length },
        { id: 'd1', label: 'D1' },
        { id: 'home', label: 'Home' },
        { id: 'neutral', label: 'Neutral' },
        { id: 'historic', label: 'Historic' },
    ];

    return html`
        <div>
            <div class="venue-stats-summary">
                <${StatBox} label="Venues" value=${stats.total} />
                <${StatBox} label="Home" value=${stats.home} />
                <${StatBox} label="Neutral" value=${stats.neutral} />
                <${StatBox} label="States" value=${stats.states} />
            </div>

            <div style="position:relative;">
                <div class="map-container" style="height: 400px; border-radius: var(--radius-lg); overflow: hidden; margin-bottom: var(--space-4);">
                    <div ref=${mapRef} style="width: 100%; height: 100%;"></div>
                </div>
                <div class="map-toggle" style="position:absolute;top:10px;right:10px;z-index:1000;">
                    <button class=${'map-toggle-btn' + (showUnvisited ? ' active' : '')} onClick=${() => setShowUnvisited(!showUnvisited)}>
                        ${showUnvisited ? 'Show Visited' : 'Show Unvisited'} (${showUnvisited ? venues.length : unvisited.length})
                    </button>
                </div>
                <div class="map-legend" style="position:absolute;bottom:30px;left:10px;z-index:1000;background:var(--bg-card);padding:8px 12px;border-radius:var(--radius-md);font-size:0.75rem;box-shadow:var(--shadow-sm);">
                    <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
                        <span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#16a34a;margin-right:4px;"></span>Visited</span>
                        <span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#f59e0b;margin-right:4px;"></span>Neutral</span>
                        <span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#a855f7;margin-right:4px;"></span>Historic</span>
                        ${showUnvisited && html`<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#9ca3af;margin-right:4px;"></span>Unvisited</span>`}
                    </div>
                </div>
            </div>

            <${FilterBar}>
                <${QuickFilters} filters=${quickFilters} active=${quickFilter} onSelect=${setQuickFilter} />
                <input type="text" class="filter-input" placeholder="Search venues..." value=${search} onInput=${(e) => setSearch(e.target.value)} />
            <//>

            <div class="venue-cards-grid">
                ${filtered.map(v => {
                    const logoUrl = getTeamLogoUrl(v['Home Team']);
                    const isNeutral = NEUTRAL_SITES.has(v.Venue);
                    const isHistoric = v.Status === 'Historic';
                    const homeWins = v['Home Wins'] || 0;
                    const awayWins = v['Away Wins'] || 0;
                    const games = v.Games || 0;
                    return html`
                        <div class=${'venue-card' + (isHistoric ? ' venue-card-historic' : '')} onClick=${() => showVenueDetail(v.Venue)}>
                            <div class="venue-card-header">
                                ${logoUrl ? html`<img src=${logoUrl} class="venue-card-logo" alt="" />` : null}
                                <div class="venue-card-badges">
                                    <span class=${'badge badge-div-' + (v.Division || 'D1').toLowerCase()}>${v.Division || 'D1'}</span>
                                    ${isNeutral ? html`<span class="neutral-badge">N</span>` : null}
                                    ${isHistoric ? html`<span class="badge badge-historic">Historic</span>` : null}
                                </div>
                            </div>
                            <div class="venue-card-name">${v.Venue}</div>
                            <div class="venue-card-location">${v.City || ''}${v.State ? ', ' + v.State : ''}</div>
                            <div class="venue-card-stats">
                                <div class="venue-card-stat">
                                    <span class="venue-card-stat-value">${games}</span>
                                    <span class="venue-card-stat-label">Games</span>
                                </div>
                                <div class="venue-card-stat">
                                    <span class="venue-card-stat-value stat-good">${homeWins}</span>
                                    <span class="venue-card-stat-label">Home W</span>
                                </div>
                                <div class="venue-card-stat">
                                    <span class="venue-card-stat-value">${awayWins}</span>
                                    <span class="venue-card-stat-label">Away W</span>
                                </div>
                            </div>
                            <div class="venue-card-scoring">
                                ${(v['Avg Home Pts'] || 0).toFixed(1)} - ${(v['Avg Away Pts'] || 0).toFixed(1)} avg
                            </div>
                        </div>
                    `;
                })}
            </div>
        </div>
    `;
}

function SchoolMapView() {
    const mapRef = useRef(null);
    const mapInstance = useRef(null);
    const [confFilter, setConfFilter] = useState('');

    const conferences = useMemo(() => {
        const checklist = DATA.conferenceChecklist || {};
        return Object.keys(checklist).filter(c => c !== 'All D1' && c !== 'Historical/Other').sort();
    }, []);

    useEffect(() => {
        if (mapInstance.current || !mapRef.current) return;
        // Delay init to ensure container is visible
        const timer = requestAnimationFrame(() => {
            if (!mapRef.current) return;
            const map = L.map(mapRef.current).setView([39.8283, -98.5795], 4);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 18,
                attribution: '&copy; OpenStreetMap contributors'
            }).addTo(map);
            mapInstance.current = map;

            // Add school markers
            const checklist = DATA.conferenceChecklist || {};
            const tracking = window.badgeTrackingData || {};
            const teamCounts = tracking.teamCounts || {};

            for (const [confName, confData] of Object.entries(checklist)) {
                if (confName === 'All D1' || confName === 'Historical/Other') continue;
                (confData.teams || []).forEach(team => {
                    const coords = SCHOOL_COORDS[team.team];
                    if (!coords) return;

                    const seenM = teamCounts[`${team.team}|M`] > 0;
                    const seenW = teamCounts[`${team.team}|W`] > 0;
                    const seen = seenM || seenW;

                    // Use ESPN logo for icon
                    let iconUrl = null;
                    if (team.espnId) {
                        iconUrl = `https://a.espncdn.com/i/teamlogos/ncaa/500/${team.espnId}.png`;
                    } else if (CUSTOM_LOGOS[team.team]) {
                        iconUrl = CUSTOM_LOGOS[team.team];
                    }

                    const icon = iconUrl ? L.icon({
                        iconUrl,
                        iconSize: seen ? [28, 28] : [18, 18],
                        className: seen ? 'school-marker-seen' : 'school-marker-unseen',
                    }) : L.divIcon({
                        className: seen ? 'school-dot seen' : 'school-dot unseen',
                        iconSize: seen ? [12, 12] : [8, 8],
                    });

                    const marker = L.marker(coords, { icon });
                    const genderInfo = seenM && seenW ? '(M+W)' : seenM ? '(M)' : seenW ? '(W)' : '';
                    marker.bindPopup(`<strong>${team.team}</strong><br>${confName}${seen ? `<br>Seen ${genderInfo}` : '<br><em>Not yet seen</em>'}`);
                    marker.conf = confName;
                    marker.addTo(map);
                });
            }

            setTimeout(() => map.invalidateSize(), 100);
        });
        return () => cancelAnimationFrame(timer);
    }, []);

    // Handle conference filter
    useEffect(() => {
        if (!mapInstance.current) return;
        mapInstance.current.eachLayer(layer => {
            if (layer instanceof L.Marker) {
                if (!confFilter || layer.conf === confFilter) {
                    layer.setOpacity(1);
                } else {
                    layer.setOpacity(0.1);
                }
            }
        });
    }, [confFilter]);

    return html`
        <div>
            <${FilterBar}>
                <select class="filter-select" value=${confFilter} onChange=${(e) => setConfFilter(e.target.value)}>
                    <option value="">All Conferences</option>
                    ${conferences.map(c => html`<option value=${c}>${c}</option>`)}
                </select>
            <//>
            <div class="map-container" style="height: 600px; border-radius: var(--radius-lg); overflow: hidden;">
                <div ref=${mapRef} style="width: 100%; height: 100%;"></div>
            </div>
        </div>
    `;
}

function ConferenceProgress() {
    const checklist = DATA.conferenceChecklist || {};
    const [genderFilter, setGenderFilter] = useState('');
    const [search, setSearch] = useState('');
    const [selectedConf, setSelectedConf] = useState(null);

    const tracking = window.badgeTrackingData || {};
    const confTeamsSeen = tracking.confTeamsSeen || {};

    const conferences = useMemo(() => {
        return Object.entries(checklist)
            .filter(([name]) => name !== 'All D1' && name !== 'Historical/Other')
            .map(([name, data]) => {
                const totalTeams = data.totalTeams || 0;
                const teams = data.teams || [];
                const teamsSeen = genderFilter === 'M' ? (data.teamsSeenM || 0) : genderFilter === 'W' ? (data.teamsSeenW || 0) : (data.teamsSeen || 0);
                const venuesVisited = genderFilter === 'M' ? (data.venuesVisitedM || 0) : genderFilter === 'W' ? (data.venuesVisitedW || 0) : (data.venuesVisited || 0);
                const totalVenues = data.totalVenues || totalTeams;
                const teamPct = totalTeams > 0 ? teamsSeen / totalTeams : 0;
                const venuePct = totalVenues > 0 ? venuesVisited / totalVenues : 0;
                return { name, totalTeams, teams, teamsSeen, venuesVisited, totalVenues, teamPct, venuePct };
            })
            .filter(c => {
                if (search) {
                    const q = search.toLowerCase();
                    if (!c.name.toLowerCase().includes(q)) return false;
                }
                return true;
            })
            .sort((a, b) => b.teamPct - a.teamPct || a.name.localeCompare(b.name));
    }, [checklist, genderFilter, search]);

    return html`
        <div>
            <${FilterBar}>
                <input type="text" class="filter-input" placeholder="Search conferences..." value=${search} onInput=${(e) => setSearch(e.target.value)} />
                <div class="gender-toggle">
                    ${[{id:'',label:'All'},{id:'M',label:"Men's"},{id:'W',label:"Women's"}].map(gf => html`
                        <button class=${'quick-filter-btn' + (genderFilter === gf.id ? ' active' : '')} onClick=${() => setGenderFilter(gf.id)}>${gf.label}</button>
                    `)}
                </div>
            <//>

            <div class="conference-grid">
                ${conferences.map(c => html`
                    <div class=${'conference-card' + (c.teamPct >= 1 ? ' complete' : '')} onClick=${() => setSelectedConf(selectedConf === c.name ? null : c.name)}>
                        <div class="conference-card-header">
                            <h4>${c.name}</h4>
                        </div>
                        <div class="conf-stat-row">
                            <span class="conf-stat-label">Teams</span>
                            <span class="conference-count">${c.teamsSeen}/${c.totalTeams}</span>
                        </div>
                        <div class="progress-bar" style="margin-bottom:6px">
                            <div class="progress-fill" style="width: ${(c.teamPct * 100).toFixed(1)}%"></div>
                        </div>
                        <div class="conf-stat-row">
                            <span class="conf-stat-label">Venues</span>
                            <span class="conference-count venue-count">${c.venuesVisited}/${c.totalVenues}</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill venue-fill" style="width: ${(c.venuePct * 100).toFixed(1)}%"></div>
                        </div>
                    </div>
                `)}
            </div>

            ${selectedConf && html`
                <${Modal} id="conf-modal" active=${true} onClose=${() => setSelectedConf(null)} title=${selectedConf}>
                    <${ConferenceTeamsDetail} confName=${selectedConf} gender=${genderFilter} />
                <//>
            `}
        </div>
    `;
}

function ConferenceTeamsDetail({ confName, gender }) {
    const checklist = DATA.conferenceChecklist || {};
    const confData = checklist[confName] || {};
    const teams = confData.teams || [];

    const categorized = useMemo(() => {
        return teams.map(t => {
            const seen = gender === 'M' ? t.seenM : gender === 'W' ? t.seenW : t.seen;
            const visited = gender === 'M' ? t.arenaVisitedM : gender === 'W' ? t.arenaVisitedW : t.arenaVisited;
            const arena = gender === 'W' ? (t.homeArenaW || t.homeArena) : (t.homeArenaM || t.homeArena);
            return { ...t, seen, visited, arena };
        }).sort((a, b) => {
            if (a.seen !== b.seen) return a.seen ? -1 : 1;
            return a.team.localeCompare(b.team);
        });
    }, [teams, confName, gender]);

    const seenCount = categorized.filter(t => t.seen).length;
    const visitedCount = categorized.filter(t => t.visited).length;

    return html`
        <div>
            <div style="display:flex;gap:var(--space-4);margin-bottom:var(--space-3);font-size:0.9rem;">
                <span><strong>${seenCount}</strong> of ${teams.length} teams seen</span>
                <span><strong>${visitedCount}</strong> of ${teams.length} venues visited</span>
            </div>
            <div class="checklist-grid">
                ${categorized.map(t => html`
                    <div class=${'checklist-item' + (t.seen ? ' seen' : '')}>
                        <div class=${'check-icon' + (t.seen ? ' checked' : '')}>
                            ${t.seen ? '✓' : ''}
                        </div>
                        <div class="checklist-details">
                            <div class="checklist-team">
                                ${t.espnId ? html`<img src=${getEspnLogoUrl(t.espnId)} class="venue-team-logo" alt="" />` : null}
                                ${t.team}
                                ${!gender && t.seenM && html` <span class="gender-seen gender-m">M</span>`}
                                ${!gender && t.seenW && html` <span class="gender-seen gender-w">W</span>`}
                            </div>
                            ${t.arena && html`
                                <div class="checklist-venue">
                                    ${t.visited ? html`<span class="venue-visited-icon" title="Venue visited">🏟️</span>` : html`<span class="venue-not-visited" title="Not visited">○</span>`}
                                    ${t.arena}
                                </div>
                            `}
                        </div>
                    </div>
                `)}
            </div>
        </div>
    `;
}

function UpcomingView({ showGameDetail }) {
    const upcoming = DATA.upcomingGames || {};
    const gamesData = upcoming.games || [];
    const [search, setSearch] = useState('');
    const [stateFilter, setStateFilter] = useState('');
    const [genderFilter, setGenderFilter] = useState('');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');
    const [mapReady, setMapReady] = useState(false);
    const mapRef = useRef(null);
    const mapInstance = useRef(null);
    const markersRef = useRef([]);

    const states = useMemo(() => {
        const set = new Set();
        gamesData.forEach(g => { if (g.state) set.add(g.state); });
        return [...set].sort();
    }, [gamesData]);

    // Get unique dates for the date filter
    const uniqueDates = useMemo(() => {
        const dateSet = new Set();
        gamesData.forEach(g => {
            if (g.date) {
                const d = new Date(g.date);
                dateSet.add(d.toISOString().split('T')[0]);
            }
        });
        return [...dateSet].sort();
    }, [gamesData]);

    const filtered = useMemo(() => {
        let result = [...gamesData];
        if (search) {
            const q = search.toLowerCase().trim();
            // Check if query exactly matches any team name — if so, only show exact matches
            const allTeamNames = new Set();
            gamesData.forEach(g => {
                [g.home, g.homeTeam, g.homeTeamFull, g.away, g.awayTeam, g.awayTeamFull,
                 g.homeTeamAbbrev, g.awayTeamAbbrev].forEach(n => {
                    if (n) allTeamNames.add(n.toLowerCase());
                });
            });
            const isExact = allTeamNames.has(q);
            result = result.filter(g => {
                const teams = [g.home, g.homeTeam, g.homeTeamFull, g.away, g.awayTeam, g.awayTeamFull,
                    g.homeTeamAbbrev, g.awayTeamAbbrev].filter(Boolean);
                if (isExact) {
                    if (teams.some(t => t.toLowerCase() === q)) return true;
                } else {
                    if (teams.some(t => t.toLowerCase().startsWith(q))) return true;
                }
                const other = `${g.venue || ''} ${g.city || ''}`.toLowerCase();
                return other.includes(q);
            });
        }
        if (genderFilter) result = result.filter(g => g.gender === genderFilter);
        if (stateFilter) result = result.filter(g => g.state === stateFilter);
        if (dateFrom || dateTo) {
            result = result.filter(g => {
                if (!g.date) return false;
                const d = new Date(g.date).toISOString().split('T')[0];
                if (dateFrom && d < dateFrom) return false;
                if (dateTo && d > dateTo) return false;
                return true;
            });
        }
        return result.sort((a, b) => (a.date || '').localeCompare(b.date || ''));
    }, [gamesData, search, genderFilter, stateFilter, dateFrom, dateTo]);

    // Init map
    useEffect(() => {
        if (mapInstance.current || !mapRef.current) return;
        const timer = requestAnimationFrame(() => {
            if (!mapRef.current) return;
            const map = L.map(mapRef.current).setView([39.8283, -98.5795], 4);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 18,
                attribution: '&copy; OpenStreetMap contributors'
            }).addTo(map);
            mapInstance.current = map;
            setTimeout(() => { map.invalidateSize(); setMapReady(true); }, 100);
        });
        return () => cancelAnimationFrame(timer);
    }, []);

    // Update map markers when filtered changes — group by venue for performance
    useEffect(() => {
        const map = mapInstance.current;
        if (!map || !mapReady) return;
        // Clear old markers
        markersRef.current.forEach(m => map.removeLayer(m));
        markersRef.current = [];
        // Group games by venue
        const byVenue = {};
        filtered.forEach(g => {
            const key = g.venue || (g.home || g.homeTeam || 'Unknown');
            if (!byVenue[key]) byVenue[key] = { games: [], venue: g.venue, home: g.home || g.homeTeam || '', city: g.city, state: g.state };
            byVenue[key].games.push(g);
        });
        // Add one marker per venue
        Object.values(byVenue).forEach(v => {
            const normalizedHome = normalizeTeamName(v.home);
            const coords = VENUE_COORDS[v.venue] || SCHOOL_COORDS[normalizedHome] || SCHOOL_COORDS[v.home];
            if (!coords) return;
            const homeLogo = getTeamLogoUrl(v.home);
            let icon;
            if (homeLogo) {
                icon = L.divIcon({
                    className: 'venue-marker-icon',
                    html: '<div style="width:28px;height:28px;border-radius:50%;border:3px solid #c2410c;background:#fff;overflow:hidden;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.3);">' +
                        '<img src="' + homeLogo + '" style="width:20px;height:20px;object-fit:contain;" onerror="this.style.display=\'none\'" />' +
                        '</div>',
                    iconSize: [28, 28],
                    iconAnchor: [14, 14],
                    popupAnchor: [0, -14]
                });
            } else {
                icon = L.divIcon({
                    className: 'venue-marker-icon',
                    html: '<div style="width:12px;height:12px;border-radius:50%;border:2px solid #fff;background:#c2410c;box-shadow:0 2px 4px rgba(0,0,0,0.3);"></div>',
                    iconSize: [12, 12],
                    iconAnchor: [6, 6],
                    popupAnchor: [0, -6]
                });
            }
            const count = v.games.length;
            const popupLines = v.games.slice(0, 5).map(g => {
                const dateStr = g.date ? formatGameDateTime(g.date, g.time_detail) : '';
                return (g.away || g.awayTeam || '') + ' @ ' + (g.home || g.homeTeam || '') + ' — ' + dateStr;
            });
            const popup = '<strong>' + (v.venue || v.home) + '</strong><br>' +
                (v.city ? v.city + (v.state ? ', ' + v.state : '') + '<br>' : '') +
                count + ' game' + (count !== 1 ? 's' : '') + '<br><hr style="margin:4px 0">' +
                popupLines.join('<br>') +
                (count > 5 ? '<br><em>...and ' + (count - 5) + ' more</em>' : '');
            const marker = L.marker(coords, { icon }).bindPopup(popup).addTo(map);
            markersRef.current.push(marker);
        });
    }, [filtered, mapReady]);

    if (gamesData.length === 0) {
        return html`<${EmptyState} title="No upcoming games data" message="Run the schedule scraper to load upcoming games." />`;
    }

    return html`
        <div>
            <div class="map-container" style="height: 350px; border-radius: var(--radius-lg); overflow: hidden; margin-bottom: var(--space-4);">
                <div ref=${mapRef} style="width: 100%; height: 100%;"></div>
            </div>

            <${FilterBar}>
                <input type="text" class="filter-input" placeholder="Search teams, venues..." value=${search} onInput=${(e) => setSearch(e.target.value)} />
                <div class="gender-toggle">
                    ${[{id:'',label:'All'},{id:'M',label:"Men's"},{id:'W',label:"Women's"}].map(gf => html`
                        <button class=${'quick-filter-btn' + (genderFilter === gf.id ? ' active' : '')} onClick=${() => setGenderFilter(gf.id)}>${gf.label}</button>
                    `)}
                </div>
                <div class="date-range-filter">
                    <input type="date" class="filter-input" value=${dateFrom} onChange=${(e) => setDateFrom(e.target.value)}
                        min=${uniqueDates[0] || ''} max=${uniqueDates[uniqueDates.length - 1] || ''} />
                    <span class="date-range-sep">to</span>
                    <input type="date" class="filter-input" value=${dateTo} onChange=${(e) => setDateTo(e.target.value)}
                        min=${dateFrom || uniqueDates[0] || ''} max=${uniqueDates[uniqueDates.length - 1] || ''} />
                </div>
                <select class="filter-select" value=${stateFilter} onChange=${(e) => setStateFilter(e.target.value)}>
                    <option value="">All States</option>
                    ${states.map(s => html`<option value=${s}>${s}</option>`)}
                </select>
                ${(dateFrom || dateTo) ? html`<button class="quick-filter-btn" onClick=${() => { setDateFrom(''); setDateTo(''); }}>Clear dates</button>` : null}
                <span class="filter-count">${filtered.length} games</span>
            <//>

            <div class="upcoming-cards-grid">
                ${filtered.slice(0, 100).map(g => {
                    const dateStr = g.date ? formatGameDateTime(g.date, g.time_detail) : '';
                    const awayLogo = getTeamLogoUrl(g.away || g.awayTeam);
                    const homeLogo = getTeamLogoUrl(g.home || g.homeTeam);
                    return html`
                        <div class="upcoming-card">
                            <div class="upcoming-date">
                                ${dateStr}
                                ${g.gender === 'W' ? html` <span class="badge badge-women">W</span>` : null}
                            </div>
                            <div class="upcoming-matchup">
                                <div class="upcoming-team">
                                    ${awayLogo ? html`<img src=${awayLogo} class="upcoming-logo" alt="" />` : null}
                                    <div>
                                        ${g.awayRank ? html`<span class="ap-rank">#${g.awayRank}</span> ` : null}
                                        <span class="upcoming-team-name">${g.away || g.awayTeam || ''}</span>
                                    </div>
                                </div>
                                <span class="upcoming-at">@</span>
                                <div class="upcoming-team">
                                    ${homeLogo ? html`<img src=${homeLogo} class="upcoming-logo" alt="" />` : null}
                                    <div>
                                        ${g.homeRank ? html`<span class="ap-rank">#${g.homeRank}</span> ` : null}
                                        <span class="upcoming-team-name">${g.home || g.homeTeam || ''}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="upcoming-venue">${g.venue || ''}</div>
                            <div class="upcoming-meta">
                                <span>${g.city || ''}${g.state ? ', ' + g.state : ''}</span>
                                ${(g.tv || []).length > 0 ? html`<span class="upcoming-tv">${g.tv.join(', ')}</span>` : null}
                            </div>
                        </div>
                    `;
                })}
                ${filtered.length > 100 ? html`<div class="text-muted" style="text-align:center;padding:var(--space-4);grid-column:1/-1;">Showing first 100 of ${filtered.length} games. Use filters to narrow results.</div>` : null}
            </div>
        </div>
    `;
}

// ============================================================================
// GAME DETAIL MODAL
// ============================================================================

function GameDetailModal({ gameId, onClose, showPlayerDetail }) {
    const game = useMemo(() => (DATA.games || []).find(g => g.GameID === gameId), [gameId]);
    if (!game) return null;

    const awayScore = game['Away Score'] || 0;
    const homeScore = game['Home Score'] || 0;
    const awayWon = awayScore > homeScore;
    const linescore = game.Linescore || {};
    const milestones = gameMilestones[gameId] || { badges: [] };
    const genderTag = game.Gender === 'W' ? ' (W)' : '';

    // Get box score data
    const boxScore = useMemo(() => {
        const playerGames = (DATA.playerGames || []).filter(pg => pg.game_id === gameId);
        const away = playerGames.filter(pg => pg.team === game['Away Team']);
        const home = playerGames.filter(pg => pg.team === game['Home Team']);
        return { away, home };
    }, [gameId]);

    // Linescore rendering
    const periods = linescore.away?.quarters ? 'quarters' : 'halves';
    const periodData = linescore.away?.[periods] || [];
    const periodLabels = periods === 'quarters'
        ? periodData.map((_, i) => `Q${i + 1}`)
        : periodData.map((_, i) => `H${i + 1}`);
    const otData = linescore.away?.OT || [];
    otData.forEach((_, i) => periodLabels.push(i === 0 ? 'OT' : `${i + 1}OT`));

    const BoxScoreTable = ({ players, teamName }) => {
        if (!players.length) return null;
        const starters = players.filter(p => p.starter);
        const bench = players.filter(p => !p.starter);
        const renderRow = (p) => html`
            <tr>
                <td>
                    <span class="player-link" onClick=${() => { showPlayerDetail(p.player_id || p.player); }}>${p.player}</span>
                    ${p.starter ? '' : ''}
                </td>
                <td>${formatMinutes(p.mp)}</td>
                <td class="stat-highlight">${p.pts || 0}</td>
                <td>${p.trb || 0}</td>
                <td>${p.ast || 0}</td>
                <td>${p.stl || 0}</td>
                <td>${p.blk || 0}</td>
                <td>${p.fg || 0}-${p.fga || 0}</td>
                <td>${p.fg3 || 0}-${p.fg3a || 0}</td>
                <td>${p.ft || 0}-${p.fta || 0}</td>
                <td>${p.pf || 0}</td>
            </tr>
        `;
        return html`
            <div class="box-score-section">
                <h4>${teamName}${genderTag}</h4>
                <div class="table-container">
                    <table class="data-table box-score-table">
                        <thead><tr><th>Player</th><th>MIN</th><th>PTS</th><th>REB</th><th>AST</th><th>STL</th><th>BLK</th><th>FG</th><th>3P</th><th>FT</th><th>PF</th></tr></thead>
                        <tbody>
                            ${starters.length > 0 && html`<tr class="section-divider"><td colspan="11">Starters</td></tr>`}
                            ${starters.map(renderRow)}
                            ${bench.length > 0 && html`<tr class="section-divider"><td colspan="11">Bench</td></tr>`}
                            ${bench.map(renderRow)}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    };

    // PBP Analysis
    const pbp = game.ESPNPBPAnalysis || {};
    const gameGender = game.Gender || 'M';
    const getPeriodLabel = (period) => {
        if (gameGender === 'W') {
            if (period <= 4) return `Q${period}`;
            return `OT${period - 4 > 1 ? period - 4 : ''}`;
        } else {
            if (period === 1) return '1st half';
            if (period === 2) return '2nd half';
            return `OT${period - 2 > 1 ? period - 2 : ''}`;
        }
    };

    return html`
        <div>
            <div class="game-detail-header">
                <div class="game-detail-score">
                    <div class=${'team-side' + (awayWon ? ' winner' : '')}>
                        ${game.AwayRank ? html`<span class="ap-rank">#${game.AwayRank}</span>` : null}
                        <span class="team-name">${game['Away Team']}</span>
                        <span class="team-score">${awayScore}</span>
                    </div>
                    <div class="score-divider">@</div>
                    <div class=${'team-side' + (!awayWon ? ' winner' : '')}>
                        ${game.HomeRank ? html`<span class="ap-rank">#${game.HomeRank}</span>` : null}
                        <span class="team-name">${game['Home Team']}</span>
                        <span class="team-score">${homeScore}</span>
                    </div>
                </div>
                <div class="game-detail-info">
                    <span>${game.Date}${genderTag}</span>
                    <span>${game.Venue}, ${game.City}, ${game.State}</span>
                    ${game.Attendance ? html`<span>Attendance: ${game.Attendance.toLocaleString()}</span>` : null}
                    ${(game.Division === 'D1' || !game.Division) && html`
                        <a href=${getSportsRefUrl(game)} target="_blank" class="external-link">Sports Reference ↗</a>
                    `}
                </div>
            </div>

            ${periodData.length > 0 && html`
                <div class="linescore-table">
                    <table class="data-table">
                        <thead><tr><th>Team</th>${periodLabels.map(l => html`<th>${l}</th>`)}<th>T</th></tr></thead>
                        <tbody>
                            <tr>
                                <td>${game['Away Team']}</td>
                                ${(linescore.away?.[periods] || []).map(s => html`<td>${s}</td>`)}
                                ${(linescore.away?.OT || []).map(s => html`<td>${s}</td>`)}
                                <td class="stat-highlight">${awayScore}</td>
                            </tr>
                            <tr>
                                <td>${game['Home Team']}</td>
                                ${(linescore.home?.[periods] || []).map(s => html`<td>${s}</td>`)}
                                ${(linescore.home?.OT || []).map(s => html`<td>${s}</td>`)}
                                <td class="stat-highlight">${homeScore}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            `}

            ${milestones.badges.length > 0 && html`
                <div class="game-badges">
                    ${milestones.badges.map(b => html`<${Badge} ...${b} />`)}
                </div>
            `}

            <${BoxScoreTable} players=${boxScore.away} teamName=${game['Away Team']} />
            <${BoxScoreTable} players=${boxScore.home} teamName=${game['Home Team']} />

            ${(pbp.biggestComeback || pbp.teamScoringRuns?.length > 0 || pbp.playerPointStreaks?.length > 0 || pbp.decisiveShot || pbp.clutchGoAhead) && html`
                <div class="espn-pbp-analysis">
                    <div class="pbp-section-title">Advanced Game Analysis</div>

                    ${pbp.biggestComeback && html`
                        <div class="pbp-comeback">
                            ${pbp.biggestComeback.neverTrailed
                                ? html`<strong>${pbp.biggestComeback.team}</strong> led wire-to-wire`
                                : html`<strong>${pbp.biggestComeback.team}</strong> ${pbp.biggestComeback.won ? 'overcame' : 'nearly overcame'} ${pbp.biggestComeback.deficit}-pt deficit
                                    <span class="pbp-detail">(down ${pbp.biggestComeback.deficit} at ${pbp.biggestComeback.deficitScore}, ${pbp.biggestComeback.deficitTime} in ${getPeriodLabel(pbp.biggestComeback.deficitPeriod)})</span>`
                            }
                        </div>
                    `}

                    ${pbp.teamScoringRuns?.length > 0 && html`
                        <div class="pbp-item">
                            <strong>Scoring Runs:</strong>
                            ${pbp.teamScoringRuns.map(run => html`
                                <span class="espn-run-badge">${run.team} ${run.points}-0 run (${run.startScore} → ${run.endScore}) ${run.startTime}-${run.endTime} ${getPeriodLabel(run.endPeriod)}</span>
                            `)}
                        </div>
                    `}

                    ${pbp.playerPointStreaks?.length > 0 && html`
                        <div class="pbp-item">
                            <strong>Individual Streaks:</strong>
                            ${pbp.playerPointStreaks.map(s => html`
                                <span class="espn-streak-badge">${s.player} (${s.team}) ${s.points} consecutive pts (${s.startScore} → ${s.endScore}) ${s.startTime}-${s.endTime} ${getPeriodLabel(s.endPeriod)}</span>
                            `)}
                        </div>
                    `}

                    ${(pbp.clutchGoAhead || pbp.decisiveShot) && html`
                        <div class="pbp-item">
                            <strong>Decisive Shots:</strong>
                            ${pbp.clutchGoAhead && html`
                                <span class="espn-gws-badge">${pbp.clutchGoAhead.player} (${pbp.clutchGoAhead.team}) go-ahead ${pbp.clutchGoAhead.points === 1 ? 'FT' : pbp.clutchGoAhead.points === 2 ? 'bucket' : 'three'} at ${pbp.clutchGoAhead.time} → ${pbp.clutchGoAhead.score}</span>
                            `}
                            ${pbp.decisiveShot && (pbp.decisiveShot.time !== pbp.clutchGoAhead?.time) && html`
                                <span class="espn-gws-badge">${pbp.decisiveShot.player} (${pbp.decisiveShot.team}) decisive shot at ${pbp.decisiveShot.time} ${getPeriodLabel(pbp.decisiveShot.period)} → ${pbp.decisiveShot.score}</span>
                            `}
                        </div>
                    `}
                </div>
            `}
        </div>
    `;
}

// ============================================================================
// PLAYER DETAIL MODAL
// ============================================================================

function PlayerDetailModal({ playerId, onClose, showGameDetail }) {
    const player = useMemo(() => (DATA.players || []).find(p => (p['Player ID'] || p.Player) === playerId), [playerId]);
    if (!player) return null;

    const chartRef = useRef(null);
    const chartInstance = useRef(null);
    const [chartStat, setChartStat] = useState('pts');

    const games = useMemo(() =>
        (DATA.playerGames || [])
            .filter(g => (g.player_id || g.player) === playerId)
            .sort((a, b) => (b.date_yyyymmdd || b.date || '').localeCompare(a.date_yyyymmdd || a.date || '')),
        [playerId]
    );

    const genderTag = player.Gender === 'W' ? ' (W)' : '';
    const link = getPlayerSportsRefLink(player);

    // Chart
    useEffect(() => {
        if (!chartRef.current || games.length < 2) return;
        if (chartInstance.current) chartInstance.current.destroy();

        const chartGames = [...games].reverse();
        const labels = chartGames.map(g => {
            const parts = (g.date || '').split(' ');
            return parts.length >= 2 ? `${parts[0].slice(0,3)} ${parts[1].replace(',','')}` : g.date;
        });
        const data = chartGames.map(g => g[chartStat] || 0);
        const avg = data.reduce((a,b) => a+b, 0) / data.length;
        const statLabels = { pts: 'Points', trb: 'Rebounds', ast: 'Assists', game_score: 'Game Score' };
        const statColors = { pts: '#4ade80', trb: '#60a5fa', ast: '#f472b6', game_score: '#fbbf24' };
        const isDark = document.body.getAttribute('data-theme') === 'dark';

        chartInstance.current = new Chart(chartRef.current, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: statLabels[chartStat] || chartStat,
                    data,
                    borderColor: statColors[chartStat] || '#4ade80',
                    backgroundColor: (statColors[chartStat] || '#4ade80') + '20',
                    fill: true, tension: 0.3, pointRadius: 5, pointHoverRadius: 7,
                }, {
                    label: `Avg: ${avg.toFixed(1)}`,
                    data: data.map(() => avg),
                    borderColor: isDark ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.3)',
                    borderWidth: 1, borderDash: [5, 5], pointRadius: 0, fill: false,
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        filter: (item) => item.datasetIndex === 0,
                        callbacks: {
                            title: (items) => chartGames[items[0].dataIndex]?.date || '',
                            afterLabel: (item) => `vs ${chartGames[item.dataIndex]?.opponent || ''}`
                        }
                    }
                },
                scales: {
                    x: { grid: { color: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }, ticks: { color: isDark ? '#b0b0b0' : '#666', maxRotation: 45 } },
                    y: { beginAtZero: true, grid: { color: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }, ticks: { color: isDark ? '#b0b0b0' : '#666' } }
                }
            }
        });

        return () => { if (chartInstance.current) chartInstance.current.destroy(); };
    }, [chartStat, games, playerId]);

    return html`
        <div>
            <p>Team: ${player.Team} ${genderTag} | Games: ${player.Games}
                ${link && html` <a href=${link.url} target="_blank" class="external-link" title=${link.title}>↗</a>`}
            </p>
            <div class="player-detail-stats">
                <div class="compare-card">
                    <h4>Averages</h4>
                    <div class="stat-row"><span>PPG</span><span class=${getStatClass(player.PPG||0, STAT_THRESHOLDS.ppg)}>${player.PPG||0}</span></div>
                    <div class="stat-row"><span>RPG</span><span class=${getStatClass(player.RPG||0, STAT_THRESHOLDS.rpg)}>${player.RPG||0}</span></div>
                    <div class="stat-row"><span>APG</span><span class=${getStatClass(player.APG||0, STAT_THRESHOLDS.apg)}>${player.APG||0}</span></div>
                    <div class="stat-row"><span>SPG</span><span>${player.SPG||0}</span></div>
                    <div class="stat-row"><span>BPG</span><span>${player.BPG||0}</span></div>
                </div>
                <div class="compare-card">
                    <h4>Shooting</h4>
                    <div class="stat-row"><span>FG%</span><span class=${getStatClass(player['FG%']||0, STAT_THRESHOLDS.fgPct)}>${((player['FG%']||0)*100).toFixed(1)}%</span></div>
                    <div class="stat-row"><span>3P%</span><span class=${getStatClass(player['3P%']||0, STAT_THRESHOLDS.threePct)}>${((player['3P%']||0)*100).toFixed(1)}%</span></div>
                    <div class="stat-row"><span>FT%</span><span>${((player['FT%']||0)*100).toFixed(1)}%</span></div>
                </div>
                <div class="compare-card">
                    <h4>Totals</h4>
                    <div class="stat-row"><span>Points</span><span>${player['Total PTS']||0}</span></div>
                    <div class="stat-row"><span>Rebounds</span><span>${player['Total REB']||0}</span></div>
                    <div class="stat-row"><span>Assists</span><span>${player['Total AST']||0}</span></div>
                </div>
            </div>

            ${games.length > 1 && html`
                <div class="chart-section">
                    <div class="chart-header">
                        <h4>Performance Trend</h4>
                        <div class="chart-toggles">
                            ${['pts', 'trb', 'ast', 'game_score'].map(stat => html`
                                <button class=${'chart-toggle' + (chartStat === stat ? ' active' : '')} onClick=${() => setChartStat(stat)}>
                                    ${{ pts: 'PTS', trb: 'REB', ast: 'AST', game_score: 'GmSc' }[stat]}
                                </button>
                            `)}
                        </div>
                    </div>
                    <div class="chart-container" style="height:200px">
                        <canvas ref=${chartRef}></canvas>
                    </div>
                </div>
            `}

            ${games.length > 0 && html`
                <h4 style="margin-top:1rem">Game Log (${games.length} games)</h4>
                <div class="table-container" style="max-height:300px;overflow-y:auto">
                    <table class="data-table">
                        <thead><tr><th>Date</th><th>Opp</th><th>Result</th><th>MIN</th><th>PTS</th><th>REB</th><th>AST</th><th>STL</th><th>BLK</th><th>FG</th><th>3P</th><th>FT</th><th>GmSc</th></tr></thead>
                        <tbody>
                            ${games.map(g => html`
                                <tr class="clickable-row" onClick=${() => { onClose(); showGameDetail(g.game_id); }}>
                                    <td><span class="game-link">${g.date}</span></td>
                                    <td>${g.opponent}</td>
                                    <td>${g.result} ${g.score || ''}</td>
                                    <td>${formatMinutes(g.mp)}</td>
                                    <td>${g.pts || 0}</td>
                                    <td>${g.trb || 0}</td>
                                    <td>${g.ast || 0}</td>
                                    <td>${g.stl || 0}</td>
                                    <td>${g.blk || 0}</td>
                                    <td>${g.fg || 0}-${g.fga || 0}</td>
                                    <td>${g.fg3 || 0}-${g.fg3a || 0}</td>
                                    <td>${g.ft || 0}-${g.fta || 0}</td>
                                    <td>${g.game_score != null ? g.game_score.toFixed(1) : '-'}</td>
                                </tr>
                            `)}
                        </tbody>
                    </table>
                </div>
            `}
        </div>
    `;
}

// ============================================================================
// VENUE DETAIL MODAL
// ============================================================================

function VenueDetailModal({ venueName, onClose, showGameDetail }) {
    const games = useMemo(() =>
        (DATA.games || []).filter(g => g.Venue === venueName)
            .sort((a, b) => (b.DateSort || '').localeCompare(a.DateSort || '')),
        [venueName]
    );

    if (!games.length) return null;

    const venueInfo = (DATA.venues || []).find(v => v.Venue === venueName) || {};
    const city = games[0]?.City || venueInfo.City || '';
    const state = games[0]?.State || venueInfo.State || '';

    const { teamsList, confsList } = useMemo(() => {
        const teamGenderSet = new Map();
        const confSet = new Set();
        games.forEach(g => {
            const gender = g.Gender || 'M';
            const awayConf = getGameConference(g, 'away');
            const homeConf = getGameConference(g, 'home');
            [`${g['Away Team']}|${gender}`, `${g['Home Team']}|${gender}`].forEach((key, idx) => {
                if (!teamGenderSet.has(key)) {
                    teamGenderSet.set(key, { team: key.split('|')[0], gender, conf: idx === 0 ? awayConf : homeConf });
                }
            });
            if (awayConf) confSet.add(awayConf);
            if (homeConf) confSet.add(homeConf);
        });
        return {
            teamsList: [...teamGenderSet.values()].sort((a, b) => a.team.localeCompare(b.team)),
            confsList: [...confSet].sort()
        };
    }, [games]);

    return html`
        <div>
            <p>${city}${state ? ', ' + state : ''}</p>
            <div class="venue-stats-summary">
                <${StatBox} label="Games" value=${games.length} />
                <${StatBox} label="Teams Seen" value=${teamsList.length} />
                <${StatBox} label="Conferences" value=${confsList.length} />
                ${venueInfo['Home Wins'] !== undefined && html`
                    <${StatBox} label="Home-Away" value="${venueInfo['Home Wins'] || 0}-${venueInfo['Away Wins'] || 0}" />
                `}
            </div>

            <h4 style="margin-top:1rem">Teams Seen Here</h4>
            <div class="venue-teams-list">
                ${teamsList.map(({ team, gender, conf }) => html`
                    <span class="venue-team-tag">${team}${gender === 'W' ? ' (W)' : ''}${conf ? html`<span class="conf-label">${conf}</span>` : null}</span>
                `)}
            </div>

            <h4 style="margin-top:1.5rem">Game History</h4>
            <div class="table-container">
                <table class="data-table">
                    <thead><tr><th>Date</th><th>Winner</th><th>Score</th><th>Loser</th></tr></thead>
                    <tbody>
                        ${games.map(g => {
                            const homeWon = (g['Home Score']||0) > (g['Away Score']||0);
                            const winner = homeWon ? g['Home Team'] : g['Away Team'];
                            const loser = homeWon ? g['Away Team'] : g['Home Team'];
                            const winScore = homeWon ? g['Home Score'] : g['Away Score'];
                            const loseScore = homeWon ? g['Away Score'] : g['Home Score'];
                            const gTag = g.Gender === 'W' ? ' (W)' : '';
                            return html`
                                <tr class="clickable-row" onClick=${() => { onClose(); showGameDetail(g.GameID); }}>
                                    <td>${g.Date}</td>
                                    <td><strong>${winner}${gTag}</strong></td>
                                    <td>${winScore}-${loseScore}</td>
                                    <td>${loser}${gTag}</td>
                                </tr>
                            `;
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// ============================================================================
// APP (root component)
// ============================================================================

function App() {
    const [route, setRoute] = useState(() => parseRoute());
    const [toast, setToast] = useState('');

    // Modal state
    const [gameModal, setGameModal] = useState(null);
    const [playerModal, setPlayerModal] = useState(null);
    const [venueModal, setVenueModal] = useState(null);

    // Listen for hash changes
    useEffect(() => {
        const handler = () => setRoute(parseRoute());
        window.addEventListener('hashchange', handler);
        window.addEventListener('popstate', handler);
        return () => {
            window.removeEventListener('hashchange', handler);
            window.removeEventListener('popstate', handler);
        };
    }, []);

    const navigate = useCallback((section, sub = '') => {
        updateRoute(section, sub);
        setRoute({ section, sub, params: {} });
    }, []);

    const onSubChange = useCallback((sub) => {
        updateRoute(route.section, sub);
        setRoute(r => ({ ...r, sub }));
    }, [route.section]);

    const showGameDetail = useCallback((gameId) => {
        setGameModal(gameId);
    }, []);

    const showPlayerDetail = useCallback((playerId) => {
        setPlayerModal(playerId);
    }, []);

    const showVenueDetail = useCallback((venueName) => {
        setVenueModal(venueName);
    }, []);

    // Handle search result selection
    const handleSearch = useCallback((type, id) => {
        if (type === 'game') showGameDetail(id);
        else if (type === 'player') showPlayerDetail(id);
        else if (type === 'venue') showVenueDetail(id);
        else if (type === 'team') navigate('games', 'teams');
    }, []);

    // Handle deep links
    useEffect(() => {
        if (route.params.game) showGameDetail(route.params.game);
        if (route.params.player) showPlayerDetail(route.params.player);
    }, []);

    const { section, sub } = route;

    return html`
        <${Header} onSearch=${handleSearch} toast=${toast} setToast=${setToast} />
        <${Nav} section=${section} onChange=${(s) => navigate(s)} />
        <main id="main-content" class="main-content">
            ${section === 'home' && html`<${HomeSection} onNavigate=${navigate} showGameDetail=${showGameDetail} showPlayerDetail=${showPlayerDetail} />`}
            ${section === 'games' && html`<${GamesSection} sub=${sub} onSubChange=${onSubChange} showGameDetail=${showGameDetail} />`}
            ${section === 'people' && html`<${PeopleSection} sub=${sub} onSubChange=${onSubChange} showPlayerDetail=${showPlayerDetail} showGameDetail=${showGameDetail} />`}
            ${section === 'places' && html`<${PlacesSection} sub=${sub} onSubChange=${onSubChange} showVenueDetail=${showVenueDetail} showGameDetail=${showGameDetail} />`}
        </main>

        <${Modal} id="game-modal" active=${!!gameModal} onClose=${() => setGameModal(null)} title="Game Detail">
            ${gameModal && html`<${GameDetailModal} gameId=${gameModal} onClose=${() => setGameModal(null)} showPlayerDetail=${showPlayerDetail} />`}
        <//>
        <${Modal} id="player-modal" active=${!!playerModal} onClose=${() => setPlayerModal(null)} title=${playerModal ? ((DATA.players||[]).find(p => (p['Player ID']||p.Player) === playerModal)?.Player || 'Player Detail') : ''}>
            ${playerModal && html`<${PlayerDetailModal} playerId=${playerModal} onClose=${() => setPlayerModal(null)} showGameDetail=${showGameDetail} />`}
        <//>
        <${Modal} id="venue-modal" active=${!!venueModal} onClose=${() => setVenueModal(null)} title=${venueModal || 'Venue Detail'}>
            ${venueModal && html`<${VenueDetailModal} venueName=${venueModal} onClose=${() => setVenueModal(null)} showGameDetail=${showGameDetail} />`}
        <//>

        <${Toast} message=${toast} onDone=${() => setToast('')} />
    `;
}

// ============================================================================
// MOUNT
// ============================================================================

render(html`<${App} />`, document.getElementById('app'));

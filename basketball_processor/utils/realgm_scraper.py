"""
RealGM scraper for player lookup and college verification.
"""

import re
import time
from typing import Any, Dict, List, Optional

try:
    import cloudscraper
    from bs4 import BeautifulSoup
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

RATE_LIMIT_SECONDS = 8  # Longer delay to avoid rate limiting


def _get_scraper():
    """Get a cloudscraper instance."""
    if not HAS_DEPS:
        return None
    return cloudscraper.create_scraper()


def search_player(name: str, scraper=None) -> List[Dict[str, Any]]:
    """
    Search RealGM for a player by name.

    Returns list of candidates with id, name, url.
    """
    if scraper is None:
        scraper = _get_scraper()
    if scraper is None:
        return []

    # URL encode the name
    query = name.replace(' ', '+')
    url = f"https://basketball.realgm.com/search?q={query}"

    # Rate limit before request
    time.sleep(RATE_LIMIT_SECONDS)

    try:
        response = scraper.get(url, timeout=15)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        # Check if redirected directly to a player page (single result)
        # Can check either URL or page content
        final_url = response.url
        if '/player/' in final_url and '/Summary/' in final_url:
            match = re.search(r'/player/([^/]+)/Summary/(\d+)', final_url)
            if match:
                player_slug = match.group(1)
                player_id = int(match.group(2))
                title = soup.find('title')
                player_name = title.text.split('|')[0].strip() if title else player_slug.replace('-', ' ')
                return [{
                    'id': player_id,
                    'name': player_name,
                    'url': final_url
                }]

        # Also check if the page content is a player page (URL might not reflect redirect)
        profile_box = soup.find('div', class_='profile-box')
        if profile_box:
            # This is a player page - extract from the canonical URL or links
            canonical = soup.find('link', rel='canonical')
            if canonical:
                href = canonical.get('href', '')
                match = re.search(r'/player/([^/]+)/Summary/(\d+)', href)
                if match:
                    player_slug = match.group(1)
                    player_id = int(match.group(2))
                    title = soup.find('title')
                    player_name = title.text.split('|')[0].strip() if title else player_slug.replace('-', ' ')
                    return [{
                        'id': player_id,
                        'name': player_name,
                        'url': href
                    }]
        players = soup.select('a[href*="/player/"]')

        results = []
        seen = set()
        for p in players:
            href = p.get('href', '')
            player_name = p.text.strip()
            if not player_name or href in seen:
                continue
            seen.add(href)

            match = re.search(r'/player/[^/]+/Summary/(\d+)', href)
            if match:
                results.append({
                    'id': int(match.group(1)),
                    'name': player_name,
                    'url': f"https://basketball.realgm.com{href}"
                })

        return results
    except Exception as e:
        print(f"Error searching RealGM: {e}")
        return []


def get_player_college(player_id: int, scraper=None) -> Optional[str]:
    """
    Get a player's college from their RealGM profile.
    
    Returns college name or None.
    """
    if scraper is None:
        scraper = _get_scraper()
    if scraper is None:
        return None
    
    url = f"https://basketball.realgm.com/player/x/Summary/{player_id}"
    
    try:
        response = scraper.get(url, timeout=15)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for college in profile text
        profile = soup.find('div', class_='profile-box')
        if profile:
            text = profile.get_text()

            # Check Pre-Draft Team first (most reliable for college)
            match = re.search(r'Pre-Draft Team:\s*([^\n]+)', text)
            if match:
                team = match.group(1).strip()
                # Remove year indicators like "(Jr)" "(Sr)" "(So)" "(Fr)"
                team = re.sub(r'\s*\([^)]*\)\s*$', '', team)
                # Skip if it's an NBA team or international
                if team and not any(x in team for x in ['Trail Blazers', 'Lakers', 'Celtics', 'Warriors']):
                    return team

            # Fall back to Current Team for college players
            match = re.search(r'Current Team:\s*([^\n]+)', text)
            if match:
                team = match.group(1).strip()
                team = re.sub(r'\s*\([^)]*\)\s*$', '', team)
                return team

        # Also check for college links in NCAA section
        college_links = soup.select('a[href*="/ncaa/conferences/"]')
        for link in college_links:
            href = link.get('href', '')
            # Look for team links like /ncaa/conferences/Big-East-Conference/59/UConn/64
            if re.search(r'/ncaa/conferences/[^/]+/\d+/[^/]+/\d+$', href):
                return link.text.strip()

        return None
    except Exception as e:
        print(f"Error fetching player {player_id}: {e}")
        return None


def normalize_college(name: str) -> str:
    """Normalize college name for comparison."""
    name = name.lower().strip()

    # Common name mappings
    mappings = {
        'uconn': 'connecticut',
        'usc': 'southern california',
        'usf': 'san francisco',
        'fau': 'florida atlantic',
        'vcu': 'virginia commonwealth',
        'gw': 'george washington',
        'pitt': 'pittsburgh',
    }
    if name in mappings:
        name = mappings[name]

    # Remove common suffixes/mascots
    for suffix in [' dons', ' huskies', ' bulldogs', ' tigers', ' bears', ' cavaliers',
                   ' terriers', ' owls', ' eagles', ' cardinals', ' trojans', ' bruins',
                   ' gaels', ' friars', ' hoyas', ' wildcats', ' blue devils', ' tar heels']:
        name = name.replace(suffix, '')

    # Common abbreviations
    name = name.replace('st.', 'saint').replace('state', '').replace('university', '')
    return name.strip()


def find_player_by_college(name: str, college: str, scraper=None) -> Optional[int]:
    """
    Find a player's RealGM ID by matching name and college.
    
    Args:
        name: Player name to search
        college: Expected college name
        
    Returns:
        RealGM player ID if found, None otherwise
    """
    if scraper is None:
        scraper = _get_scraper()
    if scraper is None:
        return None
    
    candidates = search_player(name, scraper)
    if not candidates:
        return None
    
    normalized_college = normalize_college(college)
    
    for candidate in candidates:
        time.sleep(RATE_LIMIT_SECONDS)
        player_college = get_player_college(candidate['id'], scraper)
        
        if player_college:
            if normalized_college in normalize_college(player_college):
                return candidate['id']
            # Also check if college is in the candidate's college
            if normalize_college(player_college) in normalized_college:
                return candidate['id']
    
    return None


if __name__ == '__main__':
    # Test
    print("Testing Barry Wang (San Francisco)...")
    result = find_player_by_college("Barry Wang", "San Francisco")
    print(f"Result: {result}")
    
    print("\nTesting Junjie Wang (San Francisco)...")
    result = find_player_by_college("Junjie Wang", "San Francisco")
    print(f"Result: {result}")

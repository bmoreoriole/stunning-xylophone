import requests
from bs4 import BeautifulSoup
import csv
import time
import json
from datetime import datetime

print("="*60)
print("🎯 SCRAPING RATINGS FOR ALL PLAYERS")
print("="*60)

# Load all player IDs
with open('all_player_ids.json', 'r') as f:
    players = json.load(f)

print(f"✅ Loaded {len(players):,} players")

def get_player_ratings(player):
    """Get complete ratings for a single player"""
    url = player['url']
    
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Determine if pitcher
        status_elem = soup.find('span', id='player-profile-status')
        is_pitcher = 'P' in status_elem.text if status_elem else False
        
        # Initialize ratings
        ratings = {
            'player_id': player['id'],
            'name': player['name'],
            'position': 'Pitcher' if is_pitcher else 'Hitter',
            'contact': '',
            'power': '',
            'speed': '',
            'defense': '',
            'velocity': '',
            'control': '',
            'movement': '',
            'stamina': '',
            'age': '',
            'salary': '',
            'ftv': ''
        }
        
        # Basic info
        age_elem = soup.find('span', id='player-profile-stat-age-value')
        if age_elem:
            ratings['age'] = age_elem.text.strip()
        
        ftv_elem = soup.find('span', id='player-profile-stat-ftv-value')
        if ftv_elem:
            ratings['ftv'] = ftv_elem.text.strip()
        
        salary_elem = soup.find('a', href='/research.php?view=salaries')
        if salary_elem:
            ratings['salary'] = salary_elem.text.strip()
        
        # Hitting ratings
        hitting_container = soup.find('div', id='ratings-hitting-bars-container')
        if hitting_container:
            numbers = []
            for span in hitting_container.find_all('span'):
                text = span.text.strip()
                if text.isdigit() and 1 <= int(text) <= 100:
                    numbers.append(int(text))
            
            if len(numbers) >= 4:
                ratings['contact'] = numbers[0]
                ratings['power'] = numbers[1]
                ratings['speed'] = numbers[2]
                ratings['defense'] = numbers[3]
        
        # Pitching ratings
        pitching_container = soup.find('div', id='ratings-pitching-bars-container')
        if pitching_container:
            numbers = []
            for span in pitching_container.find_all('span'):
                text = span.text.strip()
                if text.isdigit() and 1 <= int(text) <= 100:
                    numbers.append(int(text))
            
            if len(numbers) >= 4:
                ratings['velocity'] = numbers[0]
                ratings['control'] = numbers[1]
                ratings['movement'] = numbers[2]
                ratings['stamina'] = numbers[3]
        
        return ratings
        
    except Exception as e:
        print(f"   Error: {e}")
        return None

# Scrape all players
all_ratings = []
failed_ids = []

start_time = time.time()

for i, player in enumerate(players):
    print(f"[{i+1}/{len(players)}] {player['name']} (ID: {player['id']})...", end=" ")
    
    ratings = get_player_ratings(player)
    
    if ratings:
        all_ratings.append(ratings)
        print("✅")
    else:
        failed_ids.append(player['id'])
        print("❌")
    
    # Save every 100 players
    if (i + 1) % 100 == 0:
        with open('ratings_progress.json', 'w') as f:
            json.dump(all_ratings, f, indent=2)
        
        with open('ratings_progress.csv', 'w', newline='', encoding='utf-8') as f:
            if all_ratings:
                writer = csv.DictWriter(f, fieldnames=all_ratings[0].keys())
                writer.writeheader()
                writer.writerows(all_ratings)
        
        elapsed = time.time() - start_time
        rate = (i + 1) / elapsed if elapsed > 0 else 0
        print(f"   💾 Progress: {len(all_ratings)} players | {rate:.1f}/sec")
    
    time.sleep(0.3)

# Final save
with open('all_player_ratings.json', 'w') as f:
    json.dump(all_ratings, f, indent=2)

with open('all_player_ratings.csv', 'w', newline='', encoding='utf-8') as f:
    if all_ratings:
        writer = csv.DictWriter(f, fieldnames=all_ratings[0].keys())
        writer.writeheader()
        writer.writerows(all_ratings)

print("\n" + "="*60)
print("✅ COMPLETE!")
print(f"   Successful: {len(all_ratings):,}")
print(f"   Failed: {len(failed_ids):,}")
print(f"   Time: {(time.time() - start_time)/60:.1f} minutes")
import requests
from bs4 import BeautifulSoup
import time
import json
import re
import csv

print("🎯 SCRAPING ALL PLAYER IDs - SAVING FIXED")
print("="*60)

BASE_URL = "https://www.franchiseball.com/research/data/index/players/pg/{}"

all_player_ids = []  # Simple list of IDs
all_players_full = []  # List of dicts with id and name
current_page = 0
max_pages = 2200

print(f"📊 Target: ~99,719 players")
print("="*60)

while current_page <= max_pages:
    url = BASE_URL.format(current_page)
    print(f"📄 Page {current_page + 1}...", end=" ")
    
    try:
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code != 200:
            print(f"HTTP {response.status_code} - stopping")
            break
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find player links
        player_links = soup.find_all('a', class_='player-bubble')
        
        if not player_links:
            print("No player links found - stopping")
            break
        
        page_ids = []
        page_players = []
        
        for link in player_links:
            # Get player ID
            player_id = link.get('rel')
            if player_id and isinstance(player_id, list):
                player_id = player_id[0]
            else:
                href = link.get('href', '')
                match = re.search(r'/player/(\d+)', href)
                player_id = match.group(1) if match else None
            
            player_name = link.text.strip()
            
            if player_id:
                player_id = int(player_id)
                page_ids.append(player_id)
                page_players.append({'id': player_id, 'name': player_name})
        
        if not page_ids:
            print("No IDs extracted - stopping")
            break
        
        # Add to master lists
        all_player_ids.extend(page_ids)
        all_players_full.extend(page_players)
        
        print(f"found {len(page_ids)} players (total: {len(all_player_ids)})")
        
        # SAVE AFTER EVERY PAGE (not just every 10)
        # Save simple ID list
        with open('all_player_ids.json', 'w') as f:
            json.dump(all_player_ids, f, indent=2)
        
        # Save full player info
        with open('all_players_full.json', 'w') as f:
            json.dump(all_players_full, f, indent=2)
        
        # Save CSV
        with open('all_player_ids.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['player_id', 'name'])
            for player in all_players_full:
                writer.writerow([player['id'], player['name']])
        
        # Check if this is the last page
        if len(page_ids) < 50:
            print(f"✅ Last page reached!")
            break
        
        current_page += 1
        time.sleep(0.3)
        
    except Exception as e:
        print(f"Error: {e}")
        break

print("\n" + "="*60)
print(f"✅ SCRAPING COMPLETE!")
print(f"📊 Total players found: {len(all_player_ids):,}")
print(f"💾 Saved to: all_player_ids.json")

# Verify the file was saved
import os
if os.path.exists('all_player_ids.json'):
    size = os.path.getsize('all_player_ids.json')
    print(f"✅ File size: {size:,} bytes")
    
    # Show first 10 IDs
    print(f"\n📝 First 10 IDs: {all_player_ids[:10]}")
    print(f"📝 Last 10 IDs: {all_player_ids[-10:]}")
else:
    print("❌ ERROR: File was not saved!")

print("\n" + "="*60)
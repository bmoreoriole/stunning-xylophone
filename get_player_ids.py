import requests
from bs4 import BeautifulSoup
import time
import json
import re

print("🎯 SCRAPING ALL PLAYER IDs FROM PAGINATED DATABASE")
print("="*50)

base_url = "https://www.franchiseball.com/research.php?view=data&index=players&pg={}"
all_player_ids = []
current_page = 1
max_pages = 2200  # Safe upper limit

while current_page <= max_pages:
    url = base_url.format(current_page)
    print(f"📄 Page {current_page}...", end=" ")
    
    try:
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code != 200:
            print(f"HTTP {response.status_code} - stopping")
            break
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all player links on the page
        # Looking at your HTML, players are listed as links
        player_links = soup.find_all('a', href=re.compile(r'player\.php\?id=\d+'))
        
        if not player_links:
            # Alternative: Look for player names that might be links
            player_links = soup.find_all('a', href=True)
            player_links = [link for link in player_links if 'player.php?id=' in link.get('href', '')]
        
        if not player_links:
            print("No player links found - stopping")
            break
        
        # Extract IDs from links
        page_ids = []
        for link in player_links:
            href = link.get('href', '')
            match = re.search(r'id=(\d+)', href)
            if match:
                pid = int(match.group(1))
                if pid not in all_player_ids:  # Avoid duplicates
                    page_ids.append(pid)
        
        if not page_ids:
            print("No IDs extracted - stopping")
            break
        
        all_player_ids.extend(page_ids)
        print(f"found {len(page_ids)} IDs (total: {len(all_player_ids)})")
        
        # Check if this is the last page (fewer than 50 players)
        if len(page_ids) < 50:
            print(f"Last page reached ({len(page_ids)} players found)")
            break
        
        current_page += 1
        time.sleep(0.5)  # Polite delay
        
    except Exception as e:
        print(f"Error: {e}")
        break

print("\n" + "="*50)
print(f"✅ SCRAPING COMPLETE!")
print(f"📊 Total unique player IDs found: {len(all_player_ids)}")
print(f"📊 Expected: ~107,614")

# Save results
with open('all_player_ids.json', 'w') as f:
    json.dump(all_player_ids, f, indent=2)

print(f"💾 Saved to: all_player_ids.json")

# Also save as CSV
import csv
with open('all_player_ids.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['player_id'])
    for pid in all_player_ids:
        writer.writerow([pid])

print(f"💾 Saved to: all_player_ids.csv")
print(f"\n📝 First 10 IDs: {all_player_ids[:10]}")
print(f"📝 Last 10 IDs: {all_player_ids[-10:]}")
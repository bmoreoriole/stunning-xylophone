import requests
from bs4 import BeautifulSoup
import csv
import time
import json
import os

print("="*60)
print("🎯 FRANCHISE BALL - RATINGS SCRAPER (NO DATA LOSS)")
print("="*60)

# ============================================
# LOAD PLAYER IDs
# ============================================

with open('all_player_ids.json', 'r') as f:
    data = json.load(f)

# Handle both formats
player_ids = []
if isinstance(data, list):
    if len(data) > 0 and isinstance(data[0], int):
        player_ids = data
    elif isinstance(data[0], dict):
        if 'id' in data[0]:
            player_ids = [p['id'] for p in data]
        elif 'player_id' in data[0]:
            player_ids = [p['player_id'] for p in data]
    print(f"✅ Loaded {len(player_ids):,} player IDs")
else:
    print(f"❌ Unknown data format")
    exit()

# ============================================
# LOAD EXISTING PROGRESS (SAFE WAY)
# ============================================

PROGRESS_FILE = 'ratings_progress.csv'
all_ratings = []
completed_ids = set()

# Load existing data if file exists
if os.path.exists(PROGRESS_FILE) and os.path.getsize(PROGRESS_FILE) > 0:
    try:
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'player_id' in row and row['player_id']:
                    pid = int(row['player_id'])
                    completed_ids.add(pid)
                    all_ratings.append(row)
        print(f"🔄 Loaded {len(completed_ids):,} existing ratings from {PROGRESS_FILE}")
    except Exception as e:
        print(f"⚠️ Could not load: {e}")
        print("📝 Starting fresh...")
        all_ratings = []
        completed_ids = set()
else:
    print("📝 No existing progress - starting fresh")

# ============================================
# SCRAPE FUNCTION
# ============================================

def scrape_player(player_id):
    url = f"https://www.franchiseball.com/player.php?id={player_id}"
    
    try:
        r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code != 200:
            return None
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        name_elem = soup.find('span', id='player-profile-name')
        name = name_elem.text.strip() if name_elem else f"Player_{player_id}"
        
        status_elem = soup.find('span', id='player-profile-status')
        is_pitcher = 'P' in status_elem.text if status_elem else False
        
        age_elem = soup.find('span', id='player-profile-stat-age-value')
        age = age_elem.text.strip() if age_elem else ''
        
        ftv_elem = soup.find('span', id='player-profile-stat-ftv-value')
        ftv = ftv_elem.text.strip() if ftv_elem else ''
        
        # Hitting ratings
        contact = power = speed = defense = ''
        hitting = soup.find('div', id='ratings-hitting-bars-container')
        if hitting:
            nums = []
            for span in hitting.find_all('span'):
                txt = span.text.strip()
                if txt.isdigit() and 1 <= int(txt) <= 100:
                    nums.append(int(txt))
            if len(nums) >= 4:
                contact, power, speed, defense = nums[0], nums[1], nums[2], nums[3]
        
        # Pitching ratings
        velo = control = movement = stamina = ''
        pitching = soup.find('div', id='ratings-pitching-bars-container')
        if pitching:
            nums = []
            for span in pitching.find_all('span'):
                txt = span.text.strip()
                if txt.isdigit() and 1 <= int(txt) <= 100:
                    nums.append(int(txt))
            if len(nums) >= 4:
                velo, control, movement, stamina = nums[0], nums[1], nums[2], nums[3]
        
        return {
            'player_id': player_id,
            'name': name,
            'position': 'Pitcher' if is_pitcher else 'Hitter',
            'contact': contact,
            'power': power,
            'speed': speed,
            'defense': defense,
            'velocity': velo,
            'control': control,
            'movement': movement,
            'stamina': stamina,
            'age': age,
            'ftv': ftv
        }
        
    except Exception as e:
        return None

# ============================================
# APPEND TO CSV (SAFE - NO OVERWRITE)
# ============================================

def append_to_csv(rating):
    """Append a single rating to CSV - never loses existing data"""
    
    # Check if file exists and has headers
    file_exists = os.path.exists(PROGRESS_FILE) and os.path.getsize(PROGRESS_FILE) > 0
    
    with open(PROGRESS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rating.keys())
        
        # Write header only if file is new
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(rating)
    
    # Also append to JSON (append mode is tricky, so we rewrite)
    # But JSON is just backup - CSV is primary
    try:
        existing = []
        if os.path.exists('ratings_progress.json'):
            with open('ratings_progress.json', 'r') as f:
                existing = json.load(f)
        
        existing.append(rating)
        
        with open('ratings_progress.json', 'w') as f:
            json.dump(existing, f, indent=2)
    except:
        pass

# ============================================
# MAIN LOOP - APPENDS EACH PLAYER
# ============================================

start_time = time.time()
failed = []

# Filter out already scraped players
remaining_ids = [pid for pid in player_ids if pid not in completed_ids]
print(f"📊 Remaining to scrape: {len(remaining_ids):,} players")
print("="*60)

for i, pid in enumerate(remaining_ids):
    print(f"[{i+1}/{len(remaining_ids)}] ID {pid}...", end=" ")
    
    result = scrape_player(pid)
    
    if result:
        # APPEND to file immediately (not overwrite)
        append_to_csv(result)
        all_ratings.append(result)
        completed_ids.add(pid)
        print(f"✅ {result['name']}")
    else:
        failed.append(pid)
        print("❌")
    
    # Show progress every 50 players
    if (i + 1) % 50 == 0:
        elapsed = time.time() - start_time
        rate = (i + 1) / elapsed if elapsed > 0 else 0
        remaining = len(remaining_ids) - (i + 1)
        eta = remaining / rate if rate > 0 else 0
        
        # Also create a backup checkpoint
        with open('checkpoint.json', 'w') as f:
            json.dump({
                'completed': list(completed_ids),
                'last_index': i,
                'timestamp': time.time()
            }, f, indent=2)
        
        print(f"   💾 Rate: {rate:.1f}/sec | Done: {i+1} | Remaining: {remaining} | ETA: {eta/3600:.1f}h")
    
    time.sleep(0.15)

# Final save of all data
with open('all_player_ratings.csv', 'w', newline='', encoding='utf-8') as f:
    if all_ratings:
        writer = csv.DictWriter(f, fieldnames=all_ratings[0].keys())
        writer.writeheader()
        writer.writerows(all_ratings)

with open('all_player_ratings.json', 'w') as f:
    json.dump(all_ratings, f, indent=2)

print("\n" + "="*60)
print(f"✅ COMPLETE!")
print(f"   Success: {len(all_ratings):,}")
print(f"   Failed: {len(failed):,}")
print(f"   Time: {(time.time() - start_time)/60:.1f} min")
print("="*60)
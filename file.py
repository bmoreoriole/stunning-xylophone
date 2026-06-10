import requests
from bs4 import BeautifulSoup
import re

url = "https://www.franchiseball.com/research/data/index/players/pg/0"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

player_links = soup.find_all('a', class_='player-bubble')
print(f"Found {len(player_links)} player links on page 0")

if player_links:
    for link in player_links[:5]:
        print(f"  Link: {link}")
        print(f"  rel: {link.get('rel')}")
        print(f"  href: {link.get('href')}")
        print(f"  text: {link.text.strip()}")
        print()
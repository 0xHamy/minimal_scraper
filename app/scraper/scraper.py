import requests
from bs4 import BeautifulSoup
import base64
import json

def scrape_posts():
    """Scrape posts from a darknet marketplace and return base64-encoded JSON."""
    proxies = {
        'http': 'socks5h://172.17.0.2:9050',
        'https': 'socks5h://172.17.0.2:9050'
    }
    url = 'http://p5uxnaqbs77uklgg2r6rmwteo3snvaojh57buniphkpckmxwgcx5i2qd.onion/marketplace/sellers'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, proxies=proxies, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='table')
        if not table:
            raise ValueError("Table not found in HTML")
        posts = []
        for row in table.find('tbody').find_all('tr'):
            cells = row.find_all('td')
            if len(cells) != 3:
                continue
            title_cell = cells[0]
            title = title_cell.text.strip()
            link = title_cell.find('a')['href']
            if link.startswith('/'):
                link = 'http://p5uxnaqbs77uklgg2r6rmwteo3snvaojh57buniphkpckmxwgcx5i2qd.onion' + link
            category = cells[1].text.strip()
            date_str = cells[2].text.strip()
            posts.append({
                'title': title,
                'category': category,
                'date': date_str,
                'link': link
            })
        posts_json = json.dumps({'posts': posts})
        return base64.b64encode(posts_json.encode('utf-8')).decode('utf-8')
    except Exception as e:
        raise e


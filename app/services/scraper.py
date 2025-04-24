import requests
from bs4 import BeautifulSoup
import base64
import json

def scrape_posts(onion_url, proxies, headers=None, timeout=30):
    """Scrape posts from a darknet marketplace and return base64-encoded JSON.
    
    Args:
        onion_url (str): The onion URL to scrape
        proxies (dict): Proxy configuration for HTTP/HTTPS
        headers (dict, optional): HTTP headers for the request
        timeout (int, optional): Request timeout in seconds. Defaults to 30
    
    Returns:
        str: Base64-encoded JSON string of scraped posts
    """
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    try:
        response = requests.get(onion_url, proxies=proxies, headers=headers, timeout=timeout)
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
                link = onion_url.rstrip('/') + link
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


if __name__ == "__main__":
    proxies = {
        'http': 'socks5h://172.23.0.2:9050',
        'https': 'socks5h://172.23.0.2:9050'
    }
    onion_url = 'http://ft4uneyq3hu3txsmw6rnzrzrgxcbddze3hukj3kef6pvtlaycu6f7jid.onion/marketplace/sellers'
    try:
        result = scrape_posts(onion_url, proxies)
        print(result)
    except Exception as e:
        print(f"Error: {str(e)}")


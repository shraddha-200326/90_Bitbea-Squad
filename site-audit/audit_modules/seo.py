from bs4 import BeautifulSoup
import requests
from audit_modules.fetch_html import fetch_html

def check_seo(url):
    results = {}
    html = fetch_html(url)
    if "Error" in html:
        return {"error": html}

    soup = BeautifulSoup(html, 'html.parser')

    results['title_tag'] = bool(soup.title and soup.title.string)
    results['meta_description'] = bool(soup.find('meta', attrs={'name': 'description'}))
    results['h1_tag'] = bool(soup.find('h1'))
    results['alt_attributes'] = all(img.has_attr('alt') for img in soup.find_all('img'))

    try:
        robots = requests.get(url.rstrip('/') + '/robots.txt')
        results['robots_txt'] = robots.status_code == 200
    except:
        results['robots_txt'] = False

    return results

import requests

def check_headers(url):
    response = requests.get(url)
    headers = response.headers
    security_headers = {
        'Content-Security-Policy': headers.get('Content-Security-Policy', 'Missing'),
        'X-Frame-Options': headers.get('X-Frame-Options', 'Missing'),
        'Strict-Transport-Security': headers.get('Strict-Transport-Security', 'Missing'),
        'X-Content-Type-Options': headers.get('X-Content-Type-Options', 'Missing'),
    }
    return security_headers

import requests

def expand_url(url: str) -> str:
    try:
        resp = requests.get(
            url,
            allow_redirects=True,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )
        return resp.url
    except:
        return url

import re
import time
import json
import hashlib
import requests
from typing import Tuple, Optional

APP_ID = "18353340769"
SECRET = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"
API_URL = "https://open-api.affiliate.shopee.com.br/graphql"

# 1) Utilitárias
def extract_item_id(product_url: str) -> Optional[str]:
    for pattern in [r'-i\.\d+\.(\d+)', r'/product/\d+/(\d+)']:
        m = re.search(pattern, product_url)
        if m:
            return m.group(1)
    return None

def generate_signature(payload: str, timestamp: int) -> str:
    s = f"{APP_ID}{timestamp}{payload}{SECRET}"
    return hashlib.sha256(s.encode()).hexdigest()

# 2) Scraping puro do HTML da Shopee (título, imagem, preços)
def scrape_shopee_html(url: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Retorna: (title, image_url, current_price, original_price)
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9",
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return None, None, None, None
        html = r.text

        # título pela meta tag og:title
        m_title = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
        title = m_title.group(1).strip() if m_title else None

        # imagem principal pela meta tag og:image
        m_img = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
        image = m_img.group(1).strip() if m_img else None

        # preço atual: classe IZPeQz
        m_curr = re.search(r'<div\s+class="IZPeQz[^"]*">\s*(R\$[\d.,]+)\s*</div>', html)
        current_price = m_curr.group(1).strip() if m_curr else None

        # preço original riscado: classe ZA5sW5
        m_orig = re.search(r'<div\s+class="ZA5sW5[^"]*">\s*(R\$[\d.,]+)\s*</div>', html)
        original_price = m_orig.group(1).strip() if m_orig else None

        return title, image, current_price, original_price

    except Exception:
        return None, None, None, None

# 3) Função principal
def get_shopee_product_info(product_url: str) -> dict:
    item_id = extract_item_id(product_url)
    if not item_id:
        return {
            "title": None,
            "price": None,
            "original_value": None,
            "caption": "❌ Não foi possível identificar o produto.",
            "image": None,
            "url": product_url,
        }

    timestamp = int(time.time())
    short_link = product_url  # default fallback

    # Tenta gerar short_link via GraphQL
    try:
        payload1 = {"query": f"""
            mutation {{
              generateShortLink(input: {{
                originUrl: "{product_url}",
                subIds: ["s1"]
              }}) {{
                shortLink
              }}
            }}
        """}
        pj1 = json.dumps(payload1, separators=(",", ":"))
        sig1 = generate_signature(pj1, timestamp)
        h1 = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={sig1}"
        }
        resp1 = requests.post(API_URL, data=pj1, headers=h1, timeout=15)
        j1 = resp1.json()
        sl = j1.get("data", {}).get("generateShortLink", {}).get("shortLink")
        if sl:
            short_link = sl
    except Exception:
        # qualquer erro, fallback para URL original
        short_link = product_url

    # Tenta buscar via API
    productname = None
    price_api = None
    original_api = None
    image_api = None
    try:
        payload2 = {"query": f"""
          query {{
            productOfferV2(itemId:{item_id}) {{
              nodes {{
                productName
                priceMin
                priceMax
                imageUrl
              }}
            }}
          }}
        """}
        pj2 = json.dumps(payload2, separators=(",", ":"))
        sig2 = generate_signature(pj2, timestamp)
        h2 = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={sig2}"
        }
        resp2 = requests.post(API_URL, data=pj2, headers=h2, timeout=15)
        j2 = resp2.json()
        nodes = j2.get("data", {}).get("productOfferV2", {}).get("nodes") or []
        if nodes:
            n = nodes[0]
            productname = n.get("productName")
            priceMin = n.get("priceMin")
            priceMax = n.get("priceMax")
            image_api = n.get("imageUrl")
            if priceMin is not None:
                price_api = f"R$ {float(priceMin):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            if priceMax is not None and priceMax != priceMin:
                original_api = f"R$ {float(priceMax):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        pass

    # Scraping do HTML (sempre tenta)
    title_html, image_html, curr_html, orig_html = scrape_shopee_html(product_url)

    # Prioriza API > HTML
    title = productname or title_html or "Desconhecido"
    image = image_api or image_html
    price = price_api or curr_html or "Preço indisponível"
    original = original_api or orig_html

    # Monta caption
    if original and price != "Preço indisponível":
        caption = f"📦 {title}\n💰 De {original} por {price}\n🔗 {short_link}"
    else:
        caption = f"📦 {title}\n💰 {price}\n🔗 {short_link}"

    return {
        "title": title,
        "price": price,
        "original_value": original,
        "caption": caption,
        "image": image,
        "url": short_link,
    }

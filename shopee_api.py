import re
import time
import json
import hashlib
import requests
from typing import Tuple, Optional

# PLAYWRIGHT
from playwright.sync_api import sync_playwright

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

# 2) Scraping HTML simples (sem JS)
def scrape_shopee_html(url: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
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

        m_title = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
        title = m_title.group(1).strip() if m_title else None

        m_img = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
        image = m_img.group(1).strip() if m_img else None

        m_curr = re.search(r'R\$\s?\d+[,\.]\d{2}', html)
        current_price = m_curr.group(0) if m_curr else None

        return title, image, current_price, None
    except Exception:
        return None, None, None, None

# 3) Scraping com Playwright (JS executado)
def scrape_shopee_playwright(url: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )

            page = browser.new_page(
                locale="pt-BR",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )

            page.goto(url, timeout=60000, wait_until="domcontentloaded")

            # Aguarda o bloco de preço principal
            page.wait_for_selector("div.jRlVo0", timeout=15000)

            # Meta informações
            title = page.locator('meta[property="og:title"]').get_attribute("content")
            image = page.locator('meta[property="og:image"]').get_attribute("content")

            current_price = None
            original_price = None

            # Preço atual (classe mais estável)
            if page.locator("div.IZPeQz").count() > 0:
                current_price = page.locator("div.IZPeQz").first.inner_text().strip()

            # Preço riscado (classe mais estável)
            if page.locator("div.ZA5sW5").count() > 0:
                original_price = page.locator("div.ZA5sW5").first.inner_text().strip()

            # Fallback extra (caso Shopee mude classes)
            if not current_price:
                prices = page.locator("text=/R\\$\\s?\\d+/").all_inner_texts()
                if prices:
                    current_price = prices[0]

            browser.close()

            return title, image, current_price, original_price

    except Exception:
        return None, None, None, None


# 4) Função principal
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
    short_link = product_url

    # Short link
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
        short_link = resp1.json()["data"]["generateShortLink"]["shortLink"]
    except Exception:
        pass

    # API produto
    productname = price_api = original_api = image_api = None
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
        nodes = resp2.json()["data"]["productOfferV2"]["nodes"]
        if nodes:
            n = nodes[0]
            productname = n["productName"]
            image_api = n["imageUrl"]
            price_api = f"R$ {float(n['priceMin']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            if n["priceMax"] != n["priceMin"]:
                original_api = f"R$ {float(n['priceMax']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        pass

    # HTML simples
    title_html, image_html, curr_html, orig_html = scrape_shopee_html(product_url)

    # Playwright (último fallback)
    title_pw, image_pw, curr_pw, orig_pw = scrape_shopee_playwright(product_url)

    # Prioridade final
    title = productname or title_html or title_pw or "Desconhecido"
    image = image_api or image_html or image_pw
    price = price_api or curr_html or curr_pw or "Preço indisponível"
    original = original_api or orig_html or orig_pw

    caption = f"📦 {title}\n💰 {price}\n🔗 {short_link}"
    if original:
        caption = f"📦 {title}\n💰 De {original} por {price}\n🔗 {short_link}"

    return {
        "title": title,
        "price": price,
        "original_value": original,
        "caption": caption,
        "image": image,
        "url": short_link,
    }

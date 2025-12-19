import re
from requests_html import HTMLSession
from bs4 import BeautifulSoup

MAGALU_STORE = "in_603815"

def format_magalu_store(store_id: str) -> str:
    if not store_id.startswith("in_"):
        return store_id[:2] + "_" + store_id[2:]
    return store_id

def _sanitize(text):
    if not text:
        return None
    return text.replace('\xa0', ' ').replace('\u202f', ' ').strip()

def _parse_money(s):
    if not s:
        return None
    s = s.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(s)
    except:
        return None

def _format_money(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def _extract_discount_parts(discount_text):
    if not discount_text:
        return None, None
    m = re.search(r'(\d+(?:[.,]\d+)?%)', discount_text)
    percent = (m.group(1).replace(',', '.') + " OFF") if m else None
    m2 = re.search(r'OFF\s*(.+)', discount_text, re.I)
    method = m2.group(1).strip() if m2 else None
    return percent, method

def get_magalu_product_info(product_url):
    try:
        loja_corrigida = format_magalu_store(MAGALU_STORE)

        # Construir affiliate_link
        path = re.sub(r'https?://(www\.)?magazineluiza\.com\.br', '', product_url)
        affiliate_link = f"https://www.magazinevoce.com.br/magazine{loja_corrigida}{path}"

        session = HTMLSession()
        resp = session.get(product_url)
        resp.html.render(timeout=20, sleep=1)  # renderiza JS

        soup = BeautifulSoup(resp.html.html, "html.parser")

        # Nome e imagem
        tag = soup.find("meta", property="og:title")
        name = _sanitize(tag.get("content")) if tag else "Produto Magalu"

        tag = soup.find("meta", property="og:image")
        image = tag.get("content") if tag else None

        # Preço atual e antigo
        price_current_tag = soup.find(attrs={"data-testid": "price-value"})
        price_current = _sanitize(price_current_tag.get_text()) if price_current_tag else None

        price_old_tag = soup.find(attrs={"data-testid": "price-original"})
        price_old = _sanitize(price_old_tag.get_text()) if price_old_tag else None

        # Desconto
        discount_tag = soup.find(attrs={"data-testid": "tag"})
        discount_text = _sanitize(discount_tag.get_text()) if discount_tag else None
        discount_percent, discount_method = _extract_discount_parts(discount_text)

        # Monta texto final
        if price_current:
            price_text = f"💰 {price_current}"
            if price_old:
                price_text += f" (de {price_old})"
            if discount_percent and discount_method:
                price_text += f" - {discount_percent} {discount_method}"
        else:
            price_text = "Preço indisponível"

        return name, price_text, affiliate_link, image

    except Exception as e:
        print("Erro Magalu:", e)
        return "Produto Magalu", "Preço indisponível", product_url, None

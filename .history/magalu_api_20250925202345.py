import re, requests
from bs4 import BeautifulSoup

MAGALU_STORE = "in_603815"

def format_magalu_store(store_id: str) -> str:
    if not store_id.startswith("in_"):
        return store_id[:2] + "_" + store_id[2:]
    return store_id

def format_price(price_str):
    """Formata preço string tipo '130,60' ou float em 'R$ 130,60'"""
    try:
        if isinstance(price_str, str):
            price_float = float(price_str.replace(".", "").replace(",", "."))
        else:
            price_float = float(price_str)
        return f"{price_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return price_str

def get_magalu_product_info(product_url):
    try:
        loja_corrigida = format_magalu_store(MAGALU_STORE)
        if "magazinevoce.com.br" in product_url:
            affiliate_link = product_url
        else:
            path = re.sub(r"https?://www\.magazineluiza\.com\.br", "", product_url)
            affiliate_link = f"https://www.magazinevoce.com.br/magazine{loja_corrigida}{path}"

        headers = {"User-Agent": "Mozilla/5.0","Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"}
        resp = requests.get(affiliate_link, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Nome
        tag = soup.find("meta", property="og:title")
        name = tag.get("content") if tag else "Produto Magalu"

        # Imagem
        tag = soup.find("meta", property="og:image")
        image = tag.get("content") if tag else None

        # Preço atual
        match = re.search(r'"price":\s*"?([\d,\.]+)"?', resp.text)
        price_current = match.group(1) if match else None
        if price_current:
            price_current_formatted = format_price(price_current)
            # Simula preço antigo (+30%)
            price_estimated_old = float(price_current.replace(".", "").replace(",", ".")) * 1.3
            price_old_formatted = format_price(price_estimated_old)
            price_text = f"💰 R$ {price_current_formatted} (de R$ {price_old_formatted})"
        else:
            price_text = "Preço indisponível"

        return name, price_text, affiliate_link, image

    except Exception as e:
        print("Erro Magalu:", e)
        return "Produto Magalu", "Preço indisponível", product_url, None

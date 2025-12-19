import re
import requests
from bs4 import BeautifulSoup

def get_magalu_product_info(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        return "Produto indisponível", "Preço indisponível", url

    soup = BeautifulSoup(resp.text, "html.parser")

    # Título
    title_tag = soup.find("h1", {"class": re.compile("header-product-title|sc-.*")})
    title = title_tag.get_text(strip=True) if title_tag else "Título indisponível"

    # Preço à vista / Pix
    pix_tag = soup.find("p", string=re.compile("no Pix")) or soup.find("span", string=re.compile("no Pix"))
    price_pix = pix_tag.get_text(strip=True) if pix_tag else None

    # Preço parcelado (cartão)
    card_tag = soup.find("p", string=re.compile("sem juros")) or soup.find("span", string=re.compile("sem juros"))
    price_card = card_tag.get_text(strip=True) if card_tag else None

    # Caso não encontre na página, tenta buscar no JSON embutido
    if not price_pix or not price_card:
        match = re.search(r'"price":\s*([\d\.]+),\s*"paymentCondition":"([^"]+)"', resp.text)
        if match:
            price_number = float(match.group(1))
            condition = match.group(2)
            if "Pix" in condition and not price_pix:
                price_pix = f"R$ {price_number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            if "cart" in condition.lower() and not price_card:
                price_card = condition

    # Ajusta saída
    if price_pix and price_card:
        price_info = f"💰 {price_pix} | 💳 {price_card}"
    elif price_pix:
        price_info = f"💰 {price_pix}"
    elif price_card:
        price_info = f"💳 {price_card}"
    else:
        price_info = "Preço indisponível"

    return title, price_info, url


# 🔹 Teste
url = "https://www.magazineluiza.com.br/smart-tv-40-britania-btv40m9gr2cgb-roku-led-dolby-audio/p/ff4g7c5gf9/et/elit/?seller_id=123comprou"
titulo, preco, link = get_magalu_product_info(url)
print("🛒", titulo, "na Magalu por", preco)
print("🔗", link)

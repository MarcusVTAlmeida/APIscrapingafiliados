import re
import requests
from bs4 import BeautifulSoup

MAGALU_STORE = "in_603815"

def format_magalu_store(store_id: str) -> str:
    if not store_id.startswith("in_"):
        return store_id[:2] + "_" + store_id[2:]
    return store_id

def get_magalu_product_info(product_url):
    try:
        loja_corrigida = format_magalu_store(MAGALU_STORE)
        if "magazinevoce.com.br" in product_url:
            affiliate_link = product_url
        else:
            path = re.sub(r"https?://www\.magazineluiza\.com\.br", "", product_url)
            affiliate_link = f"https://www.magazinevoce.com.br/magazine{loja_corrigida}{path}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
        }
        resp = requests.get(product_url, headers=headers, timeout=10)  # <<< alterado para usar o link original
        soup = BeautifulSoup(resp.text, "html.parser")

        # Nome
        tag = soup.find("meta", property="og:title")
        name = tag.get("content") if tag else "Produto Magalu"

        # Imagem
        tag = soup.find("meta", property="og:image")
        image = tag.get("content") if tag else None

        # Preço no Pix
        price_pix_tag = soup.find("p", {"data-testid": "price-value"})
        price_pix = price_pix_tag.get_text(strip=True).replace("ou ", "") if price_pix_tag else None

        # Texto "no Pix"
        pix_method_tag = soup.find("span", {"data-testid": "in-cash"})
        pix_method = pix_method_tag.get_text(strip=True) if pix_method_tag else None

        # Desconto Pix (10%, 15% etc.)
        discount_tag = soup.find("span", class_="sc-faUjhM")
        discount_text = discount_tag.get_text(strip=True) if discount_tag else None

        # Preço no cartão (normal, sem desconto)
        price_card_tag = soup.select_one('div[data-testid="mod-bestinstallment"] p')
        price_card = price_card_tag.get_text(strip=True) if price_card_tag else None

        # Monta o texto final de preço
        if price_pix:
            price_text = f"💰 {price_pix}"
            if pix_method:
                price_text += f" ({pix_method})"
            if discount_text:
                price_text += f" - {discount_text}"
            if price_card:
                price_text += f" | 💳 {price_card} no cartão"
        else:
            price_text = "Preço indisponível"

        return name, price_text, affiliate_link, image

    except Exception as e:
        print("Erro Magalu:", e)
        return "Produto Magalu", "Preço indisponível", product_url, None

import re
import json
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
        resp = requests.get(affiliate_link, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Nome do produto
        tag = soup.find("meta", property="og:title")
        name = tag.get("content") if tag else "Produto Magalu"

        # Imagem
        tag = soup.find("meta", property="og:image")
        image = tag.get("content") if tag else None

        # -------------------
        # 1) HTML scraping
        # -------------------
        price_pix_tag = soup.find("p", {"data-testid": "price-value"})
        price_pix = price_pix_tag.get_text(strip=True).replace("ou ", "") if price_pix_tag else None

        pix_method_tag = soup.find("span", {"data-testid": "in-cash"})
        pix_method = pix_method_tag.get_text(strip=True) if pix_method_tag else None

        discount_tag = soup.find("span", string=re.compile(r"desconto", re.I))
        discount = discount_tag.get_text(strip=True) if discount_tag else None

        # Tenta capturar preço do cartão
        price_card = None
        for p in soup.find_all("p"):
            txt = p.get_text()
            if "R$" in txt and "ou " not in txt and "Cartão" not in txt:
                price_card = txt.strip()
                break

        # -------------------
        # 2) Fallback JSON-LD
        # -------------------
        if not price_pix or not price_card:
            json_ld = soup.find("script", type="application/ld+json")
            if json_ld:
                try:
                    data = json.loads(json_ld.string)
                    if isinstance(data, list):  # às vezes vem como lista
                        data = data[0]

                    if not price_pix and "offers" in data:
                        price_pix = f"R$ {data['offers'].get('price')}"
                    if not name and "name" in data:
                        name = data["name"]
                    if not image and "image" in data:
                        image = data["image"]
                except Exception:
                    pass

        # Monta o texto final
        if price_pix:
            price_text = f"💰 {price_pix}"
            if pix_method:
                price_text += f" ({pix_method})"
            if discount:
                price_text += f" - {discount}"
            if price_card:
                price_text += f" | 💳 {price_card} no cartão"
        else:
            price_text = "Preço indisponível"

        return name, price_text, affiliate_link, image

    except Exception as e:
        print("Erro Magalu:", e)
        return "Produto Magalu", "Preço indisponível", product_url, None

import re
import requests
import json
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

        # --------------------------
        # Busca preço no Pix
        # --------------------------
        price_pix = None
        pix_method, discount = None, None

        # 1) Método atual (quando existe <p data-testid="price-value">)
        tag = soup.find("p", {"data-testid": "price-value"})
        if tag:
            price_pix = tag.get_text(strip=True).replace("ou ", "")

        # 2) Novo: quando vem dentro de <div data-testid="pix-panel">
        if not price_pix:
            tag = soup.select_one("div[data-testid='pix-panel'] span.sc-cspYLC")
            if tag:
                price_pix = tag.get_text(strip=True)

        # 3) Novo: quando vem dentro de <div data-testid='showcase-price'>
        if not price_pix:
            tag = soup.select_one("div[data-testid='showcase-price'] div")
            if tag and "R$" in tag.get_text():
                price_pix = tag.get_text(strip=True).split(" ")[0] + " " + tag.get_text(strip=True).split(" ")[1]

        # Forma de pagamento (Pix, Boleto, etc)
        tag = soup.find("span", {"data-testid": "in-cash"})
        if tag:
            pix_method = tag.get_text(strip=True)

        # Desconto
        tag = soup.find("span", string=re.compile(r"desconto", re.I))
        if tag:
            discount = tag.get_text(strip=True)

        # --------------------------
        # Preço no cartão
        # --------------------------
        price_card = None

        # Padrão antigo
        for p in soup.find_all("p"):
            txt = p.get_text()
            if "R$" in txt and "Cartão" not in txt and "Pix" not in txt:
                price_card = txt.strip()
                break

        # Novo: captura em <small> (ex: "ou 3x de R$ 79,30 no cartão")
        if not price_card:
            small_tag = soup.select_one("div[data-testid='showcase-price'] small")
            if small_tag:
                price_card = small_tag.get_text(strip=True)

        # --------------------------
        # Fallback JSON-LD
        # --------------------------
        if not price_pix or not price_card:
            json_ld = soup.find("script", type="application/ld+json")
            if json_ld:
                try:
                    data = json.loads(json_ld.string)
                    if isinstance(data, list):
                        data = data[0]
                    if not price_pix and "offers" in data:
                        price_pix = f"R$ {data['offers'].get('price')}"
                    if not name and "name" in data:
                        name = data["name"]
                    if not image and "image" in data:
                        image = data["image"]
                except Exception:
                    pass

        # --------------------------
        # Monta texto final
        # --------------------------
        if price_pix:
            price_text = f"💰 {price_pix}"
            if pix_method:
                price_text += f" ({pix_method})"
            if discount:
                price_text += f" - {discount}"
            if price_card:
                price_text += f" | 💳 {price_card}"
        else:
            price_text = "Preço indisponível"

        return name, price_text, affiliate_link, image

    except Exception as e:
        print("Erro Magalu:", e)
        return "Produto Magalu", "Preço indisponível", product_url, None

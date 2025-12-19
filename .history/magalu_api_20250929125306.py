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

        # link de afiliado (para retorno)
        path = re.sub(r"https?://www\.magazineluiza\.com\.br", "", product_url)
        affiliate_link = f"https://www.magazinevoce.com.br/magazine{loja_corrigida}{path}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
        }

        # ⚠️ aqui alteramos: busca SEMPRE no site oficial (magazineluiza)
        resp = requests.get(product_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Nome
        tag = soup.find("meta", property="og:title")
        name = tag.get("content") if tag else "Produto Magalu"

        # Imagem
        tag = soup.find("meta", property="og:image")
        image = tag.get("content") if tag else None

        # Preço atual
        price_current_tag = soup.find("p", {"data-testid": "price-value"})
        price_current = price_current_tag.text.strip() if price_current_tag else None

        # Preço antigo
        price_old_tag = soup.find("p", {"data-testid": "price-original"})
        price_old = price_old_tag.text.strip() if price_old_tag else None

        # Desconto
        discount_tag = soup.find("div", {"data-testid": "tag"})
        discount_text = discount_tag.text.strip() if discount_tag else None

        # Separar percentual e método
        discount_percent = None
        discount_method = None
        if discount_text:
            parts = discount_text.split("OFF")
            discount_percent = parts[0].strip() + "OFF" if len(parts) > 0 else None
            discount_method = parts[1].strip() if len(parts) > 1 else None

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

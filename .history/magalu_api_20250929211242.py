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
        resp = requests.get(affiliate_link, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        # -------------------
        # Nome e imagem
        # -------------------
        tag = soup.find("meta", property="og:title")
        name = tag.get("content") if tag else "Produto Magalu"

        tag = soup.find("meta", property="og:image")
        image = tag.get("content") if tag else None

        # -------------------
        # Preço Pix
        # -------------------
        pix_panel = soup.find("div", {"data-testid": "pix-panel"})
        if pix_panel:
            price_pix_tag = pix_panel.select_one("span.sc-cspYLC")
            discount_tag = pix_panel.select_one("span.sc-dwalKd")
            price_pix = price_pix_tag.get_text(strip=True) if price_pix_tag else None
            discount = discount_tag.get_text(strip=True) if discount_tag else None
            pix_text = f"{price_pix} (no Pix)"
            if discount:
                pix_text += f" com {discount}"
        else:
            pix_text = None

        # -------------------
        # Preço Cartão
        # -------------------
        card_panel = soup.find("div", {"data-testid": "mod-bestinstallment"})
        price_card = None
        if card_panel:
            total_tag = card_panel.select_one("p:nth-of-type(2)")  # valor total
            installment_tag = card_panel.select_one("p:nth-of-type(4)")  # parcelas
            if total_tag:
                price_card = total_tag.get_text(strip=True)
                if installment_tag:
                    price_card += f" ({installment_tag.get_text(strip=True)})"

        # -------------------
        # Monta o texto final
        # -------------------
        if pix_text:
            price_text = f"💰 {pix_text}"
            if price_card:
                price_text += f" | 💳 {price_card} no cartão"
        else:
            price_text = "Preço indisponível"

        return name, price_text, affiliate_link, image

    except Exception as e:
        print("Erro Magalu:", e)
        return "Produto Magalu", "Preço indisponível", product_url, None

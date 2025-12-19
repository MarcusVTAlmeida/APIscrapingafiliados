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
        pix_text = None
        discount = None
        pix_panel = soup.find("div", {"data-testid": "pix-panel"})
        if pix_panel:
            price_pix_tag = pix_panel.select_one("span.sc-cspYLC")
            discount_tag = pix_panel.select_one("span.sc-dwalKd")
            price_pix = price_pix_tag.get_text(strip=True) if price_pix_tag else None
            discount = discount_tag.get_text(strip=True) if discount_tag else None
            if price_pix:
                pix_text = f"{price_pix} (no Pix)"
                if discount:
                    pix_text += f" com {discount}"

        # -------------------
        # Preço Cartão
        # -------------------
       # -------------------
# Preço Cartão
# -------------------
price_card = None
card_panel = soup.find("div", {"data-testid": "mod-bestinstallment"})
if card_panel:
    total_tag = card_panel.select_one("p:nth-of-type(2)")  # valor total
    installment_tag = card_panel.select_one("p:nth-of-type(4)")  # parcelas
    if total_tag:
        price_card = total_tag.get_text(strip=True)
        if installment_tag:
            price_card += f" ({installment_tag.get_text(strip=True)})"

# Fallback: tenta buscar no showcase-price (caso do Smart TV)
if not price_card:
    showcase_price = soup.find("div", {"data-testid": "showcase-price"})
    if showcase_price:
        small_tag = showcase_price.find("small")
        if small_tag:
            price_card = small_tag.get_text(strip=True)


        # -------------------
        # Fallback com JSON-LD
        # -------------------
        if not pix_text or not price_card:
            json_ld = soup.find("script", type="application/ld+json")
            if json_ld:
                try:
                    data = json.loads(json_ld.string)
                    if isinstance(data, list):  # às vezes vem como lista
                        data = data[0]

                    if not name and "name" in data:
                        name = data["name"]
                    if not image and "image" in data:
                        image = data["image"]

                    if not pix_text and "offers" in data:
                        price = data["offers"].get("price")
                        if price:
                            pix_text = f"R$ {price} (no Pix)"
                except Exception:
                    pass

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

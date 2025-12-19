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
        name_tag = soup.find("meta", property="og:title")
        name = name_tag.get("content") if name_tag else "Produto Magalu"

        image_tag = soup.find("meta", property="og:image")
        image = image_tag.get("content") if image_tag else None

        # -------------------
        # Preço Pix (robusto)
        # -------------------
        pix_text = None
        pix_panel = soup.find("div", {"data-testid": "pix-panel"})
        if pix_panel:
            # preço principal
            price_tag = pix_panel.select_one("span.sc-cspYLC, span.sc-fmzyuX")
            price = price_tag.get_text(strip=True) if price_tag else None

            # desconto (se existir)
            discount_tag = pix_panel.select_one("span.sc-dwalKd, span.sc-dwalKd.jDyvFH")
            discount = discount_tag.get_text(strip=True) if discount_tag else None

            if price:
                pix_text = f"{price} (no Pix)"
                if discount:
                    pix_text += f" com {discount}"

        # -------------------
        # Preço Cartão (robusto)
        # -------------------
        card_text = None
        card_panel = soup.find("div", {"data-testid": "mod-bestinstallment"})
        if card_panel:
            # busca todos os <p> dentro do painel do cartão
            p_tags = card_panel.find_all("p")
            total_price, installments = None, None

            # procura preço total e parcelas
            for p in p_tags:
                txt = p.get_text(strip=True)
                if re.match(r"^R\$ ?\d", txt):
                    if not total_price:
                        total_price = txt
                    else:
                        installments = txt

            if total_price:
                card_text = total_price
                if installments:
                    card_text += f" ({installments})"

        # -------------------
        # Monta o texto final
        # -------------------
        if pix_text:
            price_text = f"💰 {pix_text}"
            if card_text:
                price_text += f" | 💳 {card_text} no cartão"
        elif card_text:
            price_text = f"💳 {card_text} no cartão"
        else:
            price_text = "Preço indisponível"

        return name, price_text, affiliate_link, image

    except Exception as e:
        print("Erro Magalu:", e)
        return "Produto Magalu", "Preço indisponível", product_url, None

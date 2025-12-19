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
        resp = requests.get(product_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Nome do produto
        tag = soup.find("meta", property="og:title")
        name = tag.get("content") if tag else "Produto Magalu"

        # Imagem
        tag = soup.find("meta", property="og:image")
        image = tag.get("content") if tag else None

        # -------------------
        # Preço no cartão (normal) e parcelamento
        # -------------------
        price_card = None
        installment_text = None
        for div in soup.find_all("div", {"data-testid": "mod-bestinstallment"}):
            # busca p dentro do div
            p_tag = div.find("p")
            if p_tag and "R$" in p_tag.text:
                price_card = p_tag.text.strip()
                break
        if not price_card:
            # fallback: pega qualquer R$ que não seja Pix
            for p in soup.find_all("p"):
                txt = p.get_text()
                if "R$" in txt and "ou " not in txt and "Cartão" not in txt:
                    price_card = txt.strip()
                    break

        # Parcelamento
        installment_tag = soup.find("p", {"data-testid": "installment"})
        if installment_tag:
            installment_text = installment_tag.get_text(strip=True)

        # -------------------
        # Preço no Pix (ou boleto) com desconto
        # -------------------
        price_pix_tag = soup.find("p", {"data-testid": "price-value"})
        price_pix = price_pix_tag.get_text(strip=True).replace("ou ", "") if price_pix_tag else None

        pix_method_tag = soup.find("span", {"data-testid": "in-cash"})
        pix_method = pix_method_tag.get_text(strip=True) if pix_method_tag else None

        discount_tag = soup.find("span", string=re.compile(r"desconto", re.I))
        discount = discount_tag.get_text(strip=True) if discount_tag else None

        # Monta o texto final
        price_text = ""
        if price_card:
            price_text = f"💳 {price_card} no cartão"
            if installment_text:
                price_text += f" ({installment_text})"
        if price_pix and price_pix != price_card:
            # só mostra se for diferente do cartão
            price_text += f" | 💰 {price_pix}"
            if pix_method:
                price_text += f" ({pix_method})"
            if discount:
                price_text += f" - {discount}"

        if not price_text:
            price_text = "Preço indisponível"

        return name, price_text, affiliate_link, image

    except Exception as e:
        print("Erro Magalu:", e)
        return "Produto Magalu", "Preço indisponível", product_url, None

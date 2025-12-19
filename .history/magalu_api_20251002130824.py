import re
import requests
from bs4 import BeautifulSoup
import random

MAGALU_STORE = "in_603815"

# -------------------
# Legendas prontas
# -------------------
LEGENDAS = [
    "🔥 Aproveite essa oferta incrível!",
    "✨ Promoção imperdível no Magalu!",
    "🛍️ Garanta já o seu com desconto!",
    "💯 Oferta válida por tempo limitado!",
    "🚀 Não perca essa oportunidade!",
    "😍 Olha só esse preço especial!",
    "⚡ Corre antes que acabe!",
]

def gerar_legenda():
    return random.choice(LEGENDAS)

def format_magalu_store(store_id: str) -> str:
    if not store_id.startswith("in_"):
        return store_id[:2] + "_" + store_id[2:]
    return store_id

def _parse_money_to_float(s: str):
    if not s:
        return None
    s = re.sub(r"[^\d,\.]", "", s)
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except:
        return None

def _format_money(v: float):
    if v is None:
        return None
    s = f"R$ {v:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

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

        # Nome e imagem
        name = soup.find("meta", property="og:title")
        name = name.get("content") if name else "Produto Magalu"
        image = soup.find("meta", property="og:image")
        image = image.get("content") if image else None

        # Preço
        price_text = None
        price_default = soup.find("div", {"data-testid": "price-default"})
        if price_default:
            orig_tag = price_default.find("p", {"data-testid": "price-original"})
            price_original = orig_tag.get_text(strip=True) if orig_tag else None
        else:
            price_original = None

        # PIX
        pix_panel = soup.find("div", {"data-testid": "pix-panel"})
        pix_text = None
        if pix_panel:
            price_elem = next((t for t in pix_panel.find_all(['span','p','div']) if "R$" in t.get_text()), None)
            if price_elem:
                pix_text = price_elem.get_text(strip=True)
                pix_text = re.sub(r'^\s*ou\s*', '', pix_text, flags=re.I)
                pix_text = pix_text.strip()

        # CARTÃO
        card_panel = soup.find("div", {"data-testid": "mod-bestinstallment"})
        card_text = None
        if card_panel:
            installment = next((t.get_text(strip=True) for t in card_panel.find_all(['p','span','div']) if re.search(r"\d+x.*R\$", t.get_text())), None)
            if installment:
                card_text = installment

        # Monta texto curto para Telegram
        parts = []
        if price_original:
            parts.append(f"De: {price_original}")
        if pix_text:
            parts.append(f"Por: {pix_text}")
        if card_text:
            parts.append(f"💳 {card_text} no cartão")

        price_text = " | ".join(parts) if parts else "Preço indisponível"

        return name, price_text, affiliate_link, image

    except Exception as e:
        print("Erro Magalu:", e)
        return "Produto Magalu", "Preço indisponível", product_url, None

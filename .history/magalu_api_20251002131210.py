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

        # -------------------
        # Nome e imagem
        # -------------------
        tag = soup.find("meta", property="og:title")
        name = tag.get("content") if tag else "Produto Magalu"

        tag = soup.find("meta", property="og:image")
        image = tag.get("content") if tag else None

        # -------------------
        # Preço Original (riscado)
        # -------------------
        price_original = None
        price_default = soup.find("div", {"data-testid": "price-default"})
        if price_default:
            orig_tag = price_default.find("p", {"data-testid": "price-original"})
            if orig_tag:
                price_original = orig_tag.get_text(strip=True)

        # -------------------
        # PIX
        # -------------------
        pix_text = None
        pix_panel = soup.find("div", {"data-testid": "pix-panel"})
        if pix_panel:
            price_elem = None
            for t in pix_panel.find_all(['span', 'p', 'div'], recursive=True):
                txt = t.get_text(" ", strip=True)
                if "R$" in txt:
                    price_elem = t
                    break
            price_pix = price_elem.get_text(" ", strip=True) if price_elem else None
            if price_pix:
                price_pix = re.sub(r'^\s*ou\s*', '', price_pix, flags=re.I)
                price_pix = price_pix.replace("ou", "", 1) if price_pix.startswith("ouR$") else price_pix
                price_pix = price_pix.strip()

            discount_elem = pix_panel.find(string=re.compile(r"desconto", re.I))
            discount = discount_elem.strip() if discount_elem else None

            pix_method_tag = pix_panel.find(attrs={"data-testid": "in-cash"})
            pix_method = pix_method_tag.get_text(strip=True) if pix_method_tag else "no Pix"

            if price_pix:
                pix_text = f"{price_pix} ({pix_method})"
                if discount:
                    pix_text += f" com {discount}"

        # -------------------
        # CARTÃO
        # -------------------
        card_text = None
        card_panel = soup.find("div", {"data-testid": "mod-bestinstallment"})
        if card_panel:
            total_candidate = None
            installment_candidate = None
            for t in card_panel.find_all(['p', 'span', 'div'], recursive=True):
                txt = t.get_text(" ", strip=True)
                if not txt:
                    continue
                if re.search(r"Cartão de crédito", txt, re.I):
                    continue
                if "R$" in txt:
                    if re.search(r"\d+\s*[xX]\s*(?:de\s*)?R\$|\d+\s*[xX]\s*R\$", txt):
                        installment_candidate = txt
                    else:
                        if not total_candidate:
                            total_candidate = txt
            if not total_candidate and installment_candidate:
                m = re.search(r"(\d+)\s*[xX]\s*(?:de\s*)?R\$\s*([\d\.,]+)", installment_candidate)
                if not m:
                    m = re.search(r"(\d+)\s*[xX]\s*R\$\s*([\d\.,]+)", installment_candidate)
                if m:
                    parcelas = int(m.group(1))
                    valor_parcela = float(m.group(2).replace(".", "").replace(",", "."))
                    total = parcelas * valor_parcela
                    total_str = _format_money(total)
                    card_text = f"{total_str} ({installment_candidate})"
                else:
                    card_text = installment_candidate
            else:
                if total_candidate:
                    if installment_candidate:
                        card_text = f"{total_candidate} ({installment_candidate})"
                    else:
                        card_text = total_candidate

        # -------------------
        # Monta o texto final
        # -------------------
# Monta texto curto para Telegram
parts = []
if price_original:
    parts.append(f"De: {price_original}")
if pix_text:
    parts.append(f"Por: {pix_text}")
if card_text:
    parts.append(f"💳 {card_text} no cartão")

# Apenas o preço (sem legenda)
price_text = " | ".join(parts) if parts else "Preço indisponível"

# Retorna name, preço, link e imagem
    return name, price_text, affiliate_link, image

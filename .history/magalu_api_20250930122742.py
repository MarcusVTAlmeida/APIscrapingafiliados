import re
import requests
from bs4 import BeautifulSoup

def get_magalu_product_info(product_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(product_url, headers=headers, timeout=15)

    if resp.status_code != 200:
        return "Produto indisponível", "Preço indisponível", product_url, None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Nome do produto
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else "Nome não encontrado"

    # Preço atual (Pix / principal)
    pix_price = None
    pix_el = soup.select_one('span[data-testid="price-value"]') or soup.select_one('p[data-testid="price-value"]')
    if pix_el:
        pix_price = pix_el.get_text(strip=True)

    # Preço original (riscado)
    original_price = None
    orig_el = soup.select_one('span[data-testid="price-original"]') or soup.find("del")
    if orig_el:
        original_price = orig_el.get_text(strip=True)

    # Preço parcelado no cartão
    card_price = None
    card_el = soup.select_one('span[data-testid="installment"]')
    if card_el:
        card_price = card_el.get_text(strip=True)

    # Construindo saída
    parts = []
    if pix_price:
        parts.append(f"💰 {pix_price} (no Pix)")
    if card_price:
        parts.append(f"💳 {card_price} no cartão")
    if original_price:
        parts.append(f"❌ De {original_price}")

    price_text = " | ".join(parts) if parts else "Preço não encontrado"

    return title, price_text, product_url, pix_price


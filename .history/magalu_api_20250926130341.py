import re
import requests
from bs4 import BeautifulSoup
import json

MAGALU_STORE = "in_603815"

def format_magalu_store(store_id: str) -> str:
    if not store_id.startswith("in_"):
        return store_id[:2] + "_" + store_id[2:]
    return store_id

def _sanitize(text):
    if not text:
        return None
    return text.replace('\xa0', ' ').replace('\u202f', ' ').strip()

def _parse_money(s):
    if not s:
        return None
    s = s.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(s)
    except:
        return None

def _format_money(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def get_magalu_product_info(product_url):
    try:
        loja_corrigida = format_magalu_store(MAGALU_STORE)

        # Construir affiliate_link
        path = re.sub(r'https?://(www\.)?magazineluiza\.com\.br', '', product_url)
        affiliate_link = f"https://www.magazinevoce.com.br/magazine{loja_corrigida}{path}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
        }
        resp = requests.get(product_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Nome e imagem
        tag = soup.find("meta", property="og:title")
        name = _sanitize(tag.get("content")) if tag else "Produto Magalu"

        tag = soup.find("meta", property="og:image")
        image = tag.get("content") if tag else None

        # Procurar JSON-LD
        price_current = None
        price_old = None
        discount_text = None
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                # Alguns JSON-LD são listas
                if isinstance(data, list):
                    for d in data:
                        if d.get("@type") == "Product":
                            offers = d.get("offers", {})
                            if isinstance(offers, list):
                                offer = offers[0]
                            else:
                                offer = offers
                            price_current = offer.get("price")
                            price_old = offer.get("priceValidUntil")  # nem sempre tem preço antigo
                            break
                elif data.get("@type") == "Product":
                    offers = data.get("offers", {})
                    if isinstance(offers, list):
                        offer = offers[0]
                    else:
                        offer = offers
                    price_current = offer.get("price")
                    price_old = offer.get("priceValidUntil")
                    break
            except:
                continue

        if price_current:
            price_text = f"💰 {_format_money(float(price_current))}"
            if price_old:
                price_text += f" (de {_format_money(float(price_old))})"
        else:
            price_text = "Preço indisponível"

        return name, price_text, affiliate_link, image

    except Exception as e:
        print("Erro Magalu:", e)
        return "Produto Magalu", "Preço indisponível", product_url, None

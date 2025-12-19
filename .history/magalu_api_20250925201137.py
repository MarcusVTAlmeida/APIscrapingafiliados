import re, requests
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

        headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"}
        resp = requests.get(affiliate_link, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Nome
        tag = soup.find("meta", property="og:title")
        name = tag.get("content") if tag else "Produto Magalu"

        # Imagem
        tag = soup.find("meta", property="og:image")
        image = tag.get("content") if tag else None

        # Preço com e sem desconto
        # Primeiro tentamos capturar o preço "normal" e o preço atual
        price_current = None
        price_original = None

        # Busca em JSON dentro do script
        script_tags = soup.find_all("script", type="application/ld+json")
        for script in script_tags:
            try:
                json_text = script.string
                if not json_text:
                    continue
                # Preço atual
                match_current = re.search(r'"price"\s*:\s*"([\d,.]+)"', json_text)
                if match_current:
                    price_current = match_current.group(1).replace(".", "").replace(",", ".")
                # Preço original (em desconto)
                match_original = re.search(r'"priceBeforeDiscount"\s*:\s*"([\d,.]+)"', json_text)
                if match_original:
                    price_original = match_original.group(1).replace(".", "").replace(",", ".")
            except:
                continue

        # Formata os valores
        price_text = ""
        if price_current:
            price_text = f"R$ {price_current}"
            if price_original and price_original != price_current:
                price_text = f"💰 {price_text} (de R$ {price_original})"
        else:
            price_text = "Preço indisponível"

        return name, price_text, affiliate_link, image

    except Exception as e:
        print("Erro Magalu:", e)
        return "Produto Magalu", "Preço indisponível", product_url, None

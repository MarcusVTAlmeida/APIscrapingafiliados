import re, requests
from bs4 import BeautifulSoup

MAGALU_STORE = "in_603815"

def format_magalu_store(store_id: str) -> str:
    if not store_id.startswith("in_"):
        return store_id[:2] + "_" + store_id[2:]
    return store_id

def format_price(price_str):
    """
    Converte string do tipo '1.234,56' ou '130,60' em '130,60' formatado corretamente
    """
    if not price_str:
        return None
    price_str = price_str.strip()
    # Remove pontos de milhar
    price_str = price_str.replace(".", "")
    # Substitui vírgula por ponto para conversão float
    try:
        value = float(price_str.replace(",", "."))
        # Retorna formatado com vírgula e 2 casas decimais
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return price_str

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

        # Nome do produto
        tag = soup.find("meta", property="og:title")
        name = tag.get("content") if tag else "Produto Magalu"

        # Imagem
        tag = soup.find("meta", property="og:image")
        image = tag.get("content") if tag else None

        # Preço atual e original
        price_current = None
        price_original = None

        # 1️⃣ Tenta pegar via JSON LD
        script_tags = soup.find_all("script", type="application/ld+json")
        for script in script_tags:
            try:
                json_text = script.string
                if not json_text:
                    continue
                match_current = re.search(r'"price"\s*:\s*"([\d,.]+)"', json_text)
                if match_current:
                    price_current = format_price(match_current.group(1))
                match_original = re.search(r'"priceBeforeDiscount"\s*:\s*"([\d,.]+)"', json_text)
                if match_original:
                    price_original = format_price(match_original.group(1))
            except:
                continue

        # 2️⃣ Caso não tenha original, tenta pegar via "listPrice" no HTML
        if not price_original:
            match_original_alt = re.search(r'"listPrice"\s*:\s*"?([\d,.]+)"?', resp.text)
            if match_original_alt:
                price_original = format_price(match_original_alt.group(1))

        # 3️⃣ Caso não tenha atual, tenta pegar via "salePrice" no HTML
        if not price_current:
            match_current_alt = re.search(r'"salePrice"\s*:\s*"?([\d,.]+)"?', resp.text)
            if match_current_alt:
                price_current = format_price(match_current_alt.group(1))

        # Monta texto final do preço
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

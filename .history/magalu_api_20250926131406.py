import re
import requests

MAGALU_STORE = "in_603815"

def format_magalu_store(store_id: str) -> str:
    if not store_id.startswith("in_"):
        return store_id[:2] + "_" + store_id[2:]
    return store_id

def _parse_money(s):
    if not s:
        return None
    s = str(s).replace(".", "").replace(",", ".").strip()
    try:
        return float(re.sub(r"[^\d.]", "", s))
    except:
        return None

def _format_money(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def get_magalu_product_info(product_url):
    try:
        loja_corrigida = format_magalu_store(MAGALU_STORE)

        # Extrair o productId ou slug da URL
        m = re.search(r'/p/([\w-]+)', product_url)
        if not m:
            raise ValueError("URL inválida")
        product_slug = m.group(1)

        # API interna do Magalu para detalhes do produto
        api_url = f"https://www.magazineluiza.com.br/api/product/{product_slug}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
        }
        resp = requests.get(api_url, headers=headers, timeout=10)
        data = resp.json()

        # Nome e imagem
        name = data.get("name", "Produto Magalu")
        image = data.get("image", None)

        # Preço atual
        price_current = _parse_money(data.get("price", None))

        # Preço antigo (se houver)
        price_old = _parse_money(data.get("priceOld", None))

        # Desconto / tag
        discount_tag = None
        if "tags" in data and isinstance(data["tags"], list) and len(data["tags"]) > 0:
            discount_tag = data["tags"][0].get("name", None)

        # Montar texto final
        price_text = "Preço indisponível"
        if price_current:
            price_text = f"💰 {_format_money(price_current)}"
            if price_old:
                price_text += f" (de {_format_money(price_old)})"
            if discount_tag:
                price_text += f" - {discount_tag}"

        # Montar link de afiliado
        path = re.sub(r'https?://(www\.)?magazineluiza\.com\.br', '', product_url)
        affiliate_link = f"https://www.magazinevoce.com.br/magazine{loja_corrigida}{path}"

        return name, price_text, affiliate_link, image

    except Exception as e:
        print("Erro Magalu:", e)
        return "Produto Magalu", "Preço indisponível", product_url, None

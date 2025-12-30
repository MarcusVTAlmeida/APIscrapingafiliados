import re
import time
import json
import hashlib
import requests

APP_ID = "18353340769"
SECRET = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"
API_URL = "https://open-api.affiliate.shopee.com.br/graphql"


def extract_item_id(product_url):
    match = re.search(r'-i\.\d+\.(\d+)', product_url)
    if match:
        return match.group(1)
    match = re.search(r'/product/\d+/(\d+)', product_url)
    if match:
        return match.group(1)
    return None


def generate_signature(payload: str, timestamp: int) -> str:
    factor = f"{APP_ID}{timestamp}{payload}{SECRET}"
    return hashlib.sha256(factor.encode()).hexdigest()


def get_shopee_prices_from_html(url):
    """
    Fallback: extrai preço atual e preço original (riscado) do HTML da página Shopee.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None, None

        html = resp.text

        # Captura todo o bloco que contém os preços
        block_match = re.search(
            r'<div\s+class="flex\s+flex-column\s+IFdRIb">.*?</div>\s*</div>',
            html,
            re.DOTALL,
        )
        if not block_match:
            return None, None

        block = block_match.group(0)

        # Preço atual (sem desconto)
        current_match = re.search(
            r'<div\s+class="IZPeQz[^"]*">\s*(R\$[\d.,]+)\s*</div>',
            block,
        )
        # Preço original (riscado)
        original_match = re.search(
            r'<div\s+class="ZA5sW5[^"]*">\s*(R\$[\d.,]+)\s*</div>',
            block,
        )

        current_price = current_match.group(1).strip() if current_match else None
        original_price = original_match.group(1).strip() if original_match else None

        return current_price, original_price

    except Exception:
        return None, None


def get_shopee_product_info(product_url: str) -> dict:
    item_id = extract_item_id(product_url)
    if not item_id:
        return {
            "title": None,
            "price": None,
            "original_value": None,
            "caption": "❌ Não foi possível identificar o produto.",
            "image": None,
            "url": product_url,
        }

    timestamp = int(time.time())

    # 1) Gera link afiliado
    payload_shortlink = {
        "query": f"""mutation {{
            generateShortLink(input: {{
                originUrl: "{product_url}",
                subIds: ["s1"]
            }}) {{
                shortLink
            }}
        }}"""
    }
    payload_json = json.dumps(payload_shortlink, separators=(",", ":"))
    signature = generate_signature(payload_json, timestamp)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature}",
    }

    resp1 = requests.post(API_URL, data=payload_json, headers=headers, timeout=15)
    data1 = resp1.json()
    short_link = (
        data1.get("data", {})
        .get("generateShortLink", {})
        .get("shortLink")
    )
    if not short_link or data1.get("errors"):
        return {
            "title": None,
            "price": None,
            "original_value": None,
            "caption": "❌ Erro ao gerar link afiliado.",
            "image": None,
            "url": product_url,
        }

    # 2) Busca dados do produto pela API
    payload_product = {
        "query": f"""query {{
            productOfferV2(itemId:{item_id}) {{
                nodes {{
                    productName
                    priceMin
                    priceMax
                    imageUrl
                }}
            }}
        }}"""
    }
    payload_json2 = json.dumps(payload_product, separators=(",", ":"))
    signature2 = generate_signature(payload_json2, timestamp)
    headers2 = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature2}",
    }

    resp2 = requests.post(API_URL, data=payload_json2, headers=headers2, timeout=15)
    data2 = resp2.json()

    # Variáveis padrão
    productname = "Desconhecido"
    price_text = "Preço indisponível"
    original_value = None
    image_url = None

    nodes = (
        data2.get("data", {})
        .get("productOfferV2", {})
        .get("nodes", [])
    )
    if nodes:
        node = nodes[0]
        productname = node.get("productName", productname)
        min_price = node.get("priceMin")
        max_price = node.get("priceMax")
        image_url = node.get("imageUrl")

        if min_price is not None and max_price is not None:
            formatted_min = f"R$ {float(min_price):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            formatted_max = f"R$ {float(max_price):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            if min_price == max_price:
                price_text = formatted_min
            else:
                price_text = formatted_min
                original_value = formatted_max

    # 3) Fallback via HTML
    html_price, html_original = get_shopee_prices_from_html(product_url)
    if html_price:
        price_text = html_price
    if html_original:
        original_value = html_original

    # 4) Monta caption final
    if original_value and price_text != "Preço indisponível":
        caption = (
            f"📦 {productname}\n"
            f"💰 De {original_value} por {price_text}\n"
            f"🔗 {short_link}"
        )
    else:
        caption = (
            f"📦 {productname}\n"
            f"💰 {price_text}\n"
            f"🔗 {short_link}"
        )

    return {
        "title": productname,
        "price": price_text,
        "original_value": original_value,
        "caption": caption,
        "image": image_url,
        "url": short_link,
    }

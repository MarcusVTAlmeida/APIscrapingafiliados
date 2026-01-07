import re
import time
import json
import hashlib
import requests

API_URL = "https://open-api.affiliate.shopee.com.br/graphql"


# ===============================
# EXTRAI ITEM ID
# ===============================
def extract_item_id(product_url):
    match = re.search(r'-i\.\d+\.(\d+)', product_url)
    if match:
        return match.group(1)

    match = re.search(r'/product/\d+/(\d+)', product_url)
    if match:
        return match.group(1)

    return None


# ===============================
# ASSINATURA
# ===============================
def generate_signature(app_id, secret, payload, timestamp):
    factor = f"{app_id}{timestamp}{payload}{secret}"
    return hashlib.sha256(factor.encode()).hexdigest()


# ===============================
# FORMATA PREÇO
# ===============================
def format_price(value):
    if value is None:
        return None
    try:
        value = float(value) / 100
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return None


# ===============================
# FUNÇÃO PRINCIPAL
# ===============================
def get_shopee_product_info(product_url):
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

    # ===============================
    # LINK AFILIADO
    # ===============================
    payload_shortlink = {
        "query": f"""
        mutation {{
            generateShortLink(input: {{
                originUrl: "{product_url}",
                subIds: ["s1"]
            }}) {{
                shortLink
            }}
        }}
        """
    }

    payload_json = json.dumps(payload_shortlink, separators=(",", ":"))
    signature = generate_signature(payload_json, timestamp)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature}",
    }

    response = requests.post(
        API_URL,
        data=payload_json,
        headers=headers,
        timeout=10
    )

    data = response.json()
    short_link = data.get("data", {}).get("generateShortLink", {}).get("shortLink")

    if not short_link:
        return {
            "title": None,
            "price": None,
            "original_value": None,
            "caption": "❌ Erro ao gerar link afiliado.",
            "image": None,
            "url": product_url,
        }

    # ===============================
    # PRODUTO
    # ===============================
    payload_product = {
        "query": f"""
        query {{
            productOfferV2(itemId:{item_id}) {{
                nodes {{
                    productName
                    priceMin
                    priceMax
                    imageUrl
                }}
            }}
        }}
        """
    }

    payload_json_product = json.dumps(payload_product, separators=(",", ":"))
    signature_product = generate_signature(payload_json_product, timestamp)

    headers_product = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature_product}",
    }

    response2 = requests.post(
        API_URL,
        data=payload_json_product,
        headers=headers_product,
        timeout=10
    )

    info_data = response2.json()
    nodes = info_data.get("data", {}).get("productOfferV2", {}).get("nodes", [])

    if not nodes:
        return {
            "title": None,
            "price": None,
            "original_value": None,
            "caption": "❌ Produto sem oferta afiliada.",
            "image": None,
            "url": short_link,
        }

    node = nodes[0]

    productname = node.get("productName")
    min_price = node.get("priceMin")
    max_price = node.get("priceMax")
    image_url = node.get("imageUrl")

    price_text = None
    original_value = None

    if min_price:
        price_text = f"R$ {float(min_price)/100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if max_price and max_price != min_price:
        original_value = f"R$ {float(max_price)/100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    caption = (
        f"📦 {productname}\n"
        f"💰 {price_text}\n"
        f"🔗 {short_link}"
        if not original_value
        else
        f"📦 {productname}\n"
        f"💰 De {original_value} por {price_text}\n"
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

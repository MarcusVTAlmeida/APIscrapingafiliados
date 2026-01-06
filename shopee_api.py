import re
import time
import json
import hashlib
import requests

APP_ID = "18353340769"
SECRET = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"
API_URL = "https://open-api.affiliate.shopee.com.br/graphql"


# ===============================
# UTILIDADES
# ===============================

def extract_item_id(product_url):
    match = re.search(r'-i\.\d+\.(\d+)', product_url)
    if match:
        return match.group(1)

    match = re.search(r'/product/\d+/(\d+)', product_url)
    if match:
        return match.group(1)

    return None


def generate_signature(payload, timestamp):
    factor = f"{APP_ID}{timestamp}{payload}{SECRET}"
    return hashlib.sha256(factor.encode()).hexdigest()


def format_price(value):
    try:
        value = float(value) / 100000
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
            "discount": None,
            "caption": "❌ Não foi possível identificar o produto.",
            "image": None,
            "url": product_url,
        }

    timestamp = int(time.time())

    # ===============================
    # GERAR LINK AFILIADO
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

    response = requests.post(API_URL, data=payload_json, headers=headers, timeout=15)
    data = response.json()

    short_link = data.get("data", {}).get("generateShortLink", {}).get("shortLink")

    if not short_link or "errors" in data:
        return {
            "title": None,
            "price": None,
            "original_value": None,
            "discount": None,
            "caption": "❌ Erro ao gerar link afiliado.",
            "image": None,
            "url": product_url,
        }

    # ===============================
    # BUSCAR INFO DO PRODUTO
    # ===============================
    payload_product = {
        "query": f"""
        query {{
            productOfferV2(itemId:{item_id}) {{
                nodes {{
                    productName
                    price
                    priceBeforeDiscount
                    discount
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

    response2 = requests.post(API_URL, data=payload_json_product, headers=headers_product, timeout=15)
    info_data = response2.json()

    nodes = info_data.get("data", {}).get("productOfferV2", {}).get("nodes", [])

    if not nodes:
        return {
            "title": None,
            "price": None,
            "original_value": None,
            "discount": None,
            "caption": "❌ Produto não encontrado.",
            "image": None,
            "url": short_link,
        }

    node = nodes[0]

    productname = node.get("productName", "Desconhecido")
    image_url = node.get("imageUrl")

    price_raw = node.get("price")
    old_raw = node.get("priceBeforeDiscount")
    discount = node.get("discount")

    price_text = format_price(price_raw)
    original_value = (
        format_price(old_raw)
        if old_raw and old_raw != price_raw
        else None
    )

    # ===============================
    # CAPTION FINAL
    # ===============================
    if original_value and price_text:
        caption = (
            f"📦 {productname}\n"
            f"💰 De {original_value} por {price_text}\n"
            f"🏷️ Desconto: {discount}%\n"
            f"🔗 {short_link}"
        )
    else:
        caption = f"📦 {productname}\n💰 {price_text}\n🔗 {short_link}"

    return {
        "title": productname,
        "price": price_text,
        "original_value": original_value,
        "discount": discount,
        "caption": caption,
        "image": image_url,
        "url": short_link,
    }

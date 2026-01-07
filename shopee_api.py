import re
import time
import json
import hashlib
import requests

API_URL = "https://open-api.affiliate.shopee.com.br/graphql"


def extract_item_id(product_url):
    match = re.search(r'-i\.\d+\.(\d+)', product_url)
    if match:
        return match.group(1)

    match = re.search(r'/product/\d+/(\d+)', product_url)
    if match:
        return match.group(1)

    return None


def generate_signature(app_id, secret, payload, timestamp):
    factor = f"{app_id}{timestamp}{payload}{secret}"
    return hashlib.sha256(factor.encode()).hexdigest()


def format_price(value):
    try:
        value = float(value) / 100000
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return None


def get_shopee_product_info(product_url, app_id, secret):
    item_id = extract_item_id(product_url)

    if not item_id:
        return {"error": "Produto inválido"}

    # ===============================
    # GERAR LINK AFILIADO
    # ===============================
    timestamp = int(time.time())

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
    signature = generate_signature(app_id, secret, payload_json, timestamp)

    headers = {
        "Content-Type": "application/json",
        "Authorization": (
            f"SHA256 Credential={app_id},"
            f"Timestamp={timestamp},"
            f"Signature={signature}"
        ),
    }

    res = requests.post(API_URL, data=payload_json, headers=headers, timeout=15)
    data = res.json()

    short_link = data.get("data", {}).get("generateShortLink", {}).get("shortLink")
    if not short_link:
        return {"error": "Erro ao gerar link afiliado"}

    # ===============================
    # PRODUTO
    # ===============================
    timestamp = int(time.time())

    payload_product = {
        "query": f"""
        query {{
            productOfferV2(itemId:{item_id}) {{
                nodes {{
                    productName
                    priceMin
                    imageUrl
                }}
            }}
        }}
        """
    }

    payload_json_product = json.dumps(payload_product, separators=(",", ":"))
    signature_product = generate_signature(app_id, secret, payload_json_product, timestamp)

    headers_product = {
        "Content-Type": "application/json",
        "Authorization": (
            f"SHA256 Credential={app_id},"
            f"Timestamp={timestamp},"
            f"Signature={signature_product}"
        ),
    }

    res2 = requests.post(API_URL, data=payload_json_product, headers=headers_product, timeout=15)
    info = res2.json()

    nodes = info.get("data", {}).get("productOfferV2", {}).get("nodes", [])
    if not nodes:
        return {"error": "Produto não encontrado"}

    node = nodes[0]

    return {
        "title": node.get("productName"),
        "price": format_price(node.get("priceMin")),
        "image": node.get("imageUrl"),
        "url": short_link,
    }

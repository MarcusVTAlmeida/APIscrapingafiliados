import re
import time
import json
import hashlib
import requests
from typing import Optional

APP_ID = "18353340769"
SECRET = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"
API_URL = "https://open-api.affiliate.shopee.com.br/graphql"


# ======================================================
# UTILITÁRIOS
# ======================================================

def extract_ids(url: str):
    """
    Extrai shopId e itemId da Shopee
    Ex: -i.12345678.987654321
    """
    m = re.search(r"-i\.(\d+)\.(\d+)", url)
    if not m:
        return None, None
    return m.group(1), m.group(2)


def generate_signature(payload: str, timestamp: int) -> str:
    raw = f"{APP_ID}{timestamp}{payload}{SECRET}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ======================================================
# FUNÇÃO PRINCIPAL
# ======================================================

def get_shopee_product_info(product_url: str) -> dict:
    shop_id, item_id = extract_ids(product_url)

    if not item_id:
        return {
            "error": True,
            "message": "❌ Não foi possível identificar o produto Shopee.",
        }

    timestamp = int(time.time())
    short_link = product_url

    # --------------------------------------------------
    # GERAR LINK AFILIADO
    # --------------------------------------------------
    try:
        payload_link = {
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

        payload_json = json.dumps(payload_link, separators=(",", ":"))
        signature = generate_signature(payload_json, timestamp)

        headers = {
            "Content-Type": "application/json",
            "Authorization": (
                f"SHA256 Credential={APP_ID},"
                f"Timestamp={timestamp},"
                f"Signature={signature}"
            ),
        }

        res = requests.post(API_URL, data=payload_json, headers=headers, timeout=15)
        short_link = res.json()["data"]["generateShortLink"]["shortLink"]

    except Exception:
        pass  # mantém URL original se falhar


    # --------------------------------------------------
    # BUSCAR DADOS DO PRODUTO (API)
    # --------------------------------------------------
    try:
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

        payload_json = json.dumps(payload_product, separators=(",", ":"))
        signature = generate_signature(payload_json, timestamp)

        headers = {
            "Content-Type": "application/json",
            "Authorization": (
                f"SHA256 Credential={APP_ID},"
                f"Timestamp={timestamp},"
                f"Signature={signature}"
            ),
        }

        res = requests.post(API_URL, data=payload_json, headers=headers, timeout=15)
        nodes = res.json()["data"]["productOfferV2"]["nodes"]

        if not nodes:
            raise Exception("Produto não encontrado")

        product = nodes[0]

        price = (
            f"R$ {float(product['priceMin']):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        return {
            "title": product["productName"],
            "price": price,
            "image": product["imageUrl"],
            "url": short_link,
        }

    except Exception:
        return {
            "error": True,
            "message": "❌ Produto Shopee não encontrado via API.",
        }

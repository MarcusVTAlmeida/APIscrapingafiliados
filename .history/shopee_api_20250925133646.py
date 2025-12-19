import re, time, json, hashlib, requests

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

def generate_signature(payload, timestamp):
    factor = f"{APP_ID}{timestamp}{payload}{SECRET}"
    return hashlib.sha256(factor.encode()).hexdigest()

def get_shopee_product_info(product_url):
    item_id = extract_item_id(product_url)
    if not item_id:
        return None, None, None, None, None, None
    timestamp = int(time.time())

    # 1. Gerar link afiliado
    payload_shortlink = {
        "query": f"""
            mutation {{
              generateShortLink(input: {{ originUrl: "{product_url}", subIds: ["s1"] }}) {{
                shortLink
              }}
            }}
        """
    }
    payload_json = json.dumps(payload_shortlink, separators=(',', ':'))
    signature = generate_signature(payload_json, timestamp)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature}"
    }
    response = requests.post(API_URL, data=payload_json, headers=headers, timeout=15)
    data = response.json()
    if "errors" in data:
        return None, None, None, None, None, None
    short_link = data["data"]["generateShortLink"]["shortLink"]

    # 2. Buscar informações do produto
    payload_product = {
        "query": f"""
            query {{
              productOfferV2(itemId:{item_id}) {{
                nodes {{
                  productName
                  priceBeforeDiscount
                  priceMin
                  priceMax
                  imageUrl
                }}
              }}
            }}
        """
    }
    payload_json_product = json.dumps(payload_product, separators=(',', ':'))
    signature_product = generate_signature(payload_json_product, timestamp)
    headers_product = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature_product}"
    }
    response2 = requests.post(API_URL, data=payload_json_product, headers=headers_product, timeout=15)
    info_data = response2.json()

    productname, price, image_url, old_price, discount_percent = "Desconhecido", None, None, None, None

    nodes = info_data.get("data", {}).get("productOfferV2", {}).get("nodes", [])
    if nodes:
        node = nodes[0]
        productname = node.get("productName", "Desconhecido")
        image_url = node.get("imageUrl")

        min_price = node.get("priceMin")
        max_price = node.get("priceMax")
        before_discount = node.get("priceBeforeDiscount")

        if min_price:
            price = float(min_price) / 100000  # Shopee retorna em centavos × 100
        if before_discount:
            old_price = float(before_discount) / 100000
        if old_price and price:
            discount_percent = round(100 - (price / old_price * 100))

    return productname, price, old_price, discount_percent, short_link, image_url

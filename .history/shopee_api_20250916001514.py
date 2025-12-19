import requests
import time
import hashlib
import re
import json

# 🔑 Seus dados da Shopee
appID = "18353340769"
secret = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"

url = "https://open-api.affiliate.shopee.com.br/graphql"

def extract_item_id(product_url):
    # Formato antigo: -i.{shopId}.{itemId}
    match = re.search(r'-i\.\d+\.(\d+)', product_url)
    if match:
        return match.group(1)
    # Formato novo: /product/{shopId}/{itemId}
    match2 = re.search(r'/product/\d+/(\d+)', product_url)
    if match2:
        return match2.group(1)
    return None

def extract_shop_id(product_url):
    # Pega shopId do link novo: /product/{shopId}/{itemId}
    match = re.search(r'/product/(\d+)/\d+', product_url)
    if match:
        return match.group(1)
    return None

def generate_signature(payload, timestamp):
    factor = f"{appID}{timestamp}{payload}{secret}"
    return hashlib.sha256(factor.encode()).hexdigest()

def fetch_product(item_id, shop_id=None):
    page = 0
    while True:
        query_dict = {
            "query": """
            query Fetch($page:Int){
              productOfferV2(listType:0, page:$page, limit:50) {
                nodes {
                  itemId
                  productName
                  priceMax
                  priceMin
                  offerLink
                }
                pageInfo {
                  hasNextPage
                }
              }
            }
            """,
            "variables": {"page": page},
            "operationName": None
        }
        payload = json.dumps(query_dict, separators=(',', ':'))
        timestamp = int(time.time())
        signature = generate_signature(payload, timestamp)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={appID},Timestamp={timestamp},Signature={signature}"
        }

        response = requests.post(url, data=payload, headers=headers)
        data = response.json()

        nodes = data.get("data", {}).get("productOfferV2", {}).get("nodes", [])
        for node in nodes:
            if str(node["itemId"]) == str(item_id):
                return node

        has_next = data.get("data", {}).get("productOfferV2", {}).get("pageInfo", {}).get("hasNextPage", False)
        if not has_next:
            break
        page += 1

    return None

def get_affiliate_link(product_url):
    item_id = extract_item_id(product_url)
    shop_id = extract_shop_id(product_url)

    if not item_id:
        print("❌ Não foi possível extrair itemId do link")
        return

    # Busca o produto
    product = fetch_product(item_id, shop_id)
    if not product:
        print("❌ Produto não encontrado")
        return

    # Monta o shortLink afiliado
    payload_dict = {
        "query": f"""
        mutation {{
            generateShortLink(input: {{ originUrl: "{product_url}", subIds: ["s1"] }}) {{
                shortLink
            }}
        }}
        """
    }
    payload_json = json.dumps(payload_dict, separators=(',', ':'))
    timestamp = int(time.time())
    signature = generate_signature(payload_json, timestamp)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={appID},Timestamp={timestamp},Signature={signature}"
    }
    response = requests.post(url, data=payload_json, headers=headers)
    data = response.json()

    short_link = data.get("data", {}).get("generateShortLink", {}).get("shortLink", "Desconhecido")
    product_name = product.get("productName", "Desconhecido")
    price_min = product.get("priceMin", "Desconhecido")
    price_max = product.get("priceMax", "Desconhecido")

    # Formata mensagem para WhatsApp
    message = f"📌 *{product_name}*\n💰 Preço: {price_min} - {price_max}\n🔗 Link afiliado: {short_link}"
    print("\n✅ Produto pronto para WhatsApp:")
    print(message)

if __name__ == "__main__":
    link = input("Cole o link do produto Shopee: ").strip()
    get_affiliate_link(link)

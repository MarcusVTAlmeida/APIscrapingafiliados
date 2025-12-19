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
    match = re.search(r'-i\.\d+\.(\d+)', product_url)
    if match:
        return match.group(1)
    match2 = re.search(r'/product/\d+/(\d+)', product_url)
    if match2:
        return match2.group(1)
    return None

def extract_shop_id(product_url):
    match = re.search(r'/product/(\d+)/\d+', product_url)
    if match:
        return match.group(1)
    return None

def generate_signature(payload, timestamp):
    factor = f"{appID}{timestamp}{payload}{secret}"
    return hashlib.sha256(factor.encode()).hexdigest()

def fetch_product(item_id):
    page = 0
    while True:
        query_dict = {
            "query": """
            query Fetch($page:Int){
              productOfferV2(listType:0, page:$page, limit:50) {
                nodes {
                  itemId
                  productName
                  priceMin
                  priceMax
                  offerLink
                  imageUrl
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
    if not item_id:
        print("❌ Não foi possível extrair itemId do link")
        return

    product = fetch_product(item_id)
    if not product:
        print("❌ Produto não encontrado")
        return

    # Gera link afiliado
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

    # Extrai dados do produto
    product_name = product.get("productName", "Desconhecido")
    price_min = product.get("priceMin", "Desconhecido")
    price_max = product.get("priceMax", "Desconhecido")
    image_url = product.get("imageUrl", "")

    # Formata mensagem para WhatsApp
    message = (
        f"🛒 *{product_name}*\n"
        f"💰 Preço: R$ {price_min} - R$ {price_max}\n"
        f"🔗 Link afiliado: {short_link}\n"
    )
    if image_url:
        message += f"🖼️ Imagem: {image_url}"

    print("\n✅ Produto pronto para WhatsApp:")
    print(message)

if __name__ == "__main__":
    link = input("Cole o link do produto Shopee: ").strip()
    get_affiliate_link(link)

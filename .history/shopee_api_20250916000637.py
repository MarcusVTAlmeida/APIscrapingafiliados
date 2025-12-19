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
    return None

def generate_signature(payload, timestamp):
    factor = f"{appID}{timestamp}{payload}{secret}"
    return hashlib.sha256(factor.encode()).hexdigest()

def get_product_info(product_url):
    item_id = extract_item_id(product_url)
    if not item_id:
        print("❌ Não foi possível extrair itemId do link")
        return

    query_dict = {
        "query": f"""
        query {{
            productOfferV2(itemId:{item_id}) {{
                nodes {{
                    itemId
                    productName
                    priceMin
                    priceMax
                    offerLink
                }}
            }}
        }}
        """
    }

    payload_json = json.dumps(query_dict, separators=(',', ':'))
    timestamp = int(time.time())
    signature = generate_signature(payload_json, timestamp)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={appID},Timestamp={timestamp},Signature={signature}"
    }

    response = requests.post(url, data=payload_json, headers=headers)
    data = response.json()

    if "errors" in data:
        print("❌ Erro ao buscar produto:", data["errors"])
        return

    nodes = data.get("data", {}).get("productOfferV2", {}).get("nodes", [])
    if not nodes:
        print("❌ Produto não encontrado")
        return

    product = nodes[0]

    # Formata mensagem pronta para WhatsApp
    message = f"""
📦 *{product.get('productName', 'Desconhecido')}*
💰 Preço: R$ {product.get('priceMin', 'Desconhecido')} - R$ {product.get('priceMax', 'Desconhecido')}
🔗 Compre aqui: {product.get('offerLink', 'Desconhecido')}

👉 Aproveite e garanta já o seu!
"""
    print(message)

if __name__ == "__main__":
    link = input("Cole o link do produto Shopee: ").strip()
    get_product_info(link)

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
    """Extrai o itemId do link da Shopee"""
    match = re.search(r'-i\.\d+\.(\d+)', product_url)
    if match:
        return match.group(1)
    return None

def generate_signature(payload, timestamp):
    """Gera a assinatura SHA256 exigida pela Shopee"""
    factor = f"{appID}{timestamp}{payload}{secret}"
    return hashlib.sha256(factor.encode()).hexdigest()

def fetch_product_info(item_id):
    """Busca o produto diretamente pelo itemId"""
    query_dict = {
        "query": f"""
        query {{
            productOfferV2(itemIds: [{item_id}]) {{
                nodes {{
                    itemId
                    productName
                    priceMin
                    priceMax
                    productLink
                    offerLink
                    imageUrl
                    commission
                    commissionRate
                }}
            }}
        }}
        """
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

    if "errors" in data:
        print("❌ Erro ao buscar produto:", data["errors"])
        return None

    nodes = data.get("data", {}).get("productOfferV2", {}).get("nodes", [])
    if not nodes:
        print("❌ Produto não encontrado")
        return None

    return nodes[0]

def display_product_info(product_url):
    item_id = extract_item_id(product_url)
    if not item_id:
        print("❌ Não foi possível extrair itemId do link")
        return

    info = fetch_product_info(item_id)
    if not info:
        return

    print("\n✅ Informações do Produto:")
    print("Nome:", info.get("productName", "Desconhecido"))
    print("Preço:", f"{info.get('priceMin', 'Desconhecido')} - {info.get('priceMax', 'Desconhecido')}")
    print("Link normal:", info.get("productLink", product_url))
    print("Link afiliado:", info.get("offerLink", "Desconhecido"))
    print("Imagem:", info.get("imageUrl", "Desconhecida"))
    print("Comissão:", info.get("commission", "Desconhecida"))
    print("Taxa de comissão:", info.get("commissionRate", "Desconhecida"))

if __name__ == "__main__":
    link = input("Cole o link do produto Shopee: ").strip()
    display_product_info(link)

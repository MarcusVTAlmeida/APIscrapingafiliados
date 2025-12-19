import requests
import time
import hashlib
import re

# 🔑 Substitua pelos seus dados
appID = "18353340769"
secret = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"

url = "https://open-api.affiliate.shopee.com.br/graphql"

def extract_ids(product_url):
    # Captura shopId e itemId do link
    match = re.search(r'-i\.(\d+)\.(\d+)', product_url)
    if match:
        shop_id, item_id = match.groups()
        return shop_id, item_id
    return None, None

def get_product(shop_id, item_id):
    query = f"""
    {{
      productOfferV2(
        listType:0,
        page:0,
        limit:1
      ) {{
        nodes {{
          itemId
          shopId
          productName
          price
          productLink
          offerLink
        }}
      }}
    }}
    """
    timestamp = int(time.time())
    signature = hashlib.sha256(f"{appID}{timestamp}{query}{secret}".encode()).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={appID},Timestamp={timestamp},Signature={signature}"
    }

    response = requests.post(url, json={"query": query}, headers=headers)
    data = response.json()

    # Filtra pelo itemId correto
    try:
        nodes = data["data"]["productOfferV2"]["nodes"]
        for node in nodes:
            if str(node["itemId"]) == str(item_id):
                return node
    except:
        print("❌ Erro ao buscar produto:", data)
    return None

if __name__ == "__main__":
    product_url = input("Cole o link do produto Shopee: ").strip()
    shop_id, item_id = extract_ids(product_url)

    if not item_id:
        print("❌ Não foi possível extrair IDs do link")
    else:
        product = get_product(shop_id, item_id)
        if product:
            print("\n✅ Informações do Produto:")
            print("Nome:", product["productName"])
            print("Preço:", product["price"])
            print("Link normal:", product["productLink"])
            print("Link afiliado:", product["offerLink"])
        else:
            print("❌ Produto não encontrado")

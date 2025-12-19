import requests
import time
import hashlib
import re
import json

# 🔑 Substitua pelos seus dados
APP_ID = "18353340769"
SECRET = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"
URL = "https://open-api.affiliate.shopee.com.br/graphql"

def extract_item_id(product_url):
    # Extrai o itemId do link do produto
    match = re.search(r'/(\d+)$', product_url)
    if match:
        return match.group(1)
    return None

def fetch_product_by_item(item_id):
    # Query GraphQL
    query = """
    {
      productOfferV2(
        listType: 0,
        sortType: 2,
        page: 0,
        limit: 50
      ) {
        nodes {
          itemId
          productName
          price
          productLink
          offerLink
        }
      }
    }
    """

    payload = json.dumps({"query": query}, separators=(',', ':'))
    timestamp = str(int(time.time()))
    factor = f"{APP_ID}{timestamp}{payload}{SECRET}"
    signature = hashlib.sha256(factor.encode()).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature}"
    }

    response = requests.post(URL, headers=headers, data=payload)

    try:
        nodes = response.json()["data"]["productOfferV2"]["nodes"]
        # procura pelo itemId específico
        for product in nodes:
            if str(product["itemId"]) == str(item_id):
                return product
        print("❌ Produto não encontrado na primeira página")
        return None
    except Exception as e:
        print("❌ Erro ao buscar produto:", e)
        print("📦 Resposta completa:", response.json())
        return None

# 🚀 Teste
if __name__ == "__main__":
    link_produto = input("Cole o link do produto Shopee: ").strip()
    item_id = extract_item_id(link_produto)
    if not item_id:
        print("❌ Não foi possível extrair itemId do link")
    else:
        produto = fetch_product_by_item(item_id)
        if produto:
            print("\n✅ Produto encontrado:")
            print("Nome:", produto["productName"])
            print("Preço:", produto["price"])
            print("Link normal:", produto["productLink"])
            print("Link afiliado:", produto["offerLink"])

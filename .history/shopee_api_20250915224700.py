import requests
import time
import hashlib
import re

# 🔑 Substitua pelos seus dados
appID = "18353340769"
secret = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"

url = "https://open-api.affiliate.shopee.com.br/graphql"

def extract_item_id(product_url):
    """
    Extrai o itemId de links da Shopee:
    Formatos comuns:
    - https://shopee.com.br/Nome-do-produto-i.shopId.itemId
    - https://shopee.com.br/product/shopId/itemId
    """
    match = re.search(r'-i\.\d+\.(\d+)', product_url)
    if match:
        return match.group(1)
    match = re.search(r'/product/\d+/(\d+)', product_url)
    if match:
        return match.group(1)
    return None

def fetch_product_info(item_id):
    # Corpo da query GraphQL
    payload = f"""
    {{
      "query": "query Fetch{{ productOfferV2(listType:0, sortType:2, itemIds:[{item_id}]){{ nodes {{ productName price productLink offerLink }} }} }}",
      "operationName": null,
      "variables":{{}}
    }}
    """
    
    payload = payload.replace('\n','')
    timestamp = int(time.time())
    factor = f"{appID}{timestamp}{payload}{secret}"
    signature = hashlib.sha256(factor.encode()).hexdigest()

    headers = {
        "Content-type": "application/json",
        "Authorization": f"SHA256 Credential={appID},Timestamp={timestamp},Signature={signature}"
    }

    response = requests.post(url, data=payload, headers=headers)
    
    try:
        node = response.json()["data"]["productOfferV2"]["nodes"][0]
        return node
    except Exception as e:
        print("❌ Não foi possível obter o produto:", e)
        print("📦 Resposta completa:", response.json())
        return None

# 🚀 Execução
if __name__ == "__main__":
    product_url = input("Cole o link do produto Shopee: ").strip()
    item_id = extract_item_id(product_url)
    
    if not item_id:
        print("❌ Não foi possível extrair itemId do link")
    else:
        info = fetch_product_info(item_id)
        if info:
            print("\n✅ Informações do Produto:")
            print("Nome:", info["productName"])
            print("Preço:", info["price"])
            print("Link normal:", info["productLink"])
            print("Link afiliado:", info["offerLink"])

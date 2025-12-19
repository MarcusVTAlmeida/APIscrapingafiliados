import requests
import time
import hashlib
import re

# 🔑 Substitua pelos seus dados
appID = "18353340769"
secret = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"

url = "https://open-api.affiliate.shopee.com.br/graphql"

def extract_item_id(product_url):
    match = re.search(r'-i\.\d+\.(\d+)', product_url)
    if match:
        return match.group(1)
    match = re.search(r'/product/\d+/(\d+)', product_url)
    if match:
        return match.group(1)
    return None

def fetch_offers(page=0):
    payload = """
    {
      "query": "query Fetch($page:Int){ productOfferV2(listType:0, sortType:2, page:$page, limit:50) { nodes { itemId productName price productLink offerLink } pageInfo { hasNextPage } } }",
      "variables":{"page":0},
      "operationName": null
    }
    """
    payload = payload.replace('\n','').replace(':0', f':{page}')
    timestamp = int(time.time())
    factor = f"{appID}{timestamp}{payload}{secret}"
    signature = hashlib.sha256(factor.encode()).hexdigest()

    headers = {
        "Content-type": "application/json",
        "Authorization": f"SHA256 Credential={appID},Timestamp={timestamp},Signature={signature}"
    }

    response = requests.post(url, data=payload, headers=headers)
    return response.json()

def find_product_by_id(item_id):
    page = 0
    while True:
        data = fetch_offers(page)
        try:
            nodes = data["data"]["productOfferV2"]["nodes"]
        except:
            print("❌ Erro ao buscar produtos:", data)
            return None
        for node in nodes:
            if str(node["itemId"]) == str(item_id):
                return node
        if not data["data"]["productOfferV2"]["pageInfo"]["hasNextPage"]:
            break
        page += 1
    return None

# 🚀 Execução
if __name__ == "__main__":
    product_url = input("Cole o link do produto Shopee: ").strip()
    item_id = extract_item_id(product_url)
    
    if not item_id:
        print("❌ Não foi possível extrair itemId do link")
    else:
        info = find_product_by_id(item_id)
        if info:
            print("\n✅ Informações do Produto:")
            print("Nome:", info["productName"])
            print("Preço:", info["price"])
            print("Link normal:", info["productLink"])
            print("Link afiliado:", info["offerLink"])
        else:
            print("❌ Produto não encontrado na lista de ofertas")

import requests
import time
import hashlib
import json

# 🔑 Substitua pelos seus dados
APP_ID = "18353340769"
SECRET = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"
URL = "https://open-api.affiliate.shopee.com.br/graphql"

def fetch_offers(page=0):
    # Query GraphQL
    query = """
    {
      productOfferV2(
        listType: 0,
        sortType: 2,
        page: %d,
        limit: 20
      ) {
        nodes {
          productName
          price
          productLink
          offerLink
        }
        pageInfo {
          page
          limit
          hasNextPage
        }
      }
    }
    """ % page

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
        data = response.json()["data"]["productOfferV2"]["nodes"]
        return data
    except Exception as e:
        print("❌ Erro ao pegar nodes:", e)
        print("📦 Resposta completa:", response.json())
        return None

# 🚀 Teste
if __name__ == "__main__":
    offers = fetch_offers(0)
    if offers:
        for item in offers[:5]:  # mostrar só os 5 primeiros
            print("\n✅ Produto:")
            print("Nome:", item["productName"])
            print("Preço:", item["price"])
            print("Link normal:", item["productLink"])
            print("Link afiliado:", item["offerLink"])

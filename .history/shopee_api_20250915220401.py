import requests
import time
import hashlib

# 🔑 Substitua pelos seus dados

appID = "18353340769"
secret = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"

# Endpoint oficial da Shopee Afiliados
url = "https://open-api.affiliate.shopee.com.br/graphql"


    # Corpo da query em GraphQL
     payload = """
  {
  "query": "query Fetch($page:Int){
    productOfferV2(
      listType: 0, 
      sortType: 2,
      page: $page,
      limit: 50
    ) {
      nodes {
        commissionRate
        commission
        price
        productLink
        offerLink
      }
    }
  }",
  "operationName": null,
  "variables":{
    "page":0
    } 
  }
  """
    # Gera assinatura obrigatória
    payload = payload.replace('\n','').replace(':0',f':{page}')
    timestamp = int(time.time())
    factor = f"{appID}{timestamp}{payload}{secret}"
    signature = hashlib.sha256(str(factor).encode()).hexdigest()

    headers = {
        "Content-type": "application/json",
        "Authorization": f"SHA256 Credential={appID},Timestamp={timestamp},Signature={signature}"
    }

    # Faz a requisição
    response = requests.post(url, json=payload, headers=headers)
    
    # Exibe resultado cru (debug)
    print("📦 Resposta completa:", response.json())
    
    try:
        return response.json()["data"]["productOfferV2"]["nodes"]
    except Exception as e:
        print("❌ Erro ao pegar nodes:", e)
        return None

# 🚀 Teste
if __name__ == "__main__":
    offers = fetch_offers(0)
    if offers:
        for item in offers[:3]:  # mostra só 3 primeiros
            print("\n✅ Produto:")
            print("Preço:", item["price"])
            print("Link normal:", item["productLink"])
            print("Link afiliado:", item["offerLink"])

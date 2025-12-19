import requests
import time
import hashlib

# 🔑 Substitua pelos seus dados

APP_ID = "18353340769"
SECRET = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"

# Endpoint oficial da Shopee Afiliados
url = "https://open-api.affiliate.shopee.com.br/graphql"

def fetch_offers(page=0):
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
  payload = payload.replace('\n','').replace(':0',f':{page}')
  timestamp = int(time.time())
  factor = appID+str(timestamp)+payload+secret
  signature = hashlib.sha256(factor.encode()).hexdigest()

  # Set the request headers
  headers = {
      'Content-type':'application/json',
      'Authorization':f'SHA256 Credential={appID},Timestamp={timestamp},Signature={signature}'
  }

  # Send the POST request
  response = requests.post(url,payload,headers=headers)

  data = response.json()
  return data['data']['productOfferV2']['nodes']

# 🚀 Teste
if __name__ == "__main__":
    offers = fetch_offers(0)
    if offers:
        for item in offers[:3]:  # mostra só 3 primeiros
            print("\n✅ Produto:")
            print("Preço:", item["price"])
            print("Link normal:", item["productLink"])
            print("Link afiliado:", item["offerLink"])

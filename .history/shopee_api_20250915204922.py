import requests
import time
import hmac
import hashlib
import json

APP_ID = "8353340769"
SECRET = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"

url = "https://open-api.affiliate.shopee.com.br/graphql"  # use .br para Brasil
path = "/graphql"

# GraphQL query (exemplo de busca de ofertas)
body = """
{
  productOfferV2(
    listType:0
    sortType:5
  ) {
    nodes {
      commissionRate
      commission
      price
      productLink
      offerLink
    }
  }
}
"""

payload = {"query": body}
body_str = json.dumps(payload, separators=(',', ':'))  # importante: sem espaços

timestamp = str(int(time.time()))

# Monta a string que será assinada
to_sign = APP_ID + path + timestamp + body_str

# Gera a assinatura HMAC-SHA256
signature = hmac.new(SECRET.encode(), to_sign.encode(), hashlib.sha256).hexdigest()

# Headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature}"
}

# Requisição
response = requests.post(url, headers=headers, data=body_str)

print("📦 Resposta:", response.json())

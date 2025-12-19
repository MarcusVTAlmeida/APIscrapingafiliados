import requests
import time
import hashlib
import json

# 🔑 Substitua pelos seus dados
APP_ID = "18353340769"
SECRET = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"
URL = "https://open-api.affiliate.shopee.com.br/graphql"

def generate_shortlink(product_url, subIds=None):
    if subIds is None:
        subIds = ["s1","s2","s3","s4","s5"]

    timestamp = str(int(time.time()))

    # Mutation compacta
    mutation_str = (
        'mutation{generateShortLink('
        'input:{originUrl:"' + product_url + '",'
        'subIds:' + json.dumps(subIds) + '}){shortLink}}'
    )

    payload = {"query": mutation_str}

    # Assinatura SHA256
    factor = f"{APP_ID}{timestamp}{json.dumps(payload, separators=(',', ':'))}{SECRET}"
    signature = hashlib.sha256(factor.encode()).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature}"
    }

    response = requests.post(URL, headers=headers, json=payload)

    try:
        return response.json()["data"]["generateShortLink"]["shortLink"]
    except Exception as e:
        print("❌ Erro ao gerar shortLink:", e)
        print("📦 Resposta completa:", response.json())
        return None

# 🚀 Programa principal
if __name__ == "__main__":
    url_produto = input("Coloque o link do produto Shopee: ").strip()
    shortlink = generate_shortlink(url_produto)
    if shortlink:
        print("\n✅ ShortLink de afiliado gerado:")
        print(shortlink)

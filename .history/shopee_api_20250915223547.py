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

    # Mutation Shopee: gerar shortLink e pegar info do produto
    mutation_str = (
        f'mutation{{generateShortLink(input:{{originUrl:"{product_url}",subIds:{json.dumps(subIds)}}}){{shortLink productName}}}}'
    )

    payload = {"query": mutation_str}
    payload_json = json.dumps(payload, separators=(',', ':'))

    factor = f"{APP_ID}{timestamp}{payload_json}{SECRET}"
    signature = hashlib.sha256(factor.encode()).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature}"
    }

    response = requests.post(URL, headers=headers, data=payload_json)

    try:
        data = response.json()["data"]["generateShortLink"]
        return data["shortLink"], data.get("productName", "Nome não disponível")
    except Exception as e:
        print("❌ Erro ao gerar shortLink:", e)
        print("📦 Resposta completa:", response.json())
        return None, None

# 🚀 Programa principal
if __name__ == "__main__":
    url_produto = input("Coloque o link do produto Shopee: ").strip()
    shortlink, nome_produto = generate_shortlink(url_produto)
    if shortlink:
        print("\n✅ Produto:", nome_produto)
        print("✅ ShortLink de afiliado gerado:", shortlink)

import requests
import time
import hashlib
import json

# 🔑 Substitua pelos seus dados
appID = "18353340769"
secret = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"

# Endpoint oficial da Shopee Afiliados
url = "https://open-api.affiliate.shopee.com.br/graphql"

def generate_shortlink(product_url, subIds=None):
    if subIds is None:
        subIds = ["s1","s2","s3","s4","s5"]  # você pode personalizar

    # GraphQL mutation
    payload = {
        "query": f"""
           mutation = (
    'mutation{generateShortLink('
    'input:{'
    f'originUrl:"{product_url}",'
    f'subIds:{json.dumps(subIds)}'
    '}){shortLink}}'
)
    payload = {"query": mutation}}
        """,
        "operationName": "generateShortLink"
    }

    # Cria assinatura
    timestamp = int(time.time())
    factor = f"{appID}{timestamp}{json.dumps(payload, separators=(',', ':'))}{secret}"
    signature = hashlib.sha256(factor.encode()).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={appID},Timestamp={timestamp},Signature={signature}"
    }

    # Requisição POST
    response = requests.post(url, headers=headers, json=payload)
    
    try:
        data = response.json()
        short_link = data["data"]["generateShortLink"]["shortLink"]
        return short_link
    except Exception as e:
        print("❌ Erro ao gerar shortLink:", e)
        print("📦 Resposta completa:", response.json())
        return None

# 🚀 Teste
if __name__ == "__main__":
    url_produto = "https://shopee.com.br/Cabo-de-Dados-Conexão-USB-Lightning-Carregamento-Rápido-25W-de-1-Metro-Kapbom-KAP-318-5G-i.1323149422.22594410588"
    shortlink = generate_shortlink(url_produto)
    if shortlink:
        print("\n✅ ShortLink de afiliado gerado:")
        print(shortlink)

import requests
import time
import hashlib
import json
import re

# 🔑 Substitua pelos seus dados
APP_ID = "18353340769"
SECRET = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"
URL = "https://open-api.affiliate.shopee.com.br/graphql"

def is_valid_shopee_url(url):
    """
    Valida se o link é de um produto da Shopee (formato correto: ...i.NUMERO.NUMERO)
    """
    pattern = r"https://shopee\.com\.br/.+\.i\.\d+\.\d+"
    return re.match(pattern, url) is not None

def generate_shortlink(product_url, subIds=None):
    if subIds is None:
        subIds = ["s1","s2","s3","s4","s5"]

    if not is_valid_shopee_url(product_url):
        print("❌ Link inválido! Use um link direto de produto da Shopee (terminando com .i.NUMERO.NUMERO)")
        return None

    timestamp = str(int(time.time()))

    # Mutation compacta, exatamente como a Shopee espera
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

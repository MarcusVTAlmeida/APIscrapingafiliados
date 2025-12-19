import requests
import time
import hashlib
import re
import json

# 🔑 Seus dados da Shopee
appID = "18353340769"
secret = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"

url = "https://open-api.affiliate.shopee.com.br/graphql"

def extract_item_id(product_url):
    match = re.search(r'-i\.\d+\.(\d+)', product_url)
    if match:
        return match.group(1)
    return None

def generate_signature(payload, timestamp):
    factor = f"{appID}{timestamp}{payload}{secret}"
    return hashlib.sha256(factor.encode()).hexdigest()

def get_affiliate_link(product_url):
    item_id = extract_item_id(product_url)
    if not item_id:
        print("❌ Não foi possível extrair itemId do link")
        return

    # Monta o payload JSON da mutation
    payload_dict = {
        "query": f"""
        mutation {{
            generateShortLink(input: {{ originUrl: "{product_url}", subIds: ["s1"] }}) {{
                shortLink
            }}
        }}
        """
    }
    payload_json = json.dumps(payload_dict, separators=(',', ':'))  # importante manter sem espaços extras
    timestamp = int(time.time())
    signature = generate_signature(payload_json, timestamp)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={appID},Timestamp={timestamp},Signature={signature}"
    }

    response = requests.post(url, data=payload_json, headers=headers)
    data = response.json()

    if "errors" in data:
        print("❌ Erro ao gerar shortLink:", data["errors"])
        return

    short_link = data["data"]["generateShortLink"]["shortLink"]

    # Retorna as informações básicas (nome e preço podemos pegar de productOfferV2)
    # Aqui pegamos rapidamente o preço e nome usando o mesmo itemId
    query_dict = {
        "query": f"""
        query {{
            productOfferV2(listType:0, page:0, limit:50) {{
                nodes {{
                    itemId
                    productName
                    price
                    productLink
                }}
            }}
        }}
        """
    }
    payload_query = json.dumps(query_dict, separators=(',', ':'))
    signature_query = generate_signature(payload_query, timestamp)
    headers_query = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={appID},Timestamp={timestamp},Signature={signature_query}"
    }
    response2 = requests.post(url, data=payload_query, headers=headers_query)
    info_data = response2.json()

    product_name = "Desconhecido"
    price = "Desconhecido"
    for node in info_data.get("data", {}).get("productOfferV2", {}).get("nodes", []):
        if str(node["itemId"]) == item_id:
            productname = node["productName"]
            price = node["price"]
            break

    print("\n✅ Informações do Produto:")
    print("Nome:", productname)
    print("Preço:", price)
    print("Link normal:", product_url)
    print("Link afiliado:", short_link)


if __name__ == "__main__":
    link = input("Cole o link do produto Shopee: ").strip()
    get_affiliate_link(link)

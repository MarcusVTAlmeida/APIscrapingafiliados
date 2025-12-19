import requests
import time
import hashlib
import re

# 🔑 Substitua pelos seus dados
appID = "18353340769"
secret = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"

url = "https://open-api.affiliate.shopee.com.br/graphql"

def extract_ids(product_url):
    """
    Extrai shopId e itemId do link do produto
    Exemplo de link:
    https://shopee.com.br/Produto-Nome-i.1323149422.22594410588
    """
    match = re.search(r'-i\.(\d+)\.(\d+)', product_url)
    if match:
        shop_id = match.group(1)
        item_id = match.group(2)
        return shop_id, item_id
    return None, None

def generate_affiliate_link(shop_id, item_id):
    """
    Gera link afiliado e retorna informações do produto
    """
    payload = {
        "query": f"""
        mutation {{
            generateShortLink(
                input: {{
                    originUrl: "https://shopee.com.br/product/{shop_id}/{item_id}",
                    subIds: ["s1","s2","s3"]
                }}
            ) {{
                shortLink
            }}
        }}
        """
    }
    payload_str = str(payload).replace("'", '"')
    timestamp = int(time.time())
    factor = f"{appID}{timestamp}{payload_str}{secret}"
    signature = hashlib.sha256(factor.encode()).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={appID},Timestamp={timestamp},Signature={signature}"
    }

    response = requests.post(url, data=payload_str, headers=headers)
    data = response.json()
    
    if "errors" in data:
        print("❌ Erro ao gerar link afiliado:", data)
        return None
    short_link = data["data"]["generateShortLink"]["shortLink"]
    return short_link

# 🚀 Execução
if __name__ == "__main__":
    product_url = input("Cole o link do produto Shopee: ").strip()
    shop_id, item_id = extract_ids(product_url)

    if not item_id or not shop_id:
        print("❌ Não foi possível extrair shopId/itemId do link")
    else:
        affiliate_link = generate_affiliate_link(shop_id, item_id)
        if affiliate_link:
            print("\n✅ Informações do Produto:")
            print("Nome: Desconhecido")  # Aqui você pode usar outra query para pegar o nome
            print("Preço: Desconhecido") # ou integrar com productOfferV2 usando shopId + itemId
            print("Link normal:", f"https://shopee.com.br/product/{shop_id}/{item_id}")
            print("Link afiliado:", affiliate_link)

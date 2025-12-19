import requests
import re
import time
import hashlib

# 🔑 Substitua pelos seus dados de afiliado
appID = "18353340769"
secret = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"

def extract_item_id(product_url):
    """Extrai itemId do link Shopee"""
    match = re.search(r'-i\.\d+\.(\d+)', product_url)
    if match:
        return match.group(1)
    match = re.search(r'/product/\d+/(\d+)', product_url)
    if match:
        return match.group(1)
    return None

def generate_affiliate_link(product_url):
    """Gera link afiliado via API Shopee"""
    timestamp = int(time.time())
    payload = f'{{"query":"mutation{{generateShortLink(input:{{originUrl:\\"{product_url}\\",subIds:[\\"s1\\"]}}){{shortLink}}}}"}}'
    signature_raw = f"{appID}{timestamp}{payload}{secret}"
    signature = hashlib.sha256(signature_raw.encode()).hexdigest()

    headers = {
        "Content-type": "application/json",
        "Authorization": f"SHA256 Credential={appID},Timestamp={timestamp},Signature={signature}"
    }

    response = requests.post("https://open-api.affiliate.shopee.com.br/graphql", data=payload, headers=headers)
    data = response.json()
    try:
        return data["data"]["generateShortLink"]["shortLink"]
    except:
        return None

def fetch_product_info(item_id):
    """Busca nome e preço usando API pública Shopee"""
    url = f"https://shopee.com.br/api/v4/item/get?itemid={item_id}&shopid=0"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    data = response.json().get("data", {})
    name = data.get("name", "Desconhecido")
    price = data.get("price", 0) / 100000  # a API retorna preço em centavos multiplicado por 1000
    return {"name": name, "price": price}

# 🚀 Execução
if __name__ == "__main__":
    product_url = input("Cole o link do produto Shopee: ").strip()
    item_id = extract_item_id(product_url)
    
    if not item_id:
        print("❌ Não foi possível extrair itemId do link")
    else:
        info = fetch_product_info(item_id)
        affiliate_link = generate_affiliate_link(product_url)
        
        print("\n✅ Informações do Produto:")
        print("Nome:", info["name"] if info else "Desconhecido")
        print("Preço:", info["price"] if info else "Desconhecido")
        print("Link normal:", product_url)
        print("Link afiliado:", affiliate_link if affiliate_link else "Erro ao gerar link afiliado")

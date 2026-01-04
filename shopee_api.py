import re, time, json, hashlib, requests

APP_ID = "18353340769"
SECRET = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"
API_URL = "https://open-api.affiliate.shopee.com.br/graphql"

def extract_item_id(product_url):
    match = re.search(r'-i\.\d+\.(\d+)', product_url)
    if match: 
        return match.group(1)
    match = re.search(r'/product/\d+/(\d+)', product_url)
    if match: 
        return match.group(1)
    return None

def generate_signature(payload, timestamp):
    factor = f"{APP_ID}{timestamp}{payload}{SECRET}"
    return hashlib.sha256(factor.encode()).hexdigest()

def get_shopee_product_info(product_url):
    item_id = extract_item_id(product_url)
    if not item_id:
        return {
            "title": None,
            "price": None,
            "original_value": None,
            "caption": "❌ Não foi possível identificar o produto.",
            "image": None,
            "url": product_url,
        }

    timestamp = int(time.time())

    # Gerar link afiliado encurtado
    payload_shortlink = {
        "query": f"""mutation {{ generateShortLink(input: {{ originUrl: "{product_url}", subIds: ["s1"] }}) {{ shortLink }} }}"""
    }
    payload_json = json.dumps(payload_shortlink, separators=(",", ":"))
    signature = generate_signature(payload_json, timestamp)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature}",
    }

    response = requests.post(API_URL, data=payload_json, headers=headers, timeout=15)
    data = response.json()

    short_link = data.get("data", {}).get("generateShortLink", {}).get("shortLink")

    if not short_link or "errors" in data:
        return {
            "title": None,
            "price": None,
            "original_value": None,
            "caption": "❌ Erro ao gerar link afiliado.",
            "image": None,
            "url": product_url,
        }

    # Buscar informações do produto
    payload_product = {
        "query": f"""query {{ productOfferV2(itemId:{item_id}) {{
            nodes {{ productName priceMin priceMax imageUrl }}
        }} }}"""
    }
    payload_json_product = json.dumps(payload_product, separators=(",", ":"))
    signature_product = generate_signature(payload_json_product, timestamp)
    headers_product = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature_product}",
    }

    response2 = requests.post(API_URL, data=payload_json_product, headers=headers_product, timeout=15)
    info_data = response2.json()

    productname = "Desconhecido"
    price_text = "Preço indisponível"
    image_url = None
    original_value = None

    nodes = info_data.get("data", {}).get("productOfferV2", {}).get("nodes", [])
    if nodes:
        node = nodes[0]
        productname = node.get("productName", "Desconhecido")
        min_price = node.get("priceMin")
        max_price = node.get("priceMax")
        image_url = node.get("imageUrl")

        # Formatar preços
        if min_price and max_price:
            # Converte string para float e formata como R$ X.XXX,YY
            if min_price == max_price:
                price_text = f"R$ {float(min_price):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                original_value = f"R$ {float(max_price):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                price_text = f"R$ {float(min_price):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Monta caption no padrão dos outros
    if original_value and price_text != "Preço indisponível":
        caption = f"📦 {productname}\n💰 De {original_value} por {price_text}\n🔗 {short_link}"
    else:
        caption = f"📦 {productname}\n💰 {price_text}\n🔗 {short_link}"

    return {
        "title": productname,
        "price": price_text,
        "original_value": original_value,
        "caption": caption,
        "image": image_url,
        "url": short_link,
    }

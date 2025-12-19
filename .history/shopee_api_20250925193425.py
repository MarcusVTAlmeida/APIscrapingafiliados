import re, time, json, hashlib, requests

APP_ID = "18353340769"
SECRET = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"
API_URL = "https://open-api.affiliate.shopee.com.br/graphql"

def extract_item_id(product_url):
    match = re.search(r'-i\.\d+\.(\d+)', product_url)
    if match: return match.group(1)
    match = re.search(r'/product/\d+/(\d+)', product_url)
    if match: return match.group(1)
    return None

def generate_signature(payload, timestamp):
    factor = f"{APP_ID}{timestamp}{payload}{SECRET}"
    return hashlib.sha256(factor.encode()).hexdigest()

def get_shopee_product_info(product_url):
    item_id = extract_item_id(product_url)
    if not item_id: return None, None, None, None, None, None
    timestamp = int(time.time())

    # Gerar link afiliado
    payload_shortlink = {
        "query": f"""mutation {{ generateShortLink(input: {{ originUrl: "{product_url}", subIds: ["s1"] }}) {{ shortLink }} }}"""
    }
    payload_json = json.dumps(payload_shortlink, separators=(',', ':'))
    signature = generate_signature(payload_json, timestamp)
    headers = {"Content-Type": "application/json",
               "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature}"}
    response = requests.post(API_URL, data=payload_json, headers=headers, timeout=15)
    data = response.json()
    if "errors" in data: return None, None, None, None, None, None
    short_link = data["data"]["generateShortLink"]["shortLink"]

    # Buscar infos básicas via API de afiliados
    payload_product = {"query": f"""query {{ productOfferV2(itemId:{item_id}) {{ nodes {{ productName priceMin priceMax imageUrl }} }} }}"""}
    payload_json_product = json.dumps(payload_product, separators=(',', ':'))
    signature_product = generate_signature(payload_json_product, timestamp)
    headers_product = {"Content-Type": "application/json",
                       "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature_product}"}
    response2 = requests.post(API_URL, data=payload_json_product, headers=headers_product, timeout=15)
    info_data = response2.json()

    productname = "Desconhecido"
    price = "Desconhecido"
    image_url = None
    nodes = info_data.get("data", {}).get("productOfferV2", {}).get("nodes", [])
    if nodes:
        node = nodes[0]
        productname = node.get("productName", "Desconhecido")
        min_price = node.get("priceMin")
        max_price = node.get("priceMax")
        image_url = node.get("imageUrl")
        if min_price and max_price:
            price = f"R$ {min_price} - R$ {max_price}"

    # 🔹 Complemento: scraping para preço cheio e desconto
    html = requests.get(product_url, headers={"User-Agent": "Mozilla/5.0"}).text
    match = re.search(r"window\.__INITIAL_STATE__=(\{.*?\});", html)
    original_price = None
    discount = None
    if match:
        try:
            data_json = json.loads(match.group(1))
            item_data = data_json.get("itemCard", {}).get("itemData", {}).get("item", {})
            if "price_before_discount" in item_data:
                original_price = item_data["price_before_discount"] / 100000
            if "raw_discount" in item_data:
                discount = item_data["raw_discount"]
        except:
            pass

    return productname, price, short_link, image_url, original_price, discount

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


# 🔎 NOVO — captura preço antigo e atual via HTML (fallback)
def get_shopee_prices_from_html(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None, None

        html = response.text

        # 🔍 Pega o bloco inteiro que contém preços
        block_match = re.search(
            r'<div class="jRlVo0".*?</div>\s*</div>',
            html,
            re.DOTALL
        )

        if not block_match:
            return None, None

        block = block_match.group(0)

        # Preço atual
        current_match = re.search(
            r'<div class="IZPeQz[^"]*">\s*(R\$[\d.,]+)\s*</div>',
            block
        )

        # Preço antigo
        original_match = re.search(
            r'<div class="ZA5sW5[^"]*">\s*(R\$[\d.,]+)\s*</div>',
            block
        )

        current_price = current_match.group(1) if current_match else None
        original_price = original_match.group(1) if original_match else None

        return current_price, original_price

    except Exception:
        return None, None


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

    # 🔗 Gerar link afiliado
    payload_shortlink = {
        "query": f"""mutation {{
            generateShortLink(input: {{
                originUrl: "{product_url}",
                subIds: ["s1"]
            }}) {{
                shortLink
            }}
        }}"""
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

    # 📦 Buscar dados do produto
    payload_product = {
        "query": f"""query {{
            productOfferV2(itemId:{item_id}) {{
                nodes {{
                    productName
                    priceMin
                    priceMax
                    imageUrl
                }}
            }}
        }}"""
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

        if min_price and max_price:
            if min_price == max_price:
                price_text = f"R$ {float(min_price):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                original_value = f"R$ {float(max_price):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                price_text = f"R$ {float(min_price):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # 🔁 Fallback HTML (NOVO)
    html_price, html_original = get_shopee_prices_from_html(product_url)

    if html_price:
        price_text = html_price
    if html_original:
        original_value = html_original

    # 📝 Caption final
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

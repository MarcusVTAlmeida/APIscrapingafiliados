import re
import time
import hashlib
import json
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# 🔑 Coloque aqui o token do seu bot
TELEGRAM_TOKEN = "SEU_TOKEN_AQUI"

# 🔑 Dados do Shopee Affiliate
APP_ID = "18353340769"
SECRET = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"
API_URL = "https://open-api.affiliate.shopee.com.br/graphql"

# Função para extrair itemId do link
def extract_item_id(product_url):
    match = re.search(r'-i\.\d+\.(\d+)', product_url)
    if match:
        return match.group(1)
    match = re.search(r'/product/\d+/(\d+)', product_url)
    if match:
        return match.group(1)
    return None

# Função para gerar assinatura da Shopee
def generate_signature(payload, timestamp):
    factor = f"{APP_ID}{timestamp}{payload}{SECRET}"
    return hashlib.sha256(factor.encode()).hexdigest()

# Função para buscar informações do produto
def get_product_info(product_url):
    item_id = extract_item_id(product_url)
    if not item_id:
        return None, None, None

    timestamp = int(time.time())

    # 1️⃣ Gerar link afiliado
    payload_shortlink = {
        "query": f"""
        mutation {{
            generateShortLink(input: {{ originUrl: "{product_url}", subIds: ["s1"] }}) {{
                shortLink
            }}
        }}
        """
    }
    payload_json = json.dumps(payload_shortlink, separators=(',', ':'))
    signature = generate_signature(payload_json, timestamp)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature}"
    }
    response = requests.post(API_URL, data=payload_json, headers=headers)
    data = response.json()
    if "errors" in data:
        return None, None, None
    short_link = data["data"]["generateShortLink"]["shortLink"]

    # 2️⃣ Buscar informações do produto usando itemId
    payload_product = {
        "query": f"""
        query {{
            productOfferV2(itemId:{item_id}) {{
                nodes {{
                    productName
                    priceMin
                    priceMax
                }}
            }}
        }}
        """
    }
    payload_json_product = json.dumps(payload_product, separators=(',', ':'))
    signature_product = generate_signature(payload_json_product, timestamp)
    headers_product = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature_product}"
    }
    response2 = requests.post(API_URL, data=payload_json_product, headers=headers_product)
    info_data = response2.json()

    productname = "Desconhecido"
    price = "Desconhecido"
    nodes = info_data.get("data", {}).get("productOfferV2", {}).get("nodes", [])
    if nodes:
        node = nodes[0]
        productname = node.get("productName", "Desconhecido")
        min_price = node.get("priceMin")
        max_price = node.get("priceMax")
        if min_price and max_price:
            price = f"R$ {min_price} - R$ {max_price}"

    return productname, price, short_link

# Função que responde às mensagens
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "shopee.com.br" in text:
        productname, price, affiliate_link = get_product_info(text)
        if affiliate_link:
            message = f"📦 *{productname}*\n💰 Preço: {price}\n🔗 Link afiliado: {affiliate_link}"
        else:
            message = "❌ Não foi possível processar o link da Shopee."
        await update.message.reply_text(message, parse_mode='Markdown')

# Configura o bot
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

print("🤖 Bot iniciado...")
app.run_polling()

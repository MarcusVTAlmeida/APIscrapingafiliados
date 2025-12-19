import re
import time
import hashlib
import json
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# 🔑 Coloque aqui o token do seu bot
TELEGRAM_TOKEN = "7835836746:AAGh264mO96_f7nvkkm2N365fhjk979hydU"

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

    # Monta payload para gerar link afiliado
    payload_dict = {
        "query": f"""
        mutation {{
            generateShortLink(input: {{ originUrl: "{product_url}", subIds: ["s1"] }}) {{
                shortLink
            }}
        }}
        """
    }
    payload_json = json.dumps(payload_dict, separators=(',', ':'))
    timestamp = int(time.time())
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

    # Buscar nome e preço do produto (pode não ser 100% preciso)
    query_dict = {
        "query": f"""
        query {{
            productOfferV2(listType:0,page:0,limit:50) {{
                nodes {{
                    itemId
                    productName
                    priceMin
                    priceMax
                }}
            }}
        }}
        """
    }
    payload_query = json.dumps(query_dict, separators=(',', ':'))
    signature_query = generate_signature(payload_query, timestamp)
    headers_query = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature_query}"
    }
    response2 = requests.post(API_URL, data=payload_query, headers=headers_query)
    info_data = response2.json()

    productname = "Desconhecido"
    price = "Desconhecido"
    for node in info_data.get("data", {}).get("productOfferV2", {}).get("nodes", []):
        if str(node["itemId"]) == item_id:
            productname = node.get("productName", "Desconhecido")
            min_price = node.get("priceMin")
            max_price = node.get("priceMax")
            if min_price and max_price:
                price = f"R$ {min_price} - R$ {max_price}"
            break

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

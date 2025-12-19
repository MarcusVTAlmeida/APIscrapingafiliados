import re
import requests
import json
import time
import hashlib
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# ==========================
# CONFIGURAÇÃO DO TELEGRAM
# ==========================
TELEGRAM_TOKEN = "7835836746:AAGh264mO96_f7nvkkm2N365fhjk979hydU
"

# ==========================
# CONFIGURAÇÃO SHOPEE
# ==========================
APP_ID = "18353340769"
SECRET = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"
API_URL = "https://open-api.affiliate.shopee.com.br/graphql"

# ==========================
# FUNÇÕES SHOPEE
# ==========================
def extract_item_id(url):
    match = re.search(r'/product/\d+/(\d+)', url)
    if match:
        return match.group(1)
    match = re.search(r'-i\.\d+\.(\d+)', url)
    if match:
        return match.group(1)
    return None

def generate_signature(payload, timestamp):
    factor = f"{APP_ID}{timestamp}{payload}{SECRET}"
    return hashlib.sha256(factor.encode()).hexdigest()

def get_affiliate_info(product_url):
    item_id = extract_item_id(product_url)
    if not item_id:
        return None

    # Gerar link afiliado
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
        return None
    short_link = data["data"]["generateShortLink"]["shortLink"]

    # Consultar nome e preço usando productOfferV2 (primeira página)
    query_dict = {
        "query": """
        query {
            productOfferV2(listType:0,page:0,limit:50){
                nodes{
                    itemId
                    productName
                    priceMax
                    priceMin
                }
            }
        }
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

    product_name = "Desconhecido"
    price = "Desconhecido"
    for node in info_data.get("data", {}).get("productOfferV2", {}).get("nodes", []):
        if str(node["itemId"]) == item_id:
            product_name = node["productName"]
            price = node.get("priceMax", "Desconhecido")
            break

    return {
        "name": product_name,
        "price": price,
        "affiliate_link": short_link
    }

# ==========================
# FUNÇÃO DO BOT
# ==========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # Detecta link da Shopee
    shopee_links = re.findall(r'https?://shopee\.com\.br[^\s]+', text)
    for link in shopee_links:
        info = get_affiliate_info(link)
        if info:
            message = f"🔥 Produto: {info['name']}\n💰 Preço: {info['price']}\n🔗 Link Afiliado: {info['affiliate_link']}"
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("❌ Não foi possível obter informações do produto.")

# ==========================
# EXECUÇÃO DO BOT
# ==========================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("🤖 Bot rodando...")
    app.run_polling()

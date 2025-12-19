import re
import time
import hashlib
import json
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# 🔑 Token do Bot
TELEGRAM_TOKEN = "SEU_TOKEN_AQUI"

# 🔑 Shopee Affiliate
APP_ID = "18353340769"
SECRET = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"
API_URL = "https://open-api.affiliate.shopee.com.br/graphql"

# 🔑 Loja Magalu (Magazine Você)
MAGALU_STORE = "in_603815"


# --- utilitário para escapar texto em HTML (seguro) ---
def html_escape(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


# ---------------- SHOPEE ----------------
def extract_item_id(product_url):
    match = re.search(r'-i\.\d+\.(\d+)', product_url)
    if match:
        return match.group(1)
    match2 = re.search(r'/product/\d+/(\d+)', product_url)
    if match2:
        return match2.group(1)
    return None


def generate_signature(payload, timestamp):
    factor = f"{APP_ID}{timestamp}{payload}{SECRET}"
    return hashlib.sha256(factor.encode()).hexdigest()


def fetch_product(item_id):
    """Varre productOfferV2 até achar o produto com esse itemId"""
    page = 0
    while True:
        query_dict = {
            "query": """
            query Fetch($page:Int){
              productOfferV2(listType:0, page:$page, limit:50) {
                nodes {
                  itemId
                  productName
                  priceMin
                  priceMax
                  offerLink
                  imageUrl
                }
                pageInfo {
                  hasNextPage
                }
              }
            }
            """,
            "variables": {"page": page},
            "operationName": None
        }
        payload = json.dumps(query_dict, separators=(',', ':'))
        timestamp = int(time.time())
        signature = generate_signature(payload, timestamp)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={APP_ID},Timestamp={timestamp},Signature={signature}"
        }

        response = requests.post(API_URL, data=payload, headers=headers)
        data = response.json()

        nodes = data.get("data", {}).get("productOfferV2", {}).get("nodes", [])
        for node in nodes:
            if str(node["itemId"]) == str(item_id):
                return node

        has_next = data.get("data", {}).get("productOfferV2", {}).get("pageInfo", {}).get("hasNextPage", False)
        if not has_next:
            break
        page += 1

    return None


def get_product_info_shopee(product_url):
    item_id = extract_item_id(product_url)
    if not item_id:
        return None, None, None, None

    # 🔹 Buscar dados do produto
    product = fetch_product(item_id)
    if not product:
        return None, None, None, None

    # 🔹 Gerar link afiliado
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
    short_link = data.get("data", {}).get("generateShortLink", {}).get("shortLink", None)

    # Extrai dados do produto
    product_name = product.get("productName", "Desconhecido")
    price_min = product.get("priceMin", "Desconhecido")
    price_max = product.get("priceMax", "Desconhecido")
    image_url = product.get("imageUrl", None)

    price = f"R$ {price_min} - R$ {price_max}" if price_min and price_max else "Preço indisponível"

    return product_name, price, short_link, image_url


# ---------------- MAGALU ----------------
def format_magalu_store(store_id: str) -> str:
    if not store_id.startswith("in_"):
        return store_id[:2] + "_" + store_id[2:]
    return store_id


def get_product_info_magalu(product_url):
    try:
        loja_corrigida = format_magalu_store(MAGALU_STORE)

        if "magazinevoce.com.br" in product_url:
            affiliate_link = product_url
        else:
            path = re.sub(r"https?://www\.magazineluiza\.com\.br", "", product_url)
            affiliate_link = f"https://www.magazinevoce.com.br/magazine{loja_corrigida}{path}"

        response = requests.get(affiliate_link, timeout=10)
        if response.status_code != 200 or "Produto não encontrado" in response.text:
            return "Produto indisponível", "Preço indisponível", affiliate_link, None

        # Nome do produto
        match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE)
        if match:
            productname = match.group(1).replace(" | Magazine Você", "").strip()
        else:
            productname = "Produto Magalu"

        # Imagem principal do produto
        match_img = re.search(r'<meta property="og:image" content="(.*?)"', response.text)
        if match_img:
            image_url = match_img.group(1)
        else:
            image_url = None

        price = "Preço indisponível"

        return productname, price, affiliate_link, image_url

    except Exception as e:
        print("Erro Magalu:", e)
        return "Produto Magalu", "Preço indisponível", product_url, None


# ---------------- HANDLER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Shopee
    if "shopee.com.br" in text:
        productname, price, affiliate_link, image_url = get_product_info_shopee(text)
        if affiliate_link:
            caption = (
                f"📦 <b>{html_escape(productname)}</b>\n"
                f"💰 {html_escape(price)}\n"
                f"🔗 <a href=\"{affiliate_link}\">Clique aqui</a>"
            )
            if image_url:
                await update.message.reply_photo(
                    photo=image_url,
                    caption=caption,
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(caption, parse_mode='HTML')
        else:
            await update.message.reply_text("❌ Não foi possível processar o link da Shopee.")

    # Magalu
    elif "magazineluiza.com.br" in text or "magazinevoce.com.br" in text:
        productname, price, affiliate_link, image_url = get_product_info_magalu(text)
        if affiliate_link:
            caption = (
                f"📦 <b>{html_escape(productname)}</b>\n"
                f"💰 {html_escape(price)}\n"
                f"🔗 <a href=\"{affiliate_link}\">Clique aqui</a>"
            )
            if image_url:
                await update.message.reply_photo(
                    photo=image_url,
                    caption=caption,
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(caption, parse_mode='HTML')
        else:
            await update.message.reply_text("❌ Não foi possível processar o link do Magalu.")


# ---------------- RUN BOT ----------------
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

print("🤖 Bot iniciado...")
app.run_polling()

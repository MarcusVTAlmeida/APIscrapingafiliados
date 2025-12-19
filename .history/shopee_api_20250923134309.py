import re
import time
import hashlib
import json
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# 🔑 Coloque aqui o token do seu bot
TELEGRAM_TOKEN = "7835836746:AAGh264mO96_f7nvkkm2N365fhjk979hydU"

# 🔑 Dados do Shopee Affiliate
APP_ID = "18353340769"
SECRET = "374QPPMAEZPMZRILPQQXKSBEOHCWIHGU"
API_URL = "https://open-api.affiliate.shopee.com.br/graphql"

# 🔑 Sua loja Magalu (Magazine Você)
MAGALU_STORE = "in_603815"

# --- utilitário para escapar texto em HTML (simples e seguro) ---
def html_escape(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))

# Função para extrair itemId do link Shopee
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

# Função para buscar informações do produto Shopee
def get_product_info_shopee(product_url):
    item_id = extract_item_id(product_url)
    if not item_id:
        return None, None, None, None

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
    response = requests.post(API_URL, data=payload_json, headers=headers, timeout=15)
    data = response.json()
    if "errors" in data:
        return None, None, None, None
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
                    imageUrl
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

    return productname, price, short_link, image_url


def format_magalu_store(store_id: str) -> str:
    """Corrige o nome da loja, garantindo que tenha o '_' após 'in'."""
    if not store_id.startswith("in_"):
        return store_id[:2] + "_" + store_id[2:]
    return store_id

def get_product_info_ml(product_url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        resp = requests.get(product_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return "Produto indisponível", "Preço indisponível", product_url, None

        soup = BeautifulSoup(resp.text, "html.parser")

        # JSON principal do Mercado Livre
        script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
        if not script_tag:
            return "Produto ML", "Preço indisponível", product_url, None

        data = json.loads(script_tag.string)

        productname = "Produto ML"
        price = "Preço indisponível"
        image_url = None

        # Normalmente dentro de props.pageProps
        props = data.get("props", {}).get("pageProps", {})

        # Nome
        productname = props.get("initialState", {}).get("product", {}).get("name") \
                      or props.get("item", {}).get("title") \
                      or "Produto ML"

        # Preço
        price_data = props.get("initialState", {}).get("product", {}).get("price") \
                     or props.get("item", {}).get("price")
        if isinstance(price_data, dict):
            amount = price_data.get("amount")
            if amount:
                price = f"R$ {amount}"
        elif price_data:
            price = f"R$ {price_data}"

        # Imagem
        pictures = props.get("initialState", {}).get("product", {}).get("pictures") \
                   or props.get("item", {}).get("pictures")
        if pictures and isinstance(pictures, list):
            image_url = pictures[0].get("url")

        return productname, price, product_url, image_url

    except Exception as e:
        print("Erro ML:", e)
        return "Produto ML", "Preço indisponível", product_url, None



def get_product_info_magalu(product_url):
    try:
        loja_corrigida = format_magalu_store(MAGALU_STORE)

        # Se já é link afiliado
        if "magazinevoce.com.br" in product_url:
            affiliate_link = product_url
        else:
            path = re.sub(r"https?://www\.magazineluiza\.com\.br", "", product_url)
            affiliate_link = f"https://www.magazinevoce.com.br/magazine{loja_corrigida}{path}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Referer": "https://www.google.com/"
        }
        resp = requests.get(affiliate_link, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        name = price = image = None

        # Nome do produto
        tag = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
        if tag:
            name = tag.get("content")

        # Imagem do produto
        tag = soup.find("meta", property="og:image")
        if tag:
            image = tag.get("content")

        # Preço com regex no HTML
        match = re.search(r'"price":\s*"?([\d,\.]+)"?', resp.text)
        if match:
            price = match.group(1).replace(".", "").replace(",", ".")

        return (
            name or "Produto Magalu",
            f"R$ {price}" if price else "Preço indisponível",
            affiliate_link,
            image
        )

    except Exception as e:
        print("Erro Magalu:", e)
        return "Produto Magalu", "Preço indisponível", product_url, None


# Função que responde às mensagens
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Shopee
    if "shopee.com.br" in text:
        productname, price, affiliate_link, image_url = get_product_info_shopee(text)
        if affiliate_link:
            caption = (
                f"📦 <b>{html_escape(productname)}</b>\n"
                f"💰 Preço: {html_escape(price)}\n"
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

# Mercado Livre
    elif "mercadolivre.com.br" in text:
    productname, price, affiliate_link, image_url = get_product_info_ml(text)
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
        await update.message.reply_text("❌ Não foi possível processar o link do Mercado Livre.")



# Configura o bot
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

print("🤖 Bot iniciado...")
app.run_polling()

import re
import requests
from bs4 import BeautifulSoup
import random
import time
from playwright.sync_api import sync_playwright

MAGALU_STORE = "in_603815"

# -------------------
# Legendas prontas
# -------------------
LEGENDAS = [
    "🔥 Aproveite essa oferta incrível!",
    "✨ Promoção imperdível no Magalu!",
    "🛍️ Garanta já o seu com desconto!",
    "💯 Oferta válida por tempo limitado!",
    "🚀 Não perca essa oportunidade!",
    "😍 Olha só esse preço especial!",
    "⚡ Corre antes que acabe!",
]

def gerar_legenda():
    return random.choice(LEGENDAS)

def format_magalu_store(store_id: str) -> str:
    if not store_id.startswith("in_"):
        return store_id[:2] + "_" + store_id[2:]
    return store_id

def encurtar_link(url: str) -> str:
    try:
        api_url = "https://api.encurtador.dev/encurtamentos"
        headers = {"Content-Type": "application/json"}
        data = {"url": url}

        resp = requests.post(api_url, json=data, headers=headers, timeout=10)

        if resp.status_code in [200, 201]:
            result = resp.json()
            if "urlEncurtada" in result:
                return result["urlEncurtada"]

    except Exception as e:
        print(f"⚠️ Erro ao encurtar link: {e}")

    return url


# =========================================================
# PLAYWRIGHT – FALLBACK CONTRA BLOQUEIO / HTML INCOMPLETO
# =========================================================
def get_html_with_playwright(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=60000)
        time.sleep(2)
        html = page.content()
        browser.close()
        return html


# =========================================================
# FUNÇÃO PRINCIPAL
# =========================================================
def get_magalu_product_info(product_url):
    try:
        loja_corrigida = format_magalu_store(MAGALU_STORE)

        if "magazinevoce.com.br" in product_url:
            affiliate_link = product_url
        else:
            path = re.sub(r"https?://www\.magazineluiza\.com\.br", "", product_url)
            affiliate_link = f"https://www.magazinevoce.com.br/magazine{loja_corrigida}{path}"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "pt-BR,pt;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.google.com/",
        }

        resp = requests.get(affiliate_link, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text

        # 🔍 DETECTA HTML SUSPEITO (Render / Datacenter)
        if "R$" not in html or "price" not in html.lower():
            print("⚠️ HTML incompleto via requests → usando Playwright")
            html = get_html_with_playwright(affiliate_link)

        soup = BeautifulSoup(html, "html.parser")

        info = {
            "name": "Produto Magalu",
            "image": None,
            "link": affiliate_link,
            "legend": gerar_legenda(),
            "price_original": None,
            "price_pix": None,
            "pix_discount": None,
            "pix_method": None,
            "card_total": None,
            "card_installments": None,
            "caption": None
        }

        # -------------------
        # NOME E IMAGEM
        # -------------------
        tag_title = soup.find("meta", property="og:title")
        if tag_title:
            name = tag_title.get("content", "").strip()
            name = re.sub(r"\s*-\s*Magazine.*", "", name, flags=re.I)
            name = re.sub(r"\s*-\s*Magalu.*", "", name, flags=re.I)
            info["name"] = name

        tag_image = soup.find("meta", property="og:image")
        if tag_image:
            info["image"] = tag_image.get("content")

        # -------------------
        # PREÇO ORIGINAL
        # -------------------
        price_default = soup.find("div", {"data-testid": "price-default"})
        if price_default:
            orig_tag = (
                price_default.find("p", {"data-testid": "price-original"})
                or price_default.find("span", {"data-testid": "price-original"})
                or price_default.find("s")
            )
            if orig_tag:
                info["price_original"] = orig_tag.get_text(strip=True)

       # -------------------
# PIX (estrutura nova Magalu)
# -------------------
price_default = soup.find("div", {"data-testid": "price-default"})

if price_default:
    # Preço Pix
    pix_price_tag = price_default.find(
        "p", {"data-testid": "price-value"}
    )
    if pix_price_tag:
        info["price_pix"] = pix_price_tag.get_text(" ", strip=True).replace("ou ", "")

    # Método (Pix)
    pix_method_tag = price_default.find(
        "span", {"data-testid": "in-cash"}
    )
    if pix_method_tag:
        info["pix_method"] = pix_method_tag.get_text(strip=True)

    # Desconto Pix
    discount_tag = price_default.find(
        "span", string=re.compile(r"%.*pix", re.I)
    )
    if discount_tag:
        info["pix_discount"] = discount_tag.get_text(strip=True)


        # -------------------
        # CARTÃO
        # -------------------
        card_panel = soup.find("div", {"data-testid": "mod-bestinstallment"})
        if card_panel:
            total_price_tag = card_panel.find(string=re.compile(r"R\$"))
            if total_price_tag:
                info["card_total"] = total_price_tag.strip()

            installment_tag = card_panel.find(string=re.compile(r"\d+x\s*de\s*R\$"))
            if installment_tag:
                info["card_installments"] = installment_tag.strip()

        # -------------------
        # CAPTION FINAL
        # -------------------
        short_link = encurtar_link(info["link"])

        caption = f"📦 {info['name']}\n"

        if info["price_original"] and info["price_pix"]:
            caption += f"💰 De: {info['price_original']} | Por: {info['price_pix']}"
            if info["pix_discount"]:
                caption += f" | {info['pix_discount']}"
        elif info["price_pix"]:
            caption += f"💰 {info['price_pix']}"

        if info["card_total"] and info["card_installments"]:
            caption += f"\n💳 {info['card_total']} ({info['card_installments']}) no cartão"

        caption += f"\n🔗 {short_link}"

        info["caption"] = caption
        info["link"] = short_link

        return info

    except Exception as e:
        print(f"❌ Erro Magalu: {e}")
        return {
            "name": "Produto Magalu",
            "price_text": "Preço indisponível",
            "link": product_url,
            "image": None,
            "legend": "😕 Não foi possível carregar os dados.",
        }

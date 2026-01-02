import re
import random
from playwright.async_api import async_playwright
from urllib.parse import urlparse, urlunparse

MAGALU_STORE = "in_603815"

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

def limpar_url(url: str) -> str:
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))

# 🔥 AGORA É ASYNC
async def get_magalu_product_info(product_url: str) -> dict | None:
    try:
        loja = format_magalu_store(MAGALU_STORE)

        if "magazinevoce.com.br" in product_url:
            affiliate_link = limpar_url(product_url)
        else:
            path = re.sub(r"https?://www\.magazineluiza\.com\.br", "", product_url)
            affiliate_link = f"https://www.magazinevoce.com.br/magazine{loja}{path}"
            affiliate_link = limpar_url(affiliate_link)

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            context = await browser.new_context(
                locale="pt-BR",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                ),
            )

            page = await context.new_page()
            await page.goto(affiliate_link, wait_until="networkidle", timeout=60000)

            # 🚨 DETECTA BLOQUEIO
            if "az-request-verify" in page.url:
                raise Exception("Bloqueio anti-bot da Magalu")

            html = await page.content()
            await browser.close()

        # -------------------
        # EXTRAÇÃO
        # -------------------
        def find(pattern):
            m = re.search(pattern, html, re.I | re.S)
            return m.group(1).strip() if m else None

        info = {
            "name": None,
            "image": None,
            "link": affiliate_link,
            "legend": gerar_legenda(),
            "price_original": None,
            "price_pix": None,
            "pix_discount": None,
            "pix_method": "no Pix",
            "card_total": None,
            "card_installments": None,
            "caption": None,
        }

        info["name"] = find(r'property="og:title"\s+content="([^"]+)"')
        if info["name"]:
            info["name"] = re.sub(r"\s*-\s*(Magazine|Magalu).*", "", info["name"], flags=re.I)

        info["image"] = find(r'property="og:image"\s+content="([^"]+)"')

        info["price_original"] = find(r'data-testid="price-original".*?>\s*(R\$[^<]+)')
        info["price_pix"] = find(r'data-testid="price-value".*?>.*?(R\$[^<]+)')
        info["pix_discount"] = find(r'(\d+% de desconto no pix)')
        info["card_installments"] = find(r'(\d+x de R\$[^<]+)')

        # -------------------
        # CAPTION
        # -------------------
        caption = f"📦 {info['name']}\n"

        if info["price_original"] and info["price_pix"]:
            caption += f"💰 De: {info['price_original']} | Por: {info['price_pix']}"
            if info["pix_discount"]:
                caption += f" | {info['pix_discount']}"
        elif info["price_pix"]:
            caption += f"💰 {info['price_pix']}"

        if info["card_installments"]:
            caption += f"\n💳 {info['card_installments']} no cartão"

        caption += f"\n🔗 {affiliate_link}"

        info["caption"] = caption.strip()
        return info

    except Exception as e:
        print("❌ Magalu Playwright:", e)
        return None

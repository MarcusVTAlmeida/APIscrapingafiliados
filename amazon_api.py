import asyncio
import random
from playwright.async_api import async_playwright

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

async def _scrape_amazon(product_url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            locale="pt-BR",
            viewport={"width": 1366, "height": 768}
        )

        page = await context.new_page()

        try:
            await page.goto(product_url, timeout=90000, wait_until="domcontentloaded")
            await page.wait_for_timeout(random.randint(3500, 5500))

            # Se cair em CAPTCHA
            if "captcha" in page.url.lower():
                await browser.close()
                return {
                    "title": None,
                    "price": None,
                    "original_value": None,
                    "caption": "🚫 Produto indisponível (bloqueado pela Amazon)",
                    "image": None,
                    "url": product_url,
                }

            # ============ TÍTULO ============
            title = None
            title_el = page.locator("span#productTitle")
            if await title_el.count() > 0:
                title_text = await title_el.first.text_content()
                title = title_text.strip() if title_text else None
            if not title:
                title = "Título não encontrado"

            # ============ IMAGEM ============
            image = None
            img = page.locator("img#landingImage")
            if await img.count() > 0:
                image = await img.get_attribute("src")
                # Pega também data-old-hires (melhor qualidade)
                if not image or "data:image" in image:
                    hires = await img.get_attribute("data-old-hires")
                    if hires:
                        image = hires

            # ============ PREÇO ATUAL (COM DESCONTO) ============
            price = None
            selectors_price = [
                "span.priceToPay span.a-offscreen",  # Preço principal
                "span.a-price[data-a-color='base'] span.a-offscreen",  # Fallback
                "span.a-price span.a-offscreen",  # Fallback genérico
            ]
            for sel in selectors_price:
                el = page.locator(sel).first
                if await el.count() > 0:
                    txt = await el.text_content()
                    if txt and txt.strip():
                        price = txt.strip()
                        break

            # ============ PREÇO ORIGINAL (RISCADO) ============
            old_price = None
            # Seletor específico: <span class="a-price a-text-price" data-a-strike="true">
            old_selector = 'span.a-price.a-text-price[data-a-strike="true"] span.a-offscreen'
            old_el = page.locator(old_selector).first
            if await old_el.count() > 0:
                txt_old = await old_el.text_content()
                if txt_old and txt_old.strip():
                    old_price = txt_old.strip()

            # ============ DESCONTO (%) ============
            discount = None
            disc_selectors = [
                "span.savingsPercentage",
                "span.savingPriceOverride",
            ]
            for sel in disc_selectors:
                disc_el = page.locator(sel).first
                if await disc_el.count() > 0:
                    txt_disc = await disc_el.text_content()
                    if txt_disc and txt_disc.strip():
                        discount = txt_disc.strip()
                        break

            # ============ MONTA CAPTION ============
            caption = f"📦 {title}\n"
            if old_price and price:
                caption += f"💰 De {old_price} por {price}"
            elif price:
                caption += f"💰 {price}"
            else:
                caption += "💰 Preço não disponível"

            if discount:
                caption += f" ({discount})"
            caption += f"\n🔗 {product_url}"

            await browser.close()

            return {
                "title": title,
                "price": price,
                "original_value": old_price,
                "caption": caption,
                "image": image,
                "url": product_url,
            }

        except Exception as e:
            await browser.close()
            return {
                "title": None,
                "price": None,
                "original_value": None,
                "caption": f"⚠️ Erro ao obter produto Amazon: {str(e)}",
                "image": None,
                "url": product_url,
            }

async def get_amazon_product_info(product_url: str):
    return await _scrape_amazon(product_url)

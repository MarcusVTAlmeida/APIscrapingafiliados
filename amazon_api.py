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
                    "caption": "🚫 Produto indisponível (bloqueado pela Amazon)",
                    "image": None,
                    "url": product_url
                }

            # Título           
            title = title.strip() if title else "Título não encontrado"
            title_el = page.locator("span#productTitle").first
            title = await title_el.text_content()


            # Imagem principal
            image = None
            img = page.locator("#landingImage")
            if await img.count() > 0:
                image = await img.get_attribute("src")

            # Preço
            price = None
            selectors_price = [
                "span.a-price span.a-offscreen",
                "span.priceToPay span.a-offscreen",
            ]
            for sel in selectors_price:
                el = page.locator(sel)
                if await el.count() > 0:
                    price = await el.first.text_content()
                    break

            # Preço antigo
            old_price = None
            old = page.locator("span.a-text-price span.a-offscreen")
            if await old.count() > 0:
                old_price = await old.first.text_content()

            # Desconto
            discount = None
            disc = page.locator("span.savingsPercentage")
            if await disc.count() > 0:
                discount = await disc.first.text_content()

            caption = f"📦 {title}\n"
            caption += f"💰 De: {old_price or 'N/A'} | Por: {price or 'N/A'}"
            if discount:
                caption += f" | {discount}"
            caption += f"\n🔗 {product_url}"

            await browser.close()

            return {
                "caption": caption,
                "image": image,
                "url": product_url
            }

        except Exception as e:
            await browser.close()
            return {
                "caption": f"⚠️ Erro ao obter produto Amazon\n{e}",
                "image": None,
                "url": product_url
            }


async def get_amazon_product_info(product_url: str):
    return await _scrape_amazon(product_url)


# Teste local
if __name__ == "__main__":
    url = "https://www.amazon.com.br/dp/B09HHMQ1SG"
    data = get_amazon_product_info(url)
    print(data["caption"])
    print("Imagem:", data["image"])

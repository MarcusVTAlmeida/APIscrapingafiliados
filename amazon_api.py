import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

def get_amazon_product_info(product_url: str):
    try:
        # Fazendo a requisição para a página do produto
        resp = requests.get(product_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()  # Garante que a requisição foi bem-sucedida
        soup = BeautifulSoup(resp.text, "lxml")

        # Título
        title_el = soup.select_one("#productTitle")
        title = title_el.get_text(strip=True) if title_el else "Título não encontrado"

        # Imagem (preferindo data-old-hires se existir)
        img_tag = soup.select_one("img#landingImage")
        image = img_tag.get("data-old-hires") if img_tag else None
        if not image:
            image = img_tag.get("src") if img_tag else None

        # Preço atual (com desconto)
        price = None
        price_selectors = [
            "span.priceToPay span.a-offscreen",
            "#corePrice_feature_div span.a-price span.a-offscreen",
            "span.a-price.aok-align-center span.a-offscreen",
            "span.a-price span.a-offscreen",
        ]
        for sel in price_selectors:
            price_el = soup.select_one(sel)
            if price_el:
                price = price_el.get_text(strip=True)
                break

        # Preço original (riscado)
        old_price = None
        old_el = soup.select_one('span.a-price.a-text-price[data-a-strike="true"] span.a-offscreen')
        if old_el:
            old_price = old_el.get_text(strip=True)

        # Desconto percentual
        discount = None
        disc_el = soup.select_one("span.savingsPercentage") or soup.select_one("span.savingPriceOverride")
        if disc_el:
            discount = disc_el.get_text(strip=True)

        # Monta a mensagem de retorno
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

        # Retornando os dados extraídos
        return {
            "title": title,
            "price": price,
            "original_value": old_price,
            "caption": caption,
            "image": image,
            "url": product_url,
        }

    except Exception as e:
        return {
            "title": None,
            "price": None,
            "original_value": None,
            "caption": f"⚠️ Erro ao obter produto Amazon: {e}",
            "image": None,
            "url": product_url,
        }

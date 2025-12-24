import httpx
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

async def get_amazon_product_info(product_url: str):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(product_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Título (usando #title)
        title_tag = soup.find("h1", {"id": "title"})
        title = title_tag.text.strip() if title_tag else "Título não encontrado"

        # Imagens (usando regex, mais robusto)
        images = re.findall('"hiRes":"(.+?)"', resp.text)
        image = images[0] if images else None

        # Preço (com desconto, usando .a-price)
        price_tag = soup.find("span", {"class": "a-price"})
        price = price_tag.find("span", class_="a-offscreen").text.strip() if price_tag and price_tag.find("span", class_="a-offscreen") else None

        # Preço antigo (se disponível)
        old_price = None
        old_price_tag = soup.find("span", {"class": "a-text-price"})
        if old_price_tag:
            old_price = old_price_tag.text.strip()

        # Monta a mensagem de retorno
        caption = f"📦 {title}\n"
        if old_price and price:
            caption += f"💰 De {old_price} por {price}"
        elif price:
            caption += f"💰 {price}"
        else:
            caption += "💰 Preço não disponível"

        # Retorna os dados no formato esperado
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

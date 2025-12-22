from fastapi import FastAPI
from pydantic import BaseModel
import asyncio

from product_info_router import get_product_info

app = FastAPI(title="Scraper Bot API")


def normalize_image(img: str | None):
    if not img:
        return None

    if img.startswith("//"):
        return "https:" + img

    return img


def normalize_product(result, url: str):
    """
    Normaliza qualquer retorno (dict | tuple) para o padrão da API
    """
    if isinstance(result, dict):
            return {
"title": result.get("title"),
"price": result.get("price"),
"original_value": result.get("original_value"),
"caption": result.get("caption"),
"image": normalize_image(result.get("image")),
"url": result.get("url", url),
}

    if isinstance(result, tuple):
        # Suporta 2 padrões comuns de tupla:
        # 1) (caption, title, price, image)  -> padrão antigo
        # 2) (title, price, url, image)      -> padrão ML atual
        if len(result) == 4:
            a, b, c, d = result

            # Se o 3º item parece ser um link, então é (title, price, url, image)
            if isinstance(c, str) and (c.startswith("http://") or c.startswith("https://")):
                title = a
                price = b
                url_from_tuple = c
                image = d

                caption = f"🔥 OFERTA IMPERDÍVEL 🔥\n\n{title}\n\n💰 {price}\n\n👉 Compre agora:\n{url_from_tuple}"

                return {
                    "title": title,
                    "price": price,
                    "caption": caption,
                    "image": normalize_image(image),
                    "url": url_from_tuple,
                }

            # Caso normal: (caption, title, price, image)
            caption, title, price, image = result
            return {
                "title": title,
                "price": price,
                "caption": caption,
                "image": normalize_image(image),
                "url": url,
            }

        # fallback caso venha tupla em formato inesperado
        return {
            "title": None,
            "price": None,
            "caption": "❌ Retorno inesperado do scraper.",
            "image": None,
            "url": url,
        }

    return {
        "title": None,
        "price": None,
        "caption": "❌ Não foi possível obter o produto.",
        "image": None,
        "url": url,
    }


# 📥 Modelo de entrada
class ScrapeRequest(BaseModel):
    url: str


@app.post("/scrape")
async def scrape_product(data: ScrapeRequest):
    url = data.url.strip()

    try:
        result = get_product_info(url)

        # 🟢 Caso async (Amazon / Playwright)
        if asyncio.iscoroutine(result):
            result = await result

        return normalize_product(result, url)

    except Exception as e:
        return {
            "title": None,
            "price": None,
            "caption": f"⚠️ Erro interno: {str(e)}",
            "image": None,
            "url": url,
        }

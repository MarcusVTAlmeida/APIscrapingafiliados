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
            "original_value": result.get("original_value"),  # ✅ AQUI
            "caption": result.get("caption"),
            "image": normalize_image(result.get("image")),
            "url": result.get("url", url),
        }


    if isinstance(result, tuple):
        caption, title, price, image = result
        return {
            "title": title,
            "price": price,
            "caption": caption,
            "image": normalize_image(image),
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

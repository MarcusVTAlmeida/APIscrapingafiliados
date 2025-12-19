from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio

from product_info_router import get_product_info

app = FastAPI(title="Scraper Bot API")

def normalize_product(result, url: str):
    """
    Normaliza qualquer retorno (dict | tuple) para o padrão da API
    """
    if isinstance(result, dict):
        return {
            "title": None,
            "price": None,
            "caption": result.get("caption"),
            "image": result.get("image"),
            "url": result.get("url", url),
        }

    if isinstance(result, tuple):
        caption, title, price, image = result
        return {
            "title": title,
            "price": price,
            "caption": caption,
            "image": image,
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


# 📤 Modelo de saída
class ScrapeResponse(BaseModel):
    caption: str | None = None
    image: str | None = None


@app.post("/scrape")
async def scrape_product(data: ScrapeRequest):
    url = data.url.strip()

    try:
        result = get_product_info(url)

        # 🟢 Caso async (Amazon)
        if asyncio.iscoroutine(result):
            result = await result

        normalized = normalize_product(result, url)
        return normalized

    except Exception as e:
        return {
            "title": None,
            "price": None,
            "caption": f"⚠️ Erro interno: {str(e)}",
            "image": None,
            "url": url,
        }

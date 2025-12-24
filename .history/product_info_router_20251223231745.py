# product_info_router.py

from shopee_api import get_shopee_product_info
from magalu_api import get_magalu_product_info
from ml_api import get_ml_product_info
from amazon_api import get_amazon_product_info

async def get_product_info(product_url):
    url = product_url.lower()

    if "shopee" in url:
        return get_shopee_product_info(product_url)

    elif "magazineluiza" in url or "magalu" in url:
        return get_magalu_product_info(product_url)

    elif "mercadolivre" in url or "mercado-livre" in url:
        return get_ml_product_info(product_url)

    elif "amazon" in url:
        # aqui chamamos async
        return await get_amazon_product_info(product_url)

    else:
        return None

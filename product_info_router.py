from magalu_api import get_magalu_product_info
from shopee_api import get_shopee_product_info
from ml_api import get_ml_product_info
from amazon_api import get_amazon_product_info

def get_product_info(url: str):
    url = url.lower()

    if "magazineluiza" in url or "magazinevoce" in url:
        return get_magalu_product_info(url)

    if "shopee" in url:
        return get_shopee_product_info(url)

    if "mercado" in url:
        return get_ml_product_info(url)

    if "amazon" in url:
        return get_amazon_product_info(url)

    return None
